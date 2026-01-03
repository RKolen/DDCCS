"""
Story AI Generator Module

Generates story narratives using AI based on user prompts and character context.
Integrates party member personalities and background information into generated
stories. Includes RAG (Retrieval-Augmented Generation) integration for accurate
D&D spell/ability descriptions via dnd5e.wikidot.com.
"""

from typing import Optional, Dict, Any
from src.ai.availability import AI_AVAILABLE
from src.utils.spell_lookup_helper import lookup_spells_and_abilities


def _build_story_context(
    party_characters: Optional[Dict[str, Any]] = None,
    campaign_context: Optional[str] = None,
    known_npcs: Optional[list] = None,
) -> str:
    """Build combined character, NPC, and campaign context string."""
    context_parts = []

    # Add character context from party
    if party_characters:
        char_descriptions = _format_character_descriptions(party_characters)
        if char_descriptions:
            context_parts.append("\nParty Members:\n" + char_descriptions)

    # Add NPC context from known NPCs relevant to the location
    if known_npcs:
        npc_descriptions = _format_npc_descriptions(known_npcs)
        if npc_descriptions:
            context_parts.append("\nKnown NPCs at this location:\n" + npc_descriptions)

    # Add campaign context
    if campaign_context:
        context_parts.append(f"\nCampaign Setting: {campaign_context}")

    return "".join(context_parts)


def _format_character_descriptions(
    party_characters: Dict[str, Any],
) -> str:
    """Format character descriptions for context."""
    descriptions = []
    for name, profile in party_characters.items():
        if isinstance(profile, dict):
            char_class = profile.get("dnd_class", "Unknown")
            personality = profile.get("personality_summary", "")
            descriptions.append(f"- {name} ({char_class}): {personality}")
    return "\n".join(descriptions)


def _format_npc_descriptions(known_npcs: list) -> str:
    """Format NPC descriptions for context."""
    npc_descriptions = []
    for npc in known_npcs:
        name = npc.get("name", "Unknown")
        role = npc.get("role", "NPC")
        personality = npc.get("personality", "")
        location = npc.get("location", "")
        npc_descriptions.append(f"- {name} ({role} at {location}): {personality}")
    return "\n".join(npc_descriptions)


def _extract_spell_names(story_prompt: str) -> str:
    """Extract D&D spell and ability names from story prompt.

    Identifies spells/abilities mentioned and creates instructions
    to use exact spell names in the narrative.

    Args:
        story_prompt: User's story prompt

    Returns:
        Instruction string with spell names to use, or empty string
    """
    # Common D&D spells and abilities
    spell_patterns = [
        "detect magic",
        "fireball",
        "heal",
        "cure wounds",
        "scorching ray",
        "magic missile",
        "shield",
        "armor of agathys",
        "misty step",
        "dimension door",
        "invisibility",
        "stoneskin",
        "cone of cold",
        "lightning bolt",
        "polymorph",
        "counterspell",
        "dispel magic",
        "identify",
        "disguise self",
        "mage hand",
        "minor illusion",
        "prestidigitation",
        "light",
        "guidance",
        "mending",
        "resistance",
    ]

    prompt_lower = story_prompt.lower()
    found_spells = [spell for spell in spell_patterns if spell in prompt_lower]

    if found_spells:
        spell_list = ", ".join(found_spells)
        return (
            f"\nIMPORTANT SPELLS/ABILITIES MENTIONED: {spell_list}. "
            f"Use these EXACT spell names in your narrative, do not paraphrase them."
        )
    return ""


def generate_story_from_prompt(
    ai_client,
    story_prompt: str,
    story_config: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Generate a story narrative using AI based on a user prompt.

    This function takes a user's story concept and uses an AI model to generate
    a rich narrative that incorporates party member personalities, NPC context,
    and campaign information. The generated story respects D&D 5e conventions
    and character traits.

    Automatically performs RAG lookup for D&D spells and abilities mentioned in
    the prompt, enriching the narrative with accurate mechanical descriptions
    from dnd5e.wikidot.com.

    Args:
        ai_client: Initialized AIClient instance for making AI requests.
        story_prompt: User's story concept or prompt (e.g., "The party arrives
            at a mysterious tavern in the woods").
        story_config: Optional dict with generation settings:
            - 'party_characters': Dict of party members with profiles
            - 'known_npcs': List of NPC dicts relevant to location
            - 'campaign_context': Campaign setting information
            - 'max_tokens': Maximum tokens for response (default 2000)
            - 'is_exploration': If True, avoids combat, focuses on exploration
              and social dynamics (default False)

    Returns:
        Generated story narrative as a string, or None if AI is unavailable
        or generation fails.

    Raises:
        ValueError: If story_prompt is empty or None.
        AttributeError: If ai_client is not a valid AIClient instance.
    """
    if not story_prompt or not story_prompt.strip():
        raise ValueError("Story prompt cannot be empty")

    if ai_client is None or not AI_AVAILABLE:
        return None

    # Normalize configuration
    if story_config is None:
        story_config = {}

    # Build combined context (including NPC context)
    context = _build_story_context(
        story_config.get("party_characters"),
        story_config.get("campaign_context"),
        story_config.get("known_npcs"),
    )

    # Look up D&D spells/abilities for accurate descriptions
    ability_context = lookup_spells_and_abilities(story_prompt)

    # Extract spell names from prompt for explicit inclusion
    spell_instructions = _extract_spell_names(story_prompt)

    # Build system and user prompts
    system_prompt = _build_story_system_prompt(
        story_config.get("is_exploration", False)
    )

    user_prompt = (
        f"Write a D&D story scene based on this prompt:\n{story_prompt}"
        f"{context}"
        f"{ability_context}"
        f"{spell_instructions}\n\n"
        "Generate an engaging narrative that incorporates the party members "
        "and respects their personalities and backgrounds. Format as pure "
        "narrative prose suitable for a story file."
    )

    try:
        # Make AI request
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=story_config.get("max_tokens", 2000),
            temperature=0.8,
        )

        # Extract generated text
        generated_text = response.choices[0].message.content.strip()
        return generated_text

    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Failed to generate story: {e}")
        return None


def _build_story_system_prompt(is_exploration: bool = False) -> str:
    """
    Build system prompt for D&D story generation.

    Args:
        is_exploration: If True, avoid combat and focus on exploration/roleplay

    Returns:
        Formatted system prompt string
    """
    base_prompt = (
        "You are an experienced D&D Dungeon Master crafting engaging narrative. "
        "Write story descriptions in third person. Focus on atmosphere, character "
        "reactions, and plot development. Keep descriptions vivid but concise "
        "(max 80 chars per line). Respect D&D 5e conventions and the party's "
        "character personalities. Do not include dice rolls, mechanics, or "
        "meta-game information in the narrative.\n\n"
        "IMPORTANT: When spells or abilities are mentioned, USE THE EXACT SPELL "
        "NAMES in the narrative. For example, if 'detect magic' is mentioned, "
        "write 'Gandalf cast detect magic' not 'Gandalf cast a detection spell'."
    )

    if is_exploration:
        base_prompt += (
            " Do NOT include combat, fighting, or hostile action. Focus on "
            "character interactions, exploration, discovery, and social dynamics."
        )

    return base_prompt


def generate_story_description(
    ai_client,
    story_title: str,
    party_characters: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Generate a brief description for a story based on title and party.

    Used to create compelling story descriptions when a user hasn't provided
    one. Incorporates party character information for context.

    Args:
        ai_client: Initialized AIClient instance.
        story_title: Title of the story.
        party_characters: Optional dictionary of party members with profiles.

    Returns:
        Generated description string, or None if generation fails.
    """
    if not story_title or not story_title.strip():
        raise ValueError("Story title cannot be empty")

    if ai_client is None or not AI_AVAILABLE:
        return None

    # Build character context
    character_names = (
        ", ".join(party_characters.keys()) if party_characters else "the party"
    )

    system_prompt = (
        "You are a creative D&D story designer. Write concise, compelling "
        "story descriptions (1-2 sentences) that capture the essence of "
        "a story hook."
    )

    user_prompt = (
        f"Write a compelling 1-2 sentence description for a D&D story with "
        f"this title: '{story_title}' involving {character_names}. "
        f"Focus on intrigue and adventure potential."
    )

    try:
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )

        description = response.choices[0].message.content.strip()
        return description

    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Failed to generate description: {e}")
        return None


def enhance_story_narrative(
    ai_client,
    narrative_text: str,
    enhancement_type: str = "expand",
    max_tokens: int = 1500,
) -> Optional[str]:
    """
    Enhance an existing story narrative using AI.

    Takes a narrative and applies enhancements such as expanding descriptions,
    adding dialogue, or improving flow while maintaining the original story
    structure and intent.

    Args:
        ai_client: Initialized AIClient instance.
        narrative_text: The story narrative to enhance.
        enhancement_type: Type of enhancement: "expand", "dialogue", "atmosphere"
        max_tokens: Maximum tokens for the response.

    Returns:
        Enhanced narrative string, or None if generation fails.

    Raises:
        ValueError: If narrative_text is empty or enhancement_type is invalid.
    """
    valid_types = ["expand", "dialogue", "atmosphere"]
    if enhancement_type not in valid_types:
        raise ValueError(f"enhancement_type must be one of {valid_types}")

    if not narrative_text or not narrative_text.strip():
        raise ValueError("Narrative text cannot be empty")

    if ai_client is None or not AI_AVAILABLE:
        return None

    enhancement_instructions = {
        "expand": (
            "Expand this narrative with more descriptive details, sensory "
            "information, and atmospheric elements. Keep the same plot but "
            "enrich the description."
        ),
        "dialogue": (
            "Add natural dialogue exchanges between characters to bring the "
            "narrative to life. Maintain the original plot and actions."
        ),
        "atmosphere": (
            "Enhance the atmospheric and emotional tone of this narrative. "
            "Add more vivid descriptions of the setting and mood."
        ),
    }

    system_prompt = (
        "You are an experienced D&D storyteller refining narrative prose. "
        "Enhance the story while preserving its core elements, plot flow, "
        "and character actions. Keep lines to max 80 characters. Write in "
        "third person narrative style suitable for a D&D story file."
    )

    user_prompt = (
        f"{enhancement_instructions[enhancement_type]}\n\n"
        f"Original narrative:\n{narrative_text}"
    )

    try:
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )

        enhanced_text = response.choices[0].message.content.strip()
        return enhanced_text

    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Failed to enhance narrative: {e}")
        return None


def generate_session_results_from_story(
    ai_client,
    story_content: str,
    party_names: list,
) -> Optional[Dict[str, Any]]:
    """
    Generate session results from AI-created story narrative.

    Analyzes story content to extract character actions, suggested rolls,
    and key narrative events. Returns structured data for population into
    session_results_*.md file.

    Args:
        ai_client: Initialized AIClient instance for AI requests
        story_content: The narrative story that was generated
        party_names: List of party member names participating in session

    Returns:
        Dict with keys:
        - 'character_actions': List of strings (character: action/outcome)
        - 'narrative_events': List of key events from the narrative
        - 'suggested_rolls': List of dicts with roll suggestions
        - 'npc_interactions': List of NPCs encountered

        Returns None if AI is unavailable or generation fails.
    """
    if not story_content or not story_content.strip():
        return None

    if ai_client is None or not AI_AVAILABLE:
        return None

    party_list_str = ", ".join(party_names)

    system_prompt = (
        "You are a D&D session analyzer. Extract session results from "
        "story narratives. Format your response as structured data with "
        "character actions, suggested rolls, narrative events, and NPCs. "
        "Be concise and specific."
    )

    user_prompt = (
        f"Analyze this D&D story and extract session results:\n\n"
        f"{story_content}\n\n"
        f"Party members: {party_list_str}\n\n"
        f"Provide structured analysis:\n"
        f"1. Each character's main actions and outcomes\n"
        f"2. Suggested rolls (skill checks, saves, attacks) with DCs\n"
        f"3. Key narrative events that occurred\n"
        f"4. NPCs encountered and their significance\n"
        f"Format as SECTION headers followed by bullet points."
    )

    try:
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1500,
            temperature=0.6,
        )

        analysis = response.choices[0].message.content.strip()

        # Parse the AI response into structured data
        return _parse_session_analysis(analysis, party_names)

    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Failed to generate session results: {e}")
        return None


def _parse_session_analysis(analysis: str, party_names: list) -> Dict[str, Any]:
    """
    Parse AI-generated session analysis into structured format.

    Args:
        analysis: Raw text from AI analysis
        party_names: List of party member names (used for context in parsing)

    Returns:
        Dict with organized session results
    """
    # party_names used for potential context in future enhancements
    _ = party_names

    results = {
        "character_actions": [],
        "narrative_events": [],
        "suggested_rolls": [],
        "npc_interactions": [],
    }

    lines = analysis.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section headers
        if "character" in line.lower() and "action" in line.lower():
            current_section = "character_actions"
        elif "roll" in line.lower():
            current_section = "suggested_rolls"
        elif "event" in line.lower() or "narrative" in line.lower():
            current_section = "narrative_events"
        elif "npc" in line.lower() or "encounter" in line.lower():
            current_section = "npc_interactions"
        elif line.startswith("-") or line.startswith("*"):
            # Process bullet points
            bullet_text = line.lstrip("-* ").strip()
            if bullet_text and current_section:
                results[current_section].append(bullet_text)

    return results


def generate_story_hooks_from_content(
    ai_client,
    story_content: str,
    party_characters: Optional[Dict[str, Any]] = None,
    party_names: Optional[list] = None,
) -> Optional[Dict[str, Any]]:
    """
    Generate AI-powered story hooks from story content with character context.

    Analyzes story narrative using AI to extract unresolved plot threads,
    character-specific hooks based on backgrounds and motivations, next session
    ideas, and NPC follow-ups. Incorporates party character personalities and
    motivations for personalized hook generation.

    Args:
        ai_client: Initialized AIClient instance for AI requests
        story_content: The narrative story that was generated
        party_characters: Dict of character name -> profile with motivations,
                         fears, goals, background_story
        party_names: List of party member names (used for context)

    Returns:
        Dict with keys:
        - 'unresolved_threads': List of main plot threads
        - 'character_specific_hooks': Dict mapping char names to hook lists
        - 'next_session_ideas': List of future session suggestions
        - 'npc_follow_ups': List of NPC-related follow-up opportunities

        Returns None if AI is unavailable or generation fails.

    Raises:
        ValueError: If story_content is empty or party_characters is invalid
    """
    if not story_content or not story_content.strip():
        return None

    if ai_client is None or not AI_AVAILABLE:
        return None

    if not party_names and not party_characters:
        party_names = []
    elif party_names is None:
        party_names = list(party_characters.keys()) if party_characters else []

    # Build character context from profiles
    character_context = _build_character_context_for_hooks(party_characters)

    system_prompt = (
        "You are a D&D campaign planner. Generate story hooks from D&D sessions. "
        "CRITICAL: Include ALL party members in CHARACTER HOOKS section. "
        "CRITICAL: Use ONLY these section headers: UNRESOLVED THREADS, "
        "CHARACTER HOOKS, NEXT SESSIONS, NPC FOLLOW-UPS. "
        "CRITICAL: Under CHARACTER HOOKS use ONLY format: #### [Name]. "
        "Include all party members without exception. "
        "Respond only in English."
    )

    # Build explicit party member list with numbers
    party_list_numbered = (
        "\n".join([f"{i+1}. {name}" for i, name in enumerate(party_names)])
        if party_names
        else ""
    )

    user_prompt = (
        f"Analyze this D&D story and generate story hooks:\n\n"
        f"{story_content}\n\n"
        f"Party Members:\n{character_context}\n\n"
        f"REQUIRED OUTPUT FORMAT:\n\n"
        f"UNRESOLVED THREADS\n"
        f"- [thread 1]\n"
        f"- [thread 2]\n\n"
        f"CHARACTER HOOKS\n"
        f"#### Aragorn\n"
        f"- [hook 1]\n"
        f"- [hook 2]\n"
        f"#### Frodo Baggins\n"
        f"- [hook 1]\n"
        f"- [hook 2]\n"
        f"#### Gandalf the Grey\n"
        f"- [hook 1]\n"
        f"- [hook 2]\n\n"
        f"NEXT SESSIONS\n"
        f"- [idea 1]\n"
        f"- [idea 2]\n\n"
        f"NPC FOLLOW-UPS\n"
        f"- [follow-up 1]\n"
        f"- [follow-up 2]\n\n"
        f"YOUR TASK:\n"
        f"1. Generate 3-5 unresolved plot threads\n"
        f"2. Generate hooks for ALL these party members (MUST INCLUDE ALL {len(party_names)}):\n"
        f"{party_list_numbered}\n"
        f"3. Generate 2-3 next session ideas\n"
        f"4. Generate NPC follow-ups\n\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"- Include EVERY party member listed above\n"
        f"- Use ONLY the format shown above\n"
        f"- Do NOT include code, examples, or explanations\n"
        f"- Only English, no other languages"
    )

    try:
        response = ai_client.client.chat.completions.create(
            model=ai_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        analysis = response.choices[0].message.content.strip()

        # Parse the AI response into structured hooks data
        parsed_hooks = _parse_hooks_analysis(analysis, party_names)

        return parsed_hooks

    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Failed to generate story hooks: {e}")
        print(f"[ERROR] AI client type: {type(ai_client)}")
        print(f"[ERROR] AI_AVAILABLE: {AI_AVAILABLE}")
        return None


def _build_character_context_for_hooks(
    party_characters: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build character context string for hooks generation AI prompt.

    Extracts motivations, goals, fears, and backgrounds from character profiles
    to provide rich context for personalized hook generation.

    Args:
        party_characters: Dict of character name -> profile

    Returns:
        Formatted character context string
    """
    if not party_characters:
        return "No character profiles available"

    descriptions = []
    for name, profile in party_characters.items():
        if not isinstance(profile, dict):
            continue

        dnd_class = profile.get("dnd_class", "Unknown")
        desc_parts = [f"- {name} ({dnd_class})"]

        # Add personality
        if profile.get("personality_summary"):
            desc_parts.append(f"  Personality: {profile['personality_summary']}")

        # Add motivations
        motivations = profile.get("motivations", [])
        if motivations:
            desc_parts.append(f"  Motivations: {', '.join(motivations[:2])}")

        # Add goals and fears
        goals = profile.get("goals", [])
        if goals:
            desc_parts.append(f"  Goals: {', '.join(goals[:2])}")

        fears = profile.get("fears_weaknesses", [])
        if fears:
            desc_parts.append(f"  Fears: {', '.join(fears[:2])}")

        descriptions.append("\n".join(desc_parts))

    return "\n\n".join(descriptions) if descriptions else "No character data"


def _parse_hooks_analysis(
    analysis: str, party_names: Optional[list] = None
) -> Dict[str, Any]:
    """
    Parse AI-generated hooks analysis into structured format.

    Extracts sections from AI response and organizes them into hooks,
    character-specific hooks, session ideas, and NPC follow-ups.

    Args:
        analysis: Raw text from AI analysis
        party_names: List of party member names (for context in parsing)

    Returns:
        Dict with organized hooks data
    """
    results = {
        "unresolved_threads": [],
        "character_specific_hooks": {},
        "next_session_ideas": [],
        "npc_follow_ups": [],
    }

    if party_names is None:
        party_names = []

    lines = analysis.split("\n")
    current_section = None
    current_character = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Update section or character based on line content
        section, char = _detect_hooks_section_and_character(line_stripped, party_names)
        if section:
            current_section = section
            current_character = char
            continue

        # Process bullet points
        if line_stripped.startswith("-") or line_stripped.startswith("*"):
            bullet_text = line_stripped.lstrip("-* ").strip()
            if not bullet_text:
                continue

            _add_hook_to_results(
                results,
                current_section,
                bullet_text,
                current_character,
                party_names,
            )

    return results


def _detect_hooks_section_and_character(
    line: str, party_names: Optional[list] = None
) -> tuple:
    """
    Detect if line contains section header or character name.

    Args:
        line: Stripped line from analysis text
        party_names: List of party member names

    Returns:
        Tuple of (section_name, character_name) or (None, None)
    """
    if party_names is None:
        party_names = []

    line_upper = line.upper()

    # Check for section headers
    if "UNRESOLVED" in line_upper and "THREAD" in line_upper:
        return ("unresolved_threads", None)
    if "CHARACTER" in line_upper and "HOOK" in line_upper:
        return ("character_hooks", None)
    if "NEXT" in line_upper and "SESSION" in line_upper:
        return ("next_session_ideas", None)
    if "NPC" in line_upper and ("FOLLOW" in line_upper or "RELATION" in line_upper):
        return ("npc_follow_ups", None)

    # Check for character name headers
    for char_name in party_names:
        if char_name.lower() in line.lower():
            return ("character_hooks", char_name)

    return (None, None)


def _add_hook_to_results(
    results: Dict[str, Any],
    section: Optional[str],
    hook_text: str,
    character: Optional[str],
    party_names: Optional[list] = None,
) -> None:
    """
    Add a hook entry to the results dictionary.

    Args:
        results: Results dict to update
        section: Current section name
        hook_text: Hook text to add
        character: Current character name (if any)
        party_names: List of party names for detection
    """
    if party_names is None:
        party_names = []

    if section == "character_hooks":
        # Detect character in hook text if not set
        detected_char = character
        if not detected_char:
            for char_name in party_names:
                if char_name.lower() in hook_text.lower():
                    detected_char = char_name
                    break

        if detected_char:
            if detected_char not in results["character_specific_hooks"]:
                results["character_specific_hooks"][detected_char] = []
            results["character_specific_hooks"][detected_char].append(hook_text)
        else:
            if "unassigned" not in results["character_specific_hooks"]:
                results["character_specific_hooks"]["unassigned"] = []
            results["character_specific_hooks"]["unassigned"].append(hook_text)
    elif section:
        results[section].append(hook_text)

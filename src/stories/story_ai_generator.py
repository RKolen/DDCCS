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
        descriptions = []
        for name, profile in party_characters.items():
            if isinstance(profile, dict):
                char_class = profile.get("dnd_class", "Unknown")
                personality = profile.get("personality_summary", "")
                descriptions.append(f"- {name} ({char_class}): {personality}")
        if descriptions:
            context_parts.append("\nParty Members:\n" + "\n".join(descriptions))

    # Add NPC context from known NPCs relevant to the location
    if known_npcs:
        npc_descriptions = []
        for npc in known_npcs:
            name = npc.get("name", "Unknown")
            role = npc.get("role", "NPC")
            personality = npc.get("personality", "")
            location = npc.get("location", "")
            npc_descriptions.append(
                f"- {name} ({role} at {location}): {personality}"
            )
        if npc_descriptions:
            context_parts.append(
                "\nKnown NPCs at this location:\n" + "\n".join(npc_descriptions)
            )

    # Add campaign context
    if campaign_context:
        context_parts.append(f"\nCampaign Setting: {campaign_context}")

    return "".join(context_parts)


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

    # Extract configuration with defaults
    if story_config is None:
        story_config = {}

    party_characters = story_config.get("party_characters")
    known_npcs = story_config.get("known_npcs")
    campaign_context = story_config.get("campaign_context")
    max_tokens = story_config.get("max_tokens", 2000)
    is_exploration = story_config.get("is_exploration", False)

    # Build combined context (including NPC context now)
    context = _build_story_context(
        party_characters, campaign_context, known_npcs
    )

    # Look up D&D spells/abilities for accurate descriptions
    ability_context = lookup_spells_and_abilities(story_prompt)

    # Construct the system prompt for D&D storytelling
    base_prompt = (
        "You are an experienced D&D Dungeon Master crafting engaging narrative. "
        "Write story descriptions in third person. Focus on atmosphere, character "
        "reactions, and plot development. Keep descriptions vivid but concise "
        "(max 80 chars per line). Respect D&D 5e conventions and the party's "
        "character personalities. Do not include dice rolls, mechanics, or "
        "meta-game information in the narrative."
    )

    # Add exploration constraint if requested
    if is_exploration:
        base_prompt += (
            " Do NOT include combat, fighting, or hostile action. Focus on "
            "character interactions, exploration, discovery, and social dynamics."
        )

    system_prompt = base_prompt

    # Construct the user prompt
    user_prompt = (
        f"Write a D&D story scene based on this prompt:\n{story_prompt}"
        f"{context}"
        f"{ability_context}\n\n"
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
            max_tokens=max_tokens,
            temperature=0.8,
        )

        # Extract generated text
        generated_text = response.choices[0].message.content.strip()
        return generated_text

    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Failed to generate story: {e}")
        return None


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


def _parse_session_analysis(
    analysis: str,
    party_names: list
) -> Dict[str, Any]:
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


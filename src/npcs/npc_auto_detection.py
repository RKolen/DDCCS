"""
NPC Auto-Detection Module

Handles NPC detection in story content and AI-powered NPC profile generation.
"""

import os
import re
import json
from typing import Dict, List, Any, Tuple
from src.validation.npc_validator import validate_npc_json
from src.utils.file_io import save_json_file
from src.utils.path_utils import get_npcs_dir, get_npc_file_path

# NPC detection patterns - compiled at module level
NPC_PATTERNS: List[Tuple[str, str]] = [
    # "innkeeper named X" or "innkeeper called X" - must have "named" or "called"
    (
        r"(?:innkeeper|bartender|barkeep)[^.]*?(?:named|called)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "Innkeeper",
    ),
    # "X, the innkeeper" - name must come before title
    (
        r"(?<![.!?]\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:the\s+)?"
        r"(?:innkeeper|bartender|barkeep)",
        "Innkeeper",
    ),
    # "merchant named X"
    (
        r"(?:merchant|trader|shopkeeper)[^.]*?(?:named|called)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "Merchant",
    ),
    # "guard captain X" or "Captain X"
    (
        r"(?:guard\s+captain|captain)[^.]*?(?:named|called)?\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "Guard Captain",
    ),
    # "blacksmith X" or "X the blacksmith"
    (
        r"(?:blacksmith|smith)[^.]*?(?:named|called)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        "Blacksmith",
    ),
    (
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:the\s+)?"
        r"(?:blacksmith|smith)",
        "Blacksmith",
    ),
]

# False positive filters
FALSE_POSITIVES = [
    "the", "a", "an", "The", "A", "An", "And", "But", "Or", "So",
    "Then", "When", "Where", "What", "Who", "Why", "How", "This",
    "That", "These", "Those", "Now", "Here", "There",
]


def _create_fallback_profile(npc_name: str, role: str, error_msg: str) -> Dict[str, Any]:
    """Create a fallback NPC profile when AI generation fails."""
    return {
        "name": npc_name,
        "nickname": None,
        "role": role or "NPC",
        "species": "Human",
        "lineage": "",
        "personality": "To be determined",
        "relationships": {},
        "key_traits": [],
        "abilities": [],
        "recurring": False,
        "notes": f"AI generation failed: {error_msg}",
        "ai_config": {
            "enabled": False,
            "temperature": 0.7,
            "max_tokens": 1000,
            "system_prompt": "",
        },
    }


def detect_npc_suggestions(
    story_content: str, party_names: List[str], workspace_path: str
) -> List[Dict[str, str]]:
    """
    Detect potential NPCs in story content that might need profiles created.

    Args:
        story_content: The story text to analyze
        party_names: List of current party member names to exclude
        workspace_path: Path to workspace for checking existing NPC files

    Returns:
        List of dictionaries with NPC suggestions (name, role, context_excerpt, filename)
    """
    suggestions = []
    seen_npcs = set()

    for pattern, default_role in NPC_PATTERNS:
        for match in re.finditer(pattern, story_content):
            npc_name = match.group(1)

            # Filter out false positives
            if (
                npc_name not in FALSE_POSITIVES
                and not npc_name.startswith("The ")
                and npc_name not in party_names
                and npc_name not in seen_npcs
            ):

                # Check if NPC profile already exists
                npc_filename = os.path.basename(get_npc_file_path(npc_name, workspace_path))
                npc_path = get_npc_file_path(npc_name, workspace_path)

                if not os.path.exists(npc_path):
                    # Get context around the NPC mention
                    start = max(0, match.start() - 100)
                    end = min(len(story_content), match.end() + 100)
                    context = story_content[start:end].strip()

                    suggestions.append(
                        {
                            "name": npc_name,
                            "role": default_role,
                            "context_excerpt": context,
                            "filename": npc_filename,
                        }
                    )
                    seen_npcs.add(npc_name)

    return suggestions


def generate_npc_from_story(
    npc_name: str,
    context: str,
    role: str = None,
    ai_client=None,
) -> Dict[str, Any]:
    """
    Generate an NPC profile based on story context using AI.

    Args:
        npc_name: Name of the NPC
        context: Story context where NPC appears
        role: Optional role hint (e.g., "innkeeper", "merchant")
        ai_client: Optional AI client for enhanced generation

    Returns:
        NPC profile dictionary ready to save as JSON
    """
    if not ai_client:
        # Fallback without AI
        return {
            "name": npc_name,
            "nickname": None,
            "role": role or "NPC",
            "species": "Human",
            "lineage": "",
            "personality": "To be determined",
            "relationships": {},
            "key_traits": [],
            "abilities": [],
            "recurring": False,
            "notes": "Generated placeholder - needs manual customization",
            "ai_config": {
                "enabled": False,
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": "",
            },
        }

    try:
        prompt = f"""Based on this story context, generate a detailed D&D NPC profile
for {npc_name}.

Story Context:
{context[:1000]}

NPC Name: {npc_name}
{f"Role: {role}" if role else ""}

Generate a JSON profile with:
1. species: D&D species/ancestry (Human, Elf, Dwarf, Tiefling, etc.)
2. lineage: Optional subspecies (e.g., "High Elf", "Hill Dwarf", "Fire Genasi") - empty string if not applicable
3. personality: 2-3 sentence personality description
4. key_traits: Array of 3-5 distinctive traits
5. abilities: Array of 2-4 notable skills or abilities
6. recurring: boolean - should this NPC appear again?
7. notes: Any secrets, motivations, or hidden agendas
8. relationships: Object with any mentioned character names as keys

Be specific and D&D-appropriate. Make them memorable and useful for the story.

Return ONLY valid JSON in this format:
{{
  "species": "Human",
  "lineage": "",
  "personality": "description",
  "key_traits": ["trait1", "trait2"],
  "abilities": ["ability1", "ability2"],
  "recurring": true/false,
  "notes": "secrets or notes",
  "relationships": {{}}
}}"""

        response = ai_client.chat_completion(
            messages=[{"role": "user", "content": prompt}], temperature=0.7
        )

        # Try to parse the AI response as JSON
        # Extract JSON from response (might have markdown code blocks)
        json_text = response.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()

        npc_data = json.loads(json_text)

        # Build complete NPC profile
        npc_profile = {
            "name": npc_name,
            "nickname": None,
            "role": role or npc_data.get("role", "NPC"),
            "species": npc_data.get("species", "Human"),
            "lineage": npc_data.get("lineage", ""),
            "personality": npc_data.get("personality", "To be determined"),
            "relationships": npc_data.get("relationships", {}),
            "key_traits": npc_data.get("key_traits", []),
            "abilities": npc_data.get("abilities", []),
            "recurring": npc_data.get("recurring", False),
            "notes": npc_data.get("notes", ""),
            "ai_config": {
                "_comment": "AI uses centralized .env settings. "
                "Set enabled=true for AI-driven dialogue.",
                "enabled": False,
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": (
                    f"You are {npc_name}, "
                    f"{npc_data.get('personality', 'an NPC in the story')}."
                ),
            },
        }

        return npc_profile

    except (KeyError, ValueError, TypeError, AttributeError) as e:
        print(f"[WARNING]  AI NPC generation failed: {e}")
        # Return fallback profile when AI generation fails
        return _create_fallback_profile(npc_name, role, str(e))


def save_npc_profile(
    npc_profile: Dict[str, Any], workspace_path: str
) -> str:
    """
    Save an NPC profile to the game_data/npcs/ directory.

    Args:
        npc_profile: NPC profile dictionary
        workspace_path: Path to workspace root

    Returns:
        Path to saved NPC file
    """
    # Validate before saving
    try:
        is_valid, errors = validate_npc_json(npc_profile)
        if not is_valid:
            print("[WARNING]  NPC profile validation failed:")
            for error in errors:
                print(f"  - {error}")
            print("  Saving anyway, but please fix these issues.")
    except ImportError:
        pass  # Validator not available, skip validation

    npcs_path = get_npcs_dir(workspace_path)
    os.makedirs(npcs_path, exist_ok=True)

    # Create filename from name
    filepath = get_npc_file_path(npc_profile["name"], workspace_path)

    save_json_file(filepath, npc_profile)

    print(f"[SUCCESS] Saved NPC profile: {os.path.basename(filepath)}")
    return filepath

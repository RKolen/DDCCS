#!/usr/bin/env python3
"""
Story Analyzer - Intelligent suggestions for character development and NPC creation.

This module analyzes story content and provides suggestions for:
- Character relationship updates
- Major plot action logging
- Character development (new traits, motivations, fears)
- NPC creation based on story interactions
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

from src.characters.consultants.consultant_core import CharacterConsultant
from src.validation.npc_validator import validate_npc_json
from src.utils.file_io import load_json_file, save_json_file, read_text_file
from src.stories.character_loader import load_all_character_consultants


class NPCProfileAnalyzer:
    """Analyzes story content and suggests NPC profile creation."""

    def __init__(
        self,
        characters_dir: str = "game_data/characters",
        npcs_dir: str = "game_data/npcs",
    ):
        self.characters_dir = Path(characters_dir)
        self.npcs_dir = Path(npcs_dir)
        self.consultants: Dict[str, CharacterConsultant] = {}
        self.existing_npcs: Set[str] = set()

        # Load all character consultants
        self._load_character_consultants()
        self._load_existing_npcs()

    def _load_character_consultants(self):
        """Load all character consultants from JSON files."""
        # Delegate to centralized loader which will ensure directory
        # existence and handle loading errors internally.
        self.consultants = load_all_character_consultants(
            str(self.characters_dir), verbose=False
        )

    def _load_existing_npcs(self):
        """Load list of existing NPCs."""
        if not self.npcs_dir.exists():
            return

        for npc_file in self.npcs_dir.glob("*.json"):
            # Skip example files
            if npc_file.name.startswith("npc.example"):
                continue
            try:
                npc_data = load_json_file(str(npc_file))
                if "name" in npc_data:
                    self.existing_npcs.add(npc_data["name"])
            except (OSError, ValueError) as e:
                print(f"Error loading NPC from {npc_file}: {e}")

    def analyze_story_file(
        self, story_file_path: str
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Analyze a story file and return suggestions for all characters.

        Returns:
            Dict mapping character names to their suggestions dict
        """
        if not os.path.exists(story_file_path):
            print(f"Story file '{story_file_path}' not found.")
            return {}

        story_content = read_text_file(story_file_path)

        chapter_name = Path(story_file_path).stem
        all_suggestions = {}

        for character_name, consultant in self.consultants.items():
            suggestions = consultant.analyze_story_content(story_content, chapter_name)

            # Add NPC creation suggestions
            suggestions["npc_creation"] = self._suggest_npc_creation(
                story_content, character_name
            )

            if any(suggestions.values()):  # Only include if there are suggestions
                all_suggestions[character_name] = suggestions

        return all_suggestions

    def _suggest_npc_creation(
        self, story_content: str, for_character: str
    ) -> List[str]:
        """Suggest creating new NPCs based on story interactions."""
        suggestions = []

        # Look for unnamed characters mentioned in the story
        unnamed_patterns = [
            r"the (shopkeeper|guard|merchant|captain|priest|wizard|noble)",
            r"a (stranger|traveler|soldier|villager|farmer|scholar)",
            r"an? (innkeeper|blacksmith|healer|messenger|apprentice)",
        ]

        for pattern in unnamed_patterns:
            matches = re.finditer(pattern, story_content, re.IGNORECASE)
            for match in matches:
                role = match.group(1)
                if role.lower() not in (npc.lower() for npc in self.existing_npcs):
                    suggestions.append(
                        f"SUGGESTION: Create NPC '{role.title()}' "
                        f"- appears to interact with {for_character}"
                    )

        # Look for quoted dialogue that might indicate NPCs
        dialogue_pattern = r'"([^"]+)"'
        dialogue_matches = re.finditer(dialogue_pattern, story_content)

        context_around_dialogue = []
        for match in dialogue_matches:
            start = max(0, match.start() - 100)
            end = min(len(story_content), match.end() + 100)
            context = story_content[start:end]

            # If this dialogue isn't from a known character, suggest NPC creation
            if not any(char_name in context for char_name in self.consultants):
                context_around_dialogue.append(context)

        if len(context_around_dialogue) > 0:
            suggestions.append(
                f"SUGGESTION: Dialogue found without clear speaker "
                f"- consider creating NPCs for {len(context_around_dialogue)} unnamed speakers"
            )

        return suggestions

    def generate_npc_template(
        self, npc_name: str, role: str, interacted_with: str
    ) -> Dict:
        """Generate a template for a new NPC based on story context."""
        template = {
            "name": npc_name,
            "role": role,
            "species": "Human",
            "lineage": "",
            "location": "Unknown",
            "personality": {
                "summary": f"A {role} who has interacted with {interacted_with}",
                "traits": [],
                "motivations": [],
                "fears_weaknesses": [],
            },
            "relationships": {
                interacted_with: "Recent acquaintance - relationship to be developed"
            },
            "notes": [
                f"Created based on story interaction with {interacted_with}",
                "Personality and background need to be fleshed out",
                "Update species and lineage to match character description",
            ],
        }
        return template

    def save_npc_template(self, npc_data: Dict) -> bool:
        """Save a new NPC template to the npcs directory."""
        try:
            # Validate before saving
            try:
                is_valid, errors = validate_npc_json(npc_data)
                if not is_valid:
                    print("[WARNING]  NPC template validation failed:")
                    for error in errors:
                        print(f"  - {error}")
                    print("  Saving anyway, but please fix these issues.")
            except (NameError, ImportError):
                pass  # Validator not available, skip validation

            if not self.npcs_dir.exists():
                self.npcs_dir.mkdir(parents=True, exist_ok=True)

            npc_filename = f"{npc_data['name'].replace(' ', '_')}.json"
            npc_path = self.npcs_dir / npc_filename

            save_json_file(str(npc_path), npc_data)

            print(f"Created NPC template: {npc_path}")
            return True
        except (OSError, TypeError, ValueError) as e:
            print(f"Error saving NPC template: {e}")
            return False

    def update_character_file(self, character_name: str, updates: Dict) -> bool:
        """Apply suggested updates to a character file."""
        character_file = (
            self.characters_dir / f"{character_name.lower().replace(' ', '_')}.json"
        )

        if not character_file.exists():
            print(f"Character file not found: {character_file}")
            return False

        try:
            character_data = load_json_file(str(character_file))

            # Apply updates based on update type
            if "relationships" in updates:
                if "relationships" not in character_data:
                    character_data["relationships"] = {}
                character_data["relationships"].update(updates["relationships"])

            if "major_plot_actions" in updates:
                if "major_plot_actions" not in character_data:
                    character_data["major_plot_actions"] = []
                character_data["major_plot_actions"].extend(
                    updates["major_plot_actions"]
                )

            if "personality_traits" in updates:
                if "personality" not in character_data:
                    character_data["personality"] = {}
                if "traits" not in character_data["personality"]:
                    character_data["personality"]["traits"] = []
                character_data["personality"]["traits"].extend(
                    updates["personality_traits"]
                )

            # Save updated file
            save_json_file(str(character_file), character_data)

            print(f"Updated character file: {character_file}")
            return True
        except (OSError, TypeError, ValueError) as e:
            print(f"Error updating character file: {e}")
            return False

    def print_suggestions_summary(self, suggestions: Dict[str, Dict[str, List[str]]]):
        """Print a formatted summary of all suggestions."""
        if not suggestions:
            print("No suggestions found.")
            return

        print("\n" + "=" * 60)
        print("STORY ANALYSIS SUGGESTIONS")
        print("=" * 60)

        for character_name, char_suggestions in suggestions.items():
            print(f"\n {character_name}")
            print("-" * (len(character_name) + 2))

            for category, suggestion_list in char_suggestions.items():
                if suggestion_list:
                    print(f"\n  {category.replace('_', ' ').title()}:")
                    for suggestion in suggestion_list:
                        print(f"    • {suggestion}")

        print("\n" + "=" * 60)


def main():
    """Interactive story analysis tool."""
    # import already at top

    analyzer = NPCProfileAnalyzer()

    if len(sys.argv) > 1:
        # Analyze specific file
        story_file = sys.argv[1]
        suggestions = analyzer.analyze_story_file(story_file)
        analyzer.print_suggestions_summary(suggestions)
    else:
        # Interactive mode
        print("Story Analyzer - Intelligent Character Development Suggestions")
        print("=" * 60)

        # List available story files
        story_files = list(Path(".").glob("0*.md"))
        if not story_files:
            print("No story files found (looking for 0*.md pattern)")
            return

        print(f"\nFound {len(story_files)} story files:")
        for i, file in enumerate(story_files, 1):
            print(f"  {i}. {file.name}")

        try:
            choice = input("\nEnter file number to analyze (or filename): ").strip()

            if choice.isdigit():
                file_index = int(choice) - 1
                if 0 <= file_index < len(story_files):
                    story_file = str(story_files[file_index])
                else:
                    print("Invalid file number.")
                    return
            else:
                story_file = choice

            suggestions = analyzer.analyze_story_file(story_file)
            analyzer.print_suggestions_summary(suggestions)

        except KeyboardInterrupt:
            print("\nAnalysis cancelled.")
        except (OSError, TypeError, ValueError) as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

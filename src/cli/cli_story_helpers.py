"""
Story Manager Helper Module

Provides helper functions for character selection, story continuation,
and session management to reduce complexity in cli_story_manager.py.
"""

import os
import json
from typing import List, Dict, Any
from src.cli.party_config_manager import load_current_party, load_party_with_profiles
from src.cli.dnd_cli_helpers import get_combat_narrative_style
from src.stories.story_updater import StoryUpdater, ContinuationConfig
from src.stories.story_ai_generator import (
    generate_session_results_from_story,
    generate_story_from_prompt,
)
from src.stories.session_results_manager import (
    StorySession,
    populate_session_from_ai_results,
)
from src.combat.combat_narrator import CombatNarrator
from src.utils.npc_lookup_helper import load_relevant_npcs_for_prompt


class CharacterSelectionHelper:
    """Helper for character listing and party selection."""

    def __init__(self, workspace_path: str):
        """Initialize with workspace path."""
        self.workspace_path = workspace_path

    def list_available_characters(self) -> List[str]:
        """Return names of available characters from game_data/characters.

        Prefer the in-file "name" field; fallback to filename stem on errors.
        Skips example and template files.
        """
        chars_dir = os.path.join(self.workspace_path, "game_data", "characters")
        names: List[str] = []
        if not os.path.isdir(chars_dir):
            return names

        for fname in sorted(os.listdir(chars_dir)):
            if not fname.lower().endswith(".json"):
                continue
            if "example" in fname.lower() or "template" in fname.lower():
                continue
            path = os.path.join(chars_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    name = data.get("name") or os.path.splitext(fname)[0]
            except (OSError, ValueError, json.JSONDecodeError):
                name = os.path.splitext(fname)[0]
            names.append(name)
        return names

    def select_party_members(self, available: List[str], series_name: str) -> List[str]:
        """Prompt user to select party members from available list."""
        if available:
            print("\nAvailable characters:")
            for i, nm in enumerate(available, 1):
                print(f"  {i}. {nm}")
            prompt = "Select by number (comma-separated), or leave blank for defaults: "
        else:
            prompt = "Enter party members (comma-separated), or blank for defaults: "

        party_input = input(prompt).strip()
        if not party_input:
            try:
                return load_current_party(
                    workspace_path=self.workspace_path, campaign_name=series_name
                )
            except (ImportError, OSError, ValueError):
                return []

        members: List[str] = []
        if any(ch.isdigit() for ch in party_input):
            selections = [s.strip() for s in party_input.split(",") if s.strip()]
            for sel in selections:
                try:
                    idx = int(sel)
                except ValueError:
                    members.append(sel)
                    continue
                if 1 <= idx <= len(available):
                    members.append(available[idx - 1])
                else:
                    print(f"Warning: selection {idx} out of range, ignored.")
        else:
            members = [p.strip() for p in party_input.split(",") if p.strip()]

        return members


class StoryContinuationHelper:
    """Helper for story continuation and session management."""

    def __init__(self, story_manager, workspace_path: str):
        """Initialize with story manager and workspace path."""
        self.story_manager = story_manager
        self.workspace_path = workspace_path
        self.story_updater = StoryUpdater()

    def populate_session_with_ai_analysis(
        self,
        session: StorySession,
        story_content: str,
        party_characters: Dict[str, Any],
    ) -> None:
        """Populate session with AI-analyzed character actions."""
        if not self.story_manager.ai_client:
            return

        try:
            party_names = list(party_characters.keys())
            ai_results = generate_session_results_from_story(
                self.story_manager.ai_client, story_content, party_names
            )
            if ai_results:
                populate_session_from_ai_results(session, ai_results)
        except (AttributeError, ValueError, KeyError, TypeError):
            pass

    def handle_combat_continuation(
        self, story_path: str, display_name: str, story_prompt: str
    ) -> None:
        """Handle combat narrative generation."""
        style = get_combat_narrative_style()
        combat_narrator = CombatNarrator(
            self.story_manager.consultants,
            self.story_manager.ai_client,
        )
        ai_content = combat_narrator.narrate_combat_from_prompt(
            combat_prompt=story_prompt,
            story_context="",
            style=style,
        )
        if ai_content:
            combat_title = combat_narrator.generate_combat_title(story_prompt, "")
            self.story_updater.append_combat_narrative(
                story_path, ai_content, combat_title, story_prompt
            )
            print(f"\n[SUCCESS] Added combat narrative to {display_name}")
            print(f"   Title: {combat_title}")
            print("You can now edit and refine the generated content.")
        else:
            print("[WARNING] AI generation returned no content.")

    def handle_exploration_continuation(
        self,
        story_path: str,
        display_name: str,
        story_prompt: str,
        campaign_dir: str,
    ) -> None:
        """Handle exploration/social narrative generation."""
        party_characters = load_party_with_profiles(campaign_dir, self.workspace_path)
        known_npcs = load_relevant_npcs_for_prompt(story_prompt, self.workspace_path)
        ai_content = generate_story_from_prompt(
            self.story_manager.ai_client,
            story_prompt,
            {
                "party_characters": party_characters,
                "known_npcs": known_npcs,
                "is_exploration": True,
            },
        )
        if ai_content:
            config = (
                ContinuationConfig()
                .set_paths(story_path, campaign_dir, self.workspace_path)
                .set_content(ai_content)
                .set_ai_client(self.story_manager.ai_client)
                .set_prompt(story_prompt)
            )
            success = self.story_updater.append_ai_continuation(config)
            if success:
                print(f"\n[SUCCESS] Added exploration narrative to {display_name}")
                print("You can now edit and refine the generated content.")
        else:
            print("[WARNING] AI generation returned no content.")

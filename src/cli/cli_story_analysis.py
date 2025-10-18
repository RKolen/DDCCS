"""
Story Analysis CLI Module

Handles story analysis and combat conversion operations.
"""

import os
from typing import Dict, Any

# Optional AI client import
try:
    from src.ai.ai_client import AIClient
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AIClient = None
    AI_CLIENT_AVAILABLE = False

from src.combat.combat_narrator import CombatNarrator
from src.cli.dnd_cli_helpers import (
    get_multi_line_combat_input,
    select_narrative_style,
    select_target_story_for_combat,
    save_combat_narrative,
)


class StoryAnalysisCLI:
    """Manages story analysis and combat conversion operations."""

    def __init__(self, story_manager, workspace_path):
        """
        Initialize story analysis CLI manager.

        Args:
            story_manager: StoryManager instance
            workspace_path: Root workspace path
        """
        self.story_manager = story_manager
        self.workspace_path = workspace_path
        self.ai_client = None
        self.combat_narrator = CombatNarrator(story_manager.consultants)

    def analyze_story(self):
        """Analyze a story file."""
        story_files = self.story_manager.get_story_files()

        if not story_files:
            print("\n❌ No story files found.")
            return

        print("\n🔍 ANALYZE STORY FILE")
        print("-" * 30)
        for i, filename in enumerate(story_files, 1):
            print(f"{i}. {filename}")

        try:
            choice = int(input("Enter file number: ")) - 1
            if 0 <= choice < len(story_files):
                filename = story_files[choice]
                filepath = os.path.join(self.story_manager.stories_path, filename)

                print(f"\n🔄 Analyzing {filename}...")
                analysis = self.story_manager.analyze_story_file(filepath)

                if "error" in analysis:
                    print(f"❌ {analysis['error']}")
                    return

                self._display_story_analysis(analysis)

                # Ask if they want to update the file
                update = (
                    input("\nUpdate story file with analysis? (y/n): ").strip().lower()
                )
                if update == "y":
                    self.story_manager.update_story_with_analysis(filepath, analysis)
            else:
                print("Invalid file number.")
        except ValueError:
            print("Invalid input.")

    def _display_story_analysis(self, analysis: Dict[str, Any]):
        """Display story analysis results."""
        print(f"\n📊 STORY ANALYSIS: {analysis['story_file']}")
        print("=" * 50)

        # Overall consistency
        overall = analysis.get("overall_consistency", {})
        print(f"Overall Consistency: {overall.get('rating', 'Unknown')}")
        print(f"Score: {overall.get('score', 0)}/1.0")
        print(f"Summary: {overall.get('summary', 'No analysis')}")

        # Character analyses
        if analysis.get("consultant_analyses"):
            print("\n👥 CHARACTER ANALYSES:")
            for character, char_analysis in analysis["consultant_analyses"].items():
                print(f"\n• {character}: {char_analysis['overall_rating']}")
                print(f"  Score: {char_analysis['consistency_score']}/1.0")

                if char_analysis.get("positive_notes"):
                    print(f"  ✅ Positives: {len(char_analysis['positive_notes'])}")

                if char_analysis.get("issues"):
                    print(f"  ⚠️ Issues: {len(char_analysis['issues'])}")
                    for issue in char_analysis["issues"][:2]:  # Show first 2
                        print(f"    - {issue}")

        # DC suggestions
        if analysis.get("dc_suggestions"):
            print("\n🎲 DC SUGGESTIONS:")
            for request, suggestions in analysis["dc_suggestions"].items():
                print(f"\n• {request}")
                for character, suggestion in suggestions.items():
                    print(
                        f"  {character}: DC {suggestion['suggested_dc']}"
                        f" ({suggestion['reasoning']})"
                    )

        input("\nPress Enter to continue...")

    def convert_combat(self):
        """Convert combat description to narrative."""
        print("\n⚔️ CONVERT COMBAT TO NARRATIVE")
        print("-" * 50)
        print("Describe what happened in combat tactically. Example:")
        print("  Theron charges forward and strikes the goblin with his longsword.")
        print("  Mira sneaks behind an enemy and backstabs with her dagger.")
        print("  Garrick swings his warhammer, crushing the goblin's shield.")
        print()

        # Get combat description from user
        combat_prompt = get_multi_line_combat_input()
        if not combat_prompt:
            print("No combat description provided.")
            return

        # Select narrative style
        style = select_narrative_style()

        # Select target story file and get context
        target_story_path, story_context = select_target_story_for_combat(
            self.workspace_path, self.story_manager
        )

        print(f"\n🔄 Converting to {style} narrative...")

        # Initialize AI client if needed
        self._ensure_ai_client_initialized()

        # Recreate combat narrator with AI client
        self.combat_narrator = CombatNarrator(
            self.story_manager.consultants, self.ai_client
        )

        # Generate combat title automatically
        print("🏷️  Generating combat title...")
        combat_title = self.combat_narrator.generate_combat_title(
            combat_prompt, story_context
        )
        print(f"   Title: {combat_title}")

        # Generate narrative
        narrative = self.combat_narrator.narrate_combat_from_prompt(
            combat_prompt=combat_prompt, story_context=story_context, style=style
        )

        print("\n📝 COMBAT NARRATIVE:")
        print("=" * 70)
        print(narrative)
        print("=" * 70)

        # Save or append the narrative
        save_combat_narrative(
            narrative, combat_title, target_story_path, self.workspace_path
        )

    def _ensure_ai_client_initialized(self):
        """Ensure AI client is initialized, or set to None if unavailable."""
        if not hasattr(self, "ai_client") or self.ai_client is None:
            if AI_CLIENT_AVAILABLE:
                try:
                    self.ai_client = AIClient()
                except (AttributeError, ValueError) as e:
                    print(f"⚠️  Could not initialize AI client: {e}")
                    print("   Using fallback mode...")
                    self.ai_client = None
            else:
                print("⚠️  AI client not available")
                print("   Using fallback mode...")
                self.ai_client = None

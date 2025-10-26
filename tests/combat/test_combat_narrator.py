"""Tests for `src.combat.combat_narrator.CombatNarrator`.

Uses real character JSON fixtures (aragorn, frodo, gandalf) from game_data
so we exercise CharacterProfile and CharacterConsultant wiring.
"""

import sys
from pathlib import Path
import unittest
import test_helpers
from test_helpers import FakeAIClient
# Ensure tests package and project root are importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure test environment so 'src' package can be imported
test_helpers.setup_test_environment()

try:
    from src.combat.combat_narrator import CombatNarrator
    from src.characters.consultants.character_profile import CharacterProfile
    from src.characters.consultants.consultant_core import CharacterConsultant
except ImportError as exc:
    print(f"[ERROR] Import failed: {exc}")
    raise


def _load_fixture(name: str) -> CharacterConsultant:
    base = Path(__file__).parent.parent.parent
    fp = base / "game_data" / "characters" / f"{name}.json"
    profile = CharacterProfile.load_from_file(str(fp))
    return CharacterConsultant(profile)


class TestCombatNarrator(unittest.TestCase):
    """Tests for CombatNarrator using real character fixtures."""

    def setUp(self) -> None:
        """Load real character fixtures and prepare consultants mapping."""
        self.aragorn = _load_fixture("aragorn")
        self.frodo = _load_fixture("frodo")
        self.gandalf = _load_fixture("gandalf")

        self.consultants = {
            self.aragorn.profile.name: self.aragorn,
            self.frodo.profile.name: self.frodo,
            self.gandalf.profile.name: self.gandalf,
        }

    def test_narrate_fallback_and_title(self):
        """Fallback narration uses non-AI path and extracts title from prompt."""
        narrator = CombatNarrator(self.consultants, ai_client=None)

        prompt = "aragorn attacks a goblin. frodo heals aragorn."
        narrative = narrator.narrate_combat_from_prompt(prompt, style="cinematic")

        # Fallback narrator includes the scene header and capitalizes names
        self.assertIn("Combat Scene", narrative)
        self.assertIn("Aragorn", narrative)

        title = narrator.generate_combat_title(prompt)
        # With AI disabled, title is extracted from creature names
        self.assertIn("Goblin", title)

    def test_enhance_with_character_consistency(self):
        """Ensure consistency notes are appended when applicable."""
        narrator = CombatNarrator(self.consultants, ai_client=None)
        base = "A melee erupted."
        actions = {"Aragorn": ["attack the goblin"], "Frodo": ["hide"]}

        enhanced = narrator.enhance_with_character_consistency(base, actions)
        self.assertIn("Character Consistency Notes", enhanced)
        self.assertIn("**Aragorn:**", enhanced)

    def test_ai_path_integration_mocked(self):
        """When AI client is present, its output is used in narration."""
        fake = FakeAIClient()
        narrator = CombatNarrator(self.consultants, ai_client=fake)

        prompt = "Aragorn charges the orc with a mighty shout."
        out = narrator.narrate_combat_from_prompt(prompt)
        # The fake AI returns a canned string; ensure it's present after processing
        self.assertIn("generated combat narrative", out)


if __name__ == "__main__":
    unittest.main()

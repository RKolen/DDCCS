"""Test DMConsultant consistency notes when NPC relationships exist."""

from tests.test_helpers import setup_test_environment, DM_DUNGEON_MASTER, import_module

setup_test_environment()

# Import DM module
dm_module = DM_DUNGEON_MASTER or import_module("src.dm.dungeon_master")
DMConsultant = dm_module.DMConsultant


class SimpleProfile:
    """Minimal profile object used for fake agents and consultants."""

    def __init__(self, name, personality_summary=None, role=None, relationships=None):
        self.name = name
        self.personality_summary = personality_summary or "quiet and thoughtful"
        self.role = role or "civilian"
        self.relationships = relationships or {}

    def describe(self) -> str:
        """Return a short human-readable description of the profile.

        Tests use this helper to include profile text in generated notes; adding
        a small public method also keeps pylint from flagging too-few-public-methods
        for these simple test fixtures.
        """
        return f"{self.name}: {self.personality_summary} ({self.role})"

    def summary(self) -> str:
        """Return a concise personality summary string used in assertions."""
        return self.personality_summary


class FakeAgent:
    """Minimal NPC agent with a profile attribute."""

    def __init__(self, profile):
        self.profile = profile

    def get_profile(self):
        """Return the underlying profile object.

        This convenience is used by tests exercising the DM public APIs and
        keeps the helper class more expressive for assertions.
        """
        return self.profile

    def agent_name(self) -> str:
        """Return the agent's profile name for convenience in tests."""
        return getattr(self.profile, "name", "")


class FakeConsultantWithProfile:
    """Minimal consultant with profile required by DMConsultant consistency checks."""

    def __init__(self, profile):
        self.profile = profile

    def suggest_reaction(self, prompt, extra=None):  # pragma: no cover - simple passthrough
        """Return a deterministic suggested reaction used by the tests.

        Keep this method minimal; the pragma excludes it from coverage as it's
        a simple passthrough used only in unit tests.
        """
        _ = (prompt, extra)
        return {"suggested_reaction": "Respond", "reasoning": "Test", "class_expertise": "test"}

    def get_profile(self):
        """Return the profile associated with this fake consultant."""
        return self.profile


def test_check_consistency_relationships():
    """When NPCs have relationships with characters,
    consistency notes should include relationship text."""
    dm = DMConsultant(workspace_path=None, ai_client=None)

    # Create character consultant with personality_summary
    char_profile = SimpleProfile("Frodo", personality_summary="timid but brave")
    dm.character_consultants = {"Frodo": FakeConsultantWithProfile(char_profile)}

    # Create NPC agent with relationship to Frodo
    npc_profile = SimpleProfile("Bilbo", role="old friend",
                                relationships={"Frodo": "mentor and guardian"})
    dm.npc_agents = {"Bilbo": FakeAgent(npc_profile)}

    out = dm.suggest_narrative("A reunion scene", characters_present=["Frodo"],
                               npcs_present=["Bilbo"])
    notes = out.get("consistency_notes", [])
    # Expect both personality and relationship notes
    assert any("timid but brave" in n for n in notes)
    assert any("Bilbo and Frodo" in n or "mentor and guardian" in n for n in notes)

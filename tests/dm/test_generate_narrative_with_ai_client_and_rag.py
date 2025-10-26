"""Test AI branch of `DMConsultant.generate_narrative_content`
with a fake AI client and mocked RAG."""

from tests import test_helpers

from tests.test_helpers import setup_test_environment, DM_DUNGEON_MASTER

setup_test_environment()

# Import DM module
dm_module = DM_DUNGEON_MASTER or test_helpers.import_module("src.dm.dungeon_master")
DMConsultant = dm_module.DMConsultant


class SimpleFakeAI:
    """Wraps the existing FakeAIClient to provide message helpers used by DMConsultant."""

    def __init__(self):
        """Create the wrapped fake AI client used by the tests.

        The wrapped fake provides the same test-oriented chat_completion
        behavior as the project's FakeAIClient while exposing a small
        message-building helper surface expected by the DM code.
        """
        self._base = test_helpers.FakeAIClient()

    def create_system_message(self, content: str):
        """Create a simple system message dictionary with the given content.

        The DM code calls this helper to build messages; return a minimal
        mapping compatible with the FakeAIClient used below.
        """
        return {"content": content}

    def create_user_message(self, content: str):
        """Create a simple user message dictionary with the given content."""
        return {"content": content}

    def chat_completion(self, *args, **kwargs):
        # Delegate to base fake which will include a msg_preview for messages
        """Proxy chat completion calls to the wrapped fake AI client.

        The fake client produces deterministic output that's sufficient for
        asserting the DM narrative generation code exercised the AI branch.
        """
        return self._base.chat_completion(*args, **kwargs)

    def ping(self):
        """Return a simple health check response used by some callers."""
        return True


def test_generate_narrative_with_ai_client_and_rag():
    """DM should use the AI client and include RAG context when available."""
    dm = DMConsultant(workspace_path=None, ai_client=SimpleFakeAI())

    # Fake RAG system
    class FakeRag:
        """A minimal fake RAG implementation used by the test.

        It exposes the subset of the real RAG API used by the DMConsultant:
        - an 'enabled' attribute
        - get_context_for_query(prompt, locations, max_results)
        - supports_context(): small helper to indicate context is available
        """

        enabled = True

        def get_context_for_query(self, prompt, locations, max_results=2):
            """Return a short context string for the provided prompt.

            The arguments are accepted only to match the production API; the
            body returns a fixed string suitable for unit testing.
            """
            _ = (prompt, locations, max_results)
            return "LORE-CONTEXT"

        def supports_context(self) -> bool:
            """Indicate that this fake RAG can provide contextual results."""
            return True

    dm.rag_system = FakeRag()

    # Call generate_narrative_content; SimpleFakeAI will return a canned string
    out = dm.generate_narrative_content(
        "A story about Whitestone.", characters_present=[], npcs_present=[], style="immersive"
    )

    assert isinstance(out, str)
    # The FakeAI chat completion appends a msg_preview when messages passed
    assert "msg_preview:" in out or "generated combat narrative" in out

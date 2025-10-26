"""Unit tests for `src.dm.history_check_helper`.

These tests verify DC estimation, detail level mapping, fallback behavior when
RAG is not available, and behavior when a mocked RAG system is provided.
"""

from test_helpers import setup_test_environment, import_module, DM_HISTORY_HELPER

# Configure test environment and import module via shared helpers
setup_test_environment()
# Prefer the pre-imported module object from test_helpers when available
hch = DM_HISTORY_HELPER or import_module("src.dm.history_check_helper")


def test_dc_and_detail_levels_via_api():
    """Verify DC estimation and detail level mapping via the public API."""
    # Common topic: tavern -> DC 10
    res_common = hch.handle_history_check("tavern", check_result=12)
    assert res_common["dc"] == 10
    assert res_common["success"] is True

    # Obscure topic -> higher DC
    res_obscure = hch.handle_history_check("ancient ruins", check_result=19)
    # expected DC for obscure topics is 20: 19 is below -> should be failure
    assert res_obscure["dc"] == 20
    assert res_obscure["success"] is False

    # Very obscure -> DC 25
    res_very = hch.handle_history_check("primordial legend", check_result=25)
    assert res_very["dc"] == 25
    assert res_very["success"] is True

    # Detail levels via API
    assert hch.handle_history_check("topic", check_result=5)["detail_level"] == "vague"
    assert hch.handle_history_check("topic", check_result=12)["detail_level"] == "basic"
    assert hch.handle_history_check("topic", check_result=17)["detail_level"] == "detailed"
    assert hch.handle_history_check("topic", check_result=25)["detail_level"] == "comprehensive"


def test_handle_history_check_failure_and_fallback():
    """Ensure failures return 'failure' source and successful checks use 'fallback' or 'wiki'."""
    res = hch.handle_history_check("tavern", check_result=5)
    assert res["success"] is False
    assert res["source"] == "failure"
    assert res["dc"] == 10

    # A successful roll without RAG should return source 'fallback'
    res2 = hch.handle_history_check("tavern", check_result=12)
    assert res2["success"] is True
    assert res2["source"] in ("fallback", "wiki")
    # detail_level should be consistent with result (12 -> basic)
    assert res2["detail_level"] == "basic"


def test_search_lore_no_rag():
    """search_lore should return an informative message when RAG isn't available."""
    msg = hch.search_lore("Whitestone")
    assert isinstance(msg, str)
    assert "RAG" in msg or "not available" in msg


def test_handle_history_with_mocked_rag(monkeypatch):
    """When RAG provides info, handle_history_check should return wiki-sourced details."""
    # Create a fake rag_system with enabled=True and a predictable response
    class FakeRag:
        """Minimal fake RAG system used by tests to simulate wiki responses."""

        enabled = True

        def get_history_check_info(self, topic, check_result=None):
            """Return a predictable lore string for the given topic and check."""
            return f"Lore about {topic} for check {check_result}"

        def get_context_for_location(self, q):
            """Return a short context string for a queried location."""
            return f"Context for {q}"

    fake = FakeRag()

    # Monkeypatch module-level RAG_AVAILABLE and get_rag_system
    monkeypatch.setattr(hch, "RAG_AVAILABLE", True)
    monkeypatch.setattr(hch, "get_rag_system", lambda: fake)

    res = hch.handle_history_check("Whitestone", check_result=18, character_name="Elara")
    assert res["success"] is True
    assert res["source"] == "wiki"
    assert "Elara recalls" in res["information"] or "You recall" in res["information"]

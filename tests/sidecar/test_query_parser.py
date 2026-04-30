"""Unit tests for src.sidecar.query_parser and src.sidecar.app."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

_app_mod = import_module("src.sidecar.app")
_parser_mod = import_module("src.sidecar.query_parser")
_models_mod = import_module("src.sidecar.models")

app = _app_mod.app
parse_query = _parser_mod.parse_query
reset_client_cache = _parser_mod.reset_client_cache
ParseQueryResponse = _models_mod.ParseQueryResponse

_HTTP = TestClient(app)

_PATCH_TARGET = "src.sidecar.query_parser._build_parser_client"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _mock_client(response_json: str) -> MagicMock:
    """Build a mock AIClient that returns *response_json* from chat_completion.

    Args:
        response_json: String the mock returns from chat_completion.

    Returns:
        Configured MagicMock standing in for AIClient.
    """
    client = MagicMock()
    client.chat_completion.return_value = response_json
    client.create_system_message.return_value = {"role": "system", "content": "sys"}
    client.create_user_message.return_value = {"role": "user", "content": "usr"}
    return client


# ---------------------------------------------------------------------------
# parse_query — happy path
# ---------------------------------------------------------------------------


def test_parse_query_spell_type_inferred() -> None:
    """parse_query returns inferred_type spell when AI response indicates spell."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "fireball", "inferred_type": "spell", "confidence": 0.9}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("show me the fireball spell")
    assert isinstance(result, ParseQueryResponse)
    assert result.query == "fireball"
    assert result.inferred_type == "spell"
    assert result.original == "show me the fireball spell"
    assert abs(result.confidence - 0.9) < 1e-6


def test_parse_query_normalizes_filler_words() -> None:
    """parse_query uses the AI-normalized query, not the raw input."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "paladin", "inferred_type": "character", "confidence": 0.85}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("find me a paladin character")
    assert result.query == "paladin"
    assert result.inferred_type == "character"


def test_parse_query_null_inferred_type_accepted() -> None:
    """parse_query accepts null inferred_type from AI gracefully."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "dragon slayer", "inferred_type": null, "confidence": 0.0}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("dragon slayer")
    assert result.query == "dragon slayer"
    assert result.inferred_type is None


def test_parse_query_handles_markdown_fenced_response() -> None:
    """parse_query correctly parses AI response wrapped in markdown fences."""
    reset_client_cache()
    fenced = (
        '```json\n'
        '{"query": "paladin", "inferred_type": "character", "confidence": 0.8}\n'
        '```'
    )
    mock = _mock_client(fenced)
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("show me a paladin")
    assert result.inferred_type == "character"


# ---------------------------------------------------------------------------
# parse_query — type validation
# ---------------------------------------------------------------------------


def test_parse_query_rejects_unknown_content_type() -> None:
    """parse_query sets inferred_type None when AI returns an unrecognised type."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "dragon", "inferred_type": "beast", "confidence": 0.7}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("dragon")
    assert result.inferred_type is None


def test_parse_query_clamps_confidence_above_max() -> None:
    """parse_query clamps confidence values above 1.0 to exactly 1.0."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "sword", "inferred_type": "item", "confidence": 1.5}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("sword")
    assert result.confidence == 1.0


def test_parse_query_clamps_confidence_below_min() -> None:
    """parse_query clamps confidence values below 0.0 to exactly 0.0."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "potion", "inferred_type": "item", "confidence": -0.5}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("potion")
    assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# parse_query — graceful degradation
# ---------------------------------------------------------------------------


def test_parse_query_degrades_on_runtime_error() -> None:
    """parse_query falls back to raw query when chat_completion raises RuntimeError."""
    reset_client_cache()
    mock = _mock_client("")
    mock.chat_completion.side_effect = RuntimeError("connection refused")
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("fireball")
    assert result.query == "fireball"
    assert result.inferred_type is None
    assert result.confidence == 0.0


def test_parse_query_degrades_on_invalid_json() -> None:
    """parse_query falls back to raw query when AI returns unparseable JSON."""
    reset_client_cache()
    mock = _mock_client("not json at all")
    with patch(_PATCH_TARGET, return_value=mock):
        result = parse_query("fireball")
    assert result.query == "fireball"
    assert result.inferred_type is None


def test_parse_query_no_client_returns_fallback() -> None:
    """parse_query returns the raw query when no AI client is configured."""
    reset_client_cache()
    with patch(_PATCH_TARGET, return_value=None):
        result = parse_query("dragon")
    assert result.query == "dragon"
    assert result.inferred_type is None


# ---------------------------------------------------------------------------
# FastAPI endpoints
# ---------------------------------------------------------------------------


def test_health_endpoint_returns_ok() -> None:
    """GET /health returns status ok with ai_configured field."""
    response = _HTTP.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "ai_configured" in body


def test_parse_query_endpoint_success() -> None:
    """POST /parse-query returns a valid ParseQueryResponse."""
    reset_client_cache()
    mock = _mock_client(
        '{"query": "fireball", "inferred_type": "spell", "confidence": 0.9}'
    )
    with patch(_PATCH_TARGET, return_value=mock):
        response = _HTTP.post("/parse-query", json={"q": "show me fireball spell"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "fireball"
    assert body["inferred_type"] == "spell"
    assert body["original"] == "show me fireball spell"


def test_parse_query_endpoint_rejects_empty_query() -> None:
    """POST /parse-query returns 422 when q is blank."""
    response = _HTTP.post("/parse-query", json={"q": "   "})
    assert response.status_code == 422


def test_parse_query_endpoint_rejects_missing_field() -> None:
    """POST /parse-query returns 422 when q field is absent."""
    response = _HTTP.post("/parse-query", json={})
    assert response.status_code == 422

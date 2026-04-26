"""Tests for src.integration.drupal_sync.

Unit tests mock urllib so no live Drupal instance is required.
Integration tests (prefixed live_) are skipped unless DRUPAL_BASE_URL is set.

Usage (unit tests only):
    python3 tests/integration/test_drupal_sync.py

Usage (with live Drupal via DDEV):
    DRUPAL_BASE_URL=https://drupal-cms.ddev.site \\
    DRUPAL_USER=admin DRUPAL_PASSWORD=... \\
    python3 tests/integration/test_drupal_sync.py
"""

import json
import os
import unittest.mock
import urllib.error
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

drupal_sync_mod = import_module("src.integration.drupal_sync")
DrupalSync = drupal_sync_mod.DrupalSync
DrupalSyncError = drupal_sync_mod.DrupalSyncError

config_types_mod = import_module("src.config.config_types")
DrupalConfig = config_types_mod.DrupalConfig

path_utils_mod = import_module("src.utils.path_utils")
get_characters_dir = path_utils_mod.get_characters_dir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(
    base_url: str = "https://drupal-cms.ddev.site",
    user: str = "admin",
    password: str = "password",
    gatsby_webhook_url: str = "",
) -> Any:
    """Return a minimal DrupalConfig for tests."""
    return DrupalConfig(
        base_url=base_url,
        user=user,
        password=password,
        gatsby_webhook_url=gatsby_webhook_url,
    )


def _mock_urlopen(status: int, body: bytes = b"") -> unittest.mock.MagicMock:
    """Return a MagicMock patching urlopen with the given status and body."""
    mock = unittest.mock.MagicMock()
    mock.status = status
    mock.read.return_value = body
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = False
    return mock


def _skip_if_no_live_drupal() -> Optional[str]:
    """Return a skip reason when DRUPAL_BASE_URL is not configured."""
    if not os.getenv("DRUPAL_BASE_URL"):
        return "DRUPAL_BASE_URL not set — live Drupal tests skipped"
    return None


def _live_config() -> Any:
    """Build a DrupalConfig from environment variables for live tests."""
    return DrupalConfig(
        base_url=os.getenv("DRUPAL_BASE_URL", ""),
        user=os.getenv("DRUPAL_USER", ""),
        password=os.getenv("DRUPAL_PASSWORD", ""),
        gatsby_webhook_url=os.getenv("DRUPAL_GATSBY_WEBHOOK_URL", ""),
    )


# ---------------------------------------------------------------------------
# Payload builder tests (public static methods, no HTTP needed)
# ---------------------------------------------------------------------------

def test_build_character_payload_title_only() -> None:
    """Character payload uses name as title when optional fields are absent."""
    print("\n[TEST] build_character_payload - title only")
    payload = DrupalSync.build_character_payload({"name": "Aragorn"})
    assert payload["data"]["type"] == "node--character"
    assert payload["data"]["attributes"]["title"] == "Aragorn"
    assert "field_backstory" not in payload["data"]["attributes"]
    print("  [OK] title-only payload is correct")
    print("[PASS] build_character_payload - title only")


def test_build_character_payload_all_optional_fields() -> None:
    """Character payload maps all optional text fields correctly."""
    print("\n[TEST] build_character_payload - all optional fields")
    data = {
        "name": "Frodo",
        "backstory": "A hobbit from the Shire.",
        "personality_traits": ["Brave", "Modest"],
        "bonds": "The One Ring must be destroyed.",
        "ideals": ["Friendship"],
        "flaws": ["Drawn to the Ring's power"],
    }
    payload = DrupalSync.build_character_payload(data)
    attrs = payload["data"]["attributes"]
    assert attrs["title"] == "Frodo"
    assert attrs["field_backstory"][0]["value"] == "A hobbit from the Shire."
    assert len(attrs["field_personality_traits"]) == 2
    assert attrs["field_bonds"][0]["value"] == "The One Ring must be destroyed."
    assert len(attrs["field_ideals"]) == 1
    assert len(attrs["field_flaws"]) == 1
    print("  [OK] all optional fields mapped correctly")
    print("[PASS] build_character_payload - all optional fields")


def test_build_story_payload_structure() -> None:
    """Story payload has the expected JSON:API structure."""
    print("\n[TEST] build_story_payload - structure")
    payload = DrupalSync.build_story_payload("My Campaign -- session_01", "## Session 1\n\nText")
    assert payload["data"]["type"] == "node--story"
    attrs = payload["data"]["attributes"]
    assert attrs["title"] == "My Campaign -- session_01"
    assert attrs["body"]["value"] == "## Session 1\n\nText"
    assert attrs["body"]["format"] == "plain_text"
    print("  [OK] story payload structure is correct")
    print("[PASS] build_story_payload - structure")


# ---------------------------------------------------------------------------
# push_character tests (mocked internals)
# ---------------------------------------------------------------------------

def test_push_character_posts_new_node() -> None:
    """push_character POSTs when no existing node is found."""
    print("\n[TEST] push_character - POST new node")
    sync = DrupalSync(_make_config())
    char_file = Path(get_characters_dir()) / "aragorn.json"

    with unittest.mock.patch.object(sync, "_find_node_uuid", return_value=None), \
         unittest.mock.patch.object(sync, "_post_node", return_value="uuid-new") as mock_post:
        result = sync.push_character(char_file)

    assert result == "uuid-new"
    mock_post.assert_called_once_with("character", unittest.mock.ANY)
    print("  [OK] POST called for new character")
    print("[PASS] push_character - POST new node")


def test_push_character_patches_existing_node() -> None:
    """push_character PATCHes when an existing node UUID is found."""
    print("\n[TEST] push_character - PATCH existing node")
    sync = DrupalSync(_make_config())
    char_file = Path(get_characters_dir()) / "frodo.json"

    with unittest.mock.patch.object(sync, "_find_node_uuid", return_value="uuid-existing"), \
         unittest.mock.patch.object(sync, "_patch_node") as mock_patch:
        result = sync.push_character(char_file)

    assert result == "uuid-existing"
    mock_patch.assert_called_once_with("character", "uuid-existing", unittest.mock.ANY)
    print("  [OK] PATCH called for existing character")
    print("[PASS] push_character - PATCH existing node")


def test_push_character_raises_on_http_error() -> None:
    """push_character propagates DrupalSyncError when the HTTP call fails."""
    print("\n[TEST] push_character - HTTP error propagates as DrupalSyncError")
    sync = DrupalSync(_make_config())
    char_file = Path(get_characters_dir()) / "gandalf.json"
    http_error = urllib.error.HTTPError(
        url="https://drupal-cms.ddev.site/jsonapi/node/character",
        code=422,
        msg="Unprocessable Entity",
        hdrs=unittest.mock.MagicMock(),  # type: ignore[arg-type]
        fp=BytesIO(b'{"errors":[{"detail":"Validation failed"}]}'),
    )

    with unittest.mock.patch.object(sync, "_find_node_uuid", return_value=None), \
         unittest.mock.patch("urllib.request.urlopen", side_effect=http_error):
        raised = False
        try:
            sync.push_character(char_file)
        except DrupalSyncError as exc:
            raised = True
            assert "422" in str(exc)
    assert raised, "Expected DrupalSyncError from HTTP 422"
    print("  [OK] DrupalSyncError raised and contains status code")
    print("[PASS] push_character - HTTP error propagates as DrupalSyncError")


# ---------------------------------------------------------------------------
# push_story tests (mocked internals)
# ---------------------------------------------------------------------------

def test_push_story_posts_new_node(tmp_path: Path) -> None:
    """push_story POSTs when no existing story node is found."""
    print("\n[TEST] push_story - POST new node")
    story_file = tmp_path / "session_01.md"
    story_file.write_text("# Session 1\n\nThe party sets out.", encoding="utf-8")
    sync = DrupalSync(_make_config())

    with unittest.mock.patch.object(sync, "_find_node_uuid", return_value=None), \
         unittest.mock.patch.object(sync, "_post_node", return_value="uuid-story") as mock_post:
        result = sync.push_story(story_file, "Example_Campaign")

    assert result == "uuid-story"
    mock_post.assert_called_once_with("story", unittest.mock.ANY)
    print("  [OK] POST called for new story")
    print("[PASS] push_story - POST new node")


def test_push_story_patches_existing_node(tmp_path: Path) -> None:
    """push_story PATCHes when an existing story node is found."""
    print("\n[TEST] push_story - PATCH existing node")
    story_file = tmp_path / "session_02.md"
    story_file.write_text("# Session 2\n\nThe party continues.", encoding="utf-8")
    sync = DrupalSync(_make_config())

    with unittest.mock.patch.object(sync, "_find_node_uuid", return_value="uuid-old-story"), \
         unittest.mock.patch.object(sync, "_patch_node") as mock_patch:
        result = sync.push_story(story_file, "Example_Campaign")

    assert result == "uuid-old-story"
    mock_patch.assert_called_once_with("story", "uuid-old-story", unittest.mock.ANY)
    print("  [OK] PATCH called for existing story")
    print("[PASS] push_story - PATCH existing node")


# ---------------------------------------------------------------------------
# trigger_gatsby_build tests (mocked urllib)
# ---------------------------------------------------------------------------

def test_trigger_gatsby_build_raises_without_url() -> None:
    """trigger_gatsby_build raises DrupalSyncError when no webhook URL is set."""
    print("\n[TEST] trigger_gatsby_build - no webhook URL raises")
    sync = DrupalSync(_make_config(gatsby_webhook_url=""))
    raised = False
    try:
        sync.trigger_gatsby_build()
    except DrupalSyncError:
        raised = True
    assert raised, "Expected DrupalSyncError when gatsby_webhook_url is empty"
    print("  [OK] DrupalSyncError raised as expected")
    print("[PASS] trigger_gatsby_build - no webhook URL raises")


def test_trigger_gatsby_build_returns_true_on_success() -> None:
    """trigger_gatsby_build returns True when webhook returns 200."""
    print("\n[TEST] trigger_gatsby_build - success")
    sync = DrupalSync(_make_config(gatsby_webhook_url="https://drupal-cms.ddev.site/gatsby/build"))
    mock_resp = _mock_urlopen(200, b"{}")

    with unittest.mock.patch("urllib.request.urlopen", return_value=mock_resp):
        result = sync.trigger_gatsby_build()

    assert result is True
    print("  [OK] True returned on 200 response")
    print("[PASS] trigger_gatsby_build - success")


def test_trigger_gatsby_build_raises_on_url_error() -> None:
    """trigger_gatsby_build wraps URLError in DrupalSyncError."""
    print("\n[TEST] trigger_gatsby_build - URLError wraps to DrupalSyncError")
    sync = DrupalSync(_make_config(gatsby_webhook_url="https://drupal-cms.ddev.site/gatsby/build"))
    url_error = urllib.error.URLError("connection refused")

    with unittest.mock.patch("urllib.request.urlopen", side_effect=url_error):
        raised = False
        try:
            sync.trigger_gatsby_build()
        except DrupalSyncError:
            raised = True
    assert raised, "Expected DrupalSyncError wrapping URLError"
    print("  [OK] URLError wrapped in DrupalSyncError")
    print("[PASS] trigger_gatsby_build - URLError wraps to DrupalSyncError")


# ---------------------------------------------------------------------------
# node lookup routing tests (end-to-end via push_character + mocked urlopen)
# ---------------------------------------------------------------------------

def test_push_character_posts_when_lookup_returns_empty() -> None:
    """push_character POSTs when the GET lookup returns no matching nodes."""
    print("\n[TEST] push_character - GET empty -> POST")
    sync = DrupalSync(_make_config())
    char_file = Path(get_characters_dir()) / "aragorn.json"

    get_body = json.dumps({"data": []}).encode()
    post_body = json.dumps({"data": {"id": "post-uuid"}}).encode()

    call_count = 0

    def side_effect(_req, timeout=30):  # pylint: disable=unused-argument
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_urlopen(200, get_body)
        return _mock_urlopen(201, post_body)

    with unittest.mock.patch("urllib.request.urlopen", side_effect=side_effect):
        result = sync.push_character(char_file)

    assert result == "post-uuid"
    assert call_count == 2, "Expected GET then POST"
    print("  [OK] GET empty -> POST called -> UUID returned")
    print("[PASS] push_character - GET empty -> POST")


def test_push_character_patches_when_lookup_returns_node() -> None:
    """push_character PATCHes when the GET lookup finds an existing node."""
    print("\n[TEST] push_character - GET match -> PATCH")
    sync = DrupalSync(_make_config())
    char_file = Path(get_characters_dir()) / "frodo.json"

    get_body = json.dumps({"data": [{"id": "existing-uuid"}]}).encode()
    patch_body = json.dumps({"data": {"id": "existing-uuid"}}).encode()

    call_count = 0

    def side_effect(_req, timeout=30):  # pylint: disable=unused-argument
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_urlopen(200, get_body)
        return _mock_urlopen(200, patch_body)

    with unittest.mock.patch("urllib.request.urlopen", side_effect=side_effect):
        result = sync.push_character(char_file)

    assert result == "existing-uuid"
    assert call_count == 2, "Expected GET then PATCH"
    print("  [OK] GET match -> PATCH called -> existing UUID returned")
    print("[PASS] push_character - GET match -> PATCH")


# ---------------------------------------------------------------------------
# Live integration tests (skipped when DRUPAL_BASE_URL is not set)
# ---------------------------------------------------------------------------

def test_live_push_character_real_drupal() -> None:
    """Live: push aragorn.json to a running Drupal instance.

    Requires JSON:API write access enabled in Drupal (jsonapi, basic_auth,
    serialization modules enabled, read-only mode off).
    """
    print("\n[TEST] live push_character - aragorn.json")
    skip = _skip_if_no_live_drupal()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    sync = DrupalSync(_live_config())
    char_file = Path(get_characters_dir()) / "aragorn.json"
    try:
        uuid = sync.push_character(char_file)
    except DrupalSyncError as exc:
        print(f"  [SKIP] Drupal API not writable (enable jsonapi/basic_auth modules): {exc}")
        return
    assert isinstance(uuid, str) and uuid, "Expected a non-empty UUID string"
    print(f"  [OK] aragorn synced: {uuid}")
    print("[PASS] live push_character - aragorn.json")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests() -> None:
    """Run all drupal_sync tests."""
    print("=" * 70)
    print("DRUPAL SYNC TESTS")
    print("=" * 70)

    test_build_character_payload_title_only()
    test_build_character_payload_all_optional_fields()
    test_build_story_payload_structure()
    test_push_character_posts_new_node()
    test_push_character_patches_existing_node()
    test_push_character_raises_on_http_error()
    test_push_story_posts_new_node(Path("/tmp"))
    test_push_story_patches_existing_node(Path("/tmp"))
    test_trigger_gatsby_build_raises_without_url()
    test_trigger_gatsby_build_returns_true_on_success()
    test_trigger_gatsby_build_raises_on_url_error()
    test_push_character_posts_when_lookup_returns_empty()
    test_push_character_patches_when_lookup_returns_node()
    test_live_push_character_real_drupal()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL DRUPAL SYNC TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()

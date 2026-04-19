"""Drupal CMS sync utilities.

Provides delta push from the Python app to Drupal without re-running the full
Migrate API import.  Three public entry points cover the three most common
write operations: push a character profile, push a story file, and trigger
an incremental Gatsby rebuild via the Gatsby Preview webhook.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.config_types import DrupalConfig
from src.utils.file_io import load_json_file

logger = logging.getLogger(__name__)


class DrupalSyncError(Exception):
    """Raised when a Drupal API call fails."""


class DrupalSync:
    """Client for pushing content updates to Drupal via JSON:API.

    All write operations require the Drupal instance to have the ``jsonapi``
    and ``basic_auth`` modules enabled and the configured user to have the
    appropriate JSON:API write permissions.

    Args:
        config: Drupal integration configuration.
    """

    _JSONAPI_CONTENT_TYPE = "application/vnd.api+json"

    def __init__(self, config: DrupalConfig) -> None:
        self._config = config
        self._auth_header = self._build_auth_header()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push_character(self, character_file: Path) -> str:
        """Push a character JSON file to Drupal as a node.

        Looks up an existing character node by title and PATCHes it when
        found, otherwise POSTs a new one.

        Args:
            character_file: Path to a character JSON file in game_data/.

        Returns:
            The Drupal node UUID of the created or updated node.

        Raises:
            DrupalSyncError: On HTTP error or unexpected response shape.
        """
        raw = load_json_file(str(character_file))
        data: Dict[str, Any] = raw if raw is not None else {}
        title = data.get("name", character_file.stem)
        existing_uuid = self._find_node_uuid("character", title)
        payload: Dict[str, Any] = self._build_character_payload(data)

        if existing_uuid:
            self._patch_node("character", existing_uuid, payload)
            logger.info("Updated character '%s' (%s)", title, existing_uuid)
            return existing_uuid

        uuid = self._post_node("character", payload)
        logger.info("Created character '%s' (%s)", title, uuid)
        return uuid

    def push_story(self, story_file: Path, campaign: str) -> str:
        """Push a Markdown story file to Drupal as a story node.

        Args:
            story_file: Path to a ``.md`` story file.
            campaign: Campaign name used as the story title prefix.

        Returns:
            The Drupal node UUID of the created or updated node.

        Raises:
            DrupalSyncError: On HTTP error or unexpected response shape.
        """
        body = story_file.read_text(encoding="utf-8")
        title = f"{campaign} — {story_file.stem}"
        existing_uuid = self._find_node_uuid("story", title)
        payload = self._build_story_payload(title, body)

        if existing_uuid:
            self._patch_node("story", existing_uuid, payload)
            logger.info("Updated story '%s' (%s)", title, existing_uuid)
            return existing_uuid

        uuid = self._post_node("story", payload)
        logger.info("Created story '%s' (%s)", title, uuid)
        return uuid

    def trigger_gatsby_build(self) -> bool:
        """Fire the Gatsby Preview webhook to start an incremental rebuild.

        Returns:
            True if the webhook accepted the request (2xx response).

        Raises:
            DrupalSyncError: When no webhook URL is configured.
        """
        webhook_url = self._config.gatsby_webhook_url
        if not webhook_url:
            raise DrupalSyncError(
                "gatsby_webhook_url is not configured in DrupalConfig"
            )

        try:
            req = urllib.request.Request(
                webhook_url,
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                success = 200 <= resp.status < 300
                logger.info("Gatsby webhook %s -> %s", webhook_url, resp.status)
                return success
        except urllib.error.URLError as exc:
            raise DrupalSyncError(
                f"Gatsby webhook request failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_auth_header(self) -> str:
        """Return a Basic Auth header value from config credentials."""
        credentials = f"{self._config.user}:{self._config.password}"
        encoded = b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _api_url(self, *parts: str) -> str:
        """Build a JSON:API URL from path parts."""
        base = self._config.base_url.rstrip("/")
        path = "/".join(p.strip("/") for p in parts)
        return f"{base}/jsonapi/{path}"

    def _request(
        self,
        method: str,
        url: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an authenticated JSON:API request.

        Args:
            method: HTTP verb (GET, POST, PATCH).
            url: Full request URL.
            body: Optional request body (serialised to JSON).

        Returns:
            Parsed JSON response body.

        Raises:
            DrupalSyncError: On HTTP or decoding error.
        """
        data: Optional[bytes] = None
        headers: Dict[str, str] = {
            "Authorization": self._auth_header,
            "Accept": self._JSONAPI_CONTENT_TYPE,
        }
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = self._JSONAPI_CONTENT_TYPE

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                response_body = resp.read().decode()
                return json.loads(response_body) if response_body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise DrupalSyncError(
                f"{method} {url} returned {exc.code}: {detail[:200]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise DrupalSyncError(
                f"{method} {url} connection error: {exc.reason}"
            ) from exc

    def _find_node_uuid(self, node_type: str, title: str) -> Optional[str]:
        """Look up a node UUID by content type and title.

        Args:
            node_type: Drupal machine name of the content type.
            title: Node title to search for.

        Returns:
            UUID string if found, None otherwise.
        """
        encoded_title = urllib.parse.quote(title)
        url = self._api_url(
            "node", node_type
        ) + f"?filter[title]={encoded_title}&page[limit]=1"
        try:
            result = self._request("GET", url)
        except DrupalSyncError as exc:
            logger.warning("Node lookup failed: %s", exc)
            return None

        items = result.get("data", [])
        if items and isinstance(items, list):
            return str(items[0].get("id", ""))
        return None

    def _post_node(self, node_type: str, payload: Dict[str, Any]) -> str:
        """POST a new node and return its UUID.

        Args:
            node_type: Drupal machine name of the content type.
            payload: JSON:API resource object (without id).

        Returns:
            UUID of the newly created node.

        Raises:
            DrupalSyncError: On failure or unexpected response.
        """
        url = self._api_url("node", node_type)
        result = self._request("POST", url, payload)
        uuid = result.get("data", {}).get("id")
        if not uuid:
            raise DrupalSyncError(f"POST {node_type} returned no UUID: {result}")
        return str(uuid)

    def _patch_node(
        self, node_type: str, uuid: str, payload: Dict[str, Any]
    ) -> None:
        """PATCH an existing node.

        Args:
            node_type: Drupal machine name of the content type.
            uuid: UUID of the existing node.
            payload: JSON:API resource object (must include id).
        """
        payload.setdefault("data", {})["id"] = uuid
        url = self._api_url("node", node_type, uuid)
        self._request("PATCH", url, payload)

    @staticmethod
    def _build_character_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a character dict to a JSON:API POST/PATCH payload.

        Args:
            data: Raw character profile dict from game_data/characters/*.json.

        Returns:
            JSON:API resource object suitable for node/character.
        """
        attrs: Dict[str, Any] = {
            "title": data.get("name", ""),
        }
        if "backstory" in data:
            attrs["field_backstory"] = [
                {"value": data["backstory"], "format": "plain_text"}
            ]
        if "personality_traits" in data:
            attrs["field_personality_traits"] = [
                {"value": t} for t in (
                    data["personality_traits"]
                    if isinstance(data["personality_traits"], list)
                    else [data["personality_traits"]]
                )
            ]
        if "bonds" in data:
            attrs["field_bonds"] = [
                {"value": b} for b in (
                    data["bonds"]
                    if isinstance(data["bonds"], list)
                    else [data["bonds"]]
                )
            ]
        if "ideals" in data:
            attrs["field_ideals"] = [
                {"value": i} for i in (
                    data["ideals"]
                    if isinstance(data["ideals"], list)
                    else [data["ideals"]]
                )
            ]
        if "flaws" in data:
            attrs["field_flaws"] = [
                {"value": f} for f in (
                    data["flaws"]
                    if isinstance(data["flaws"], list)
                    else [data["flaws"]]
                )
            ]
        return {
            "data": {
                "type": "node--character",
                "attributes": attrs,
            }
        }

    @staticmethod
    def _build_story_payload(title: str, body: str) -> Dict[str, Any]:
        """Convert a story Markdown body to a JSON:API POST/PATCH payload.

        Args:
            title: Node title (campaign + filename).
            body: Full Markdown content of the story file.

        Returns:
            JSON:API resource object suitable for node/story.
        """
        return {
            "data": {
                "type": "node--story",
                "attributes": {
                    "title": title,
                    "body": {"value": body, "format": "plain_text"},
                },
            }
        }

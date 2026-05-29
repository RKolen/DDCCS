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
        return self._upsert_node("character", str(title), self.build_character_payload(data))

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
        return self._upsert_node("story", title, self.build_story_payload(title, body))

    def push_item(self, item_data: Dict[str, Any], skip_existing: bool = True) -> str:
        """Push a single parsed FGU item to Drupal as a node--item node.

        By default, existing nodes are left untouched (skip_existing=True) so
        that manually-curated Drupal items are never overwritten by the import.

        Args:
            item_data: Normalized item dict from FguXmlParser.iter_items().
            skip_existing: When True (default), return the existing UUID without
                updating if a node with the same title already exists.

        Returns:
            The Drupal node UUID of the created or found node.

        Raises:
            DrupalSyncError: On HTTP error or unexpected response shape.
        """
        title = str(item_data.get("name", ""))
        return self._upsert_node(
            "item", title, self.build_item_payload(item_data), skip_existing=skip_existing
        )

    def push_monster(self, monster_data: Dict[str, Any], skip_existing: bool = True) -> str:
        """Push a single parsed FGU npc stat block to Drupal as a node--monster node.

        By default, existing nodes are left untouched (skip_existing=True) so
        that manually-curated Drupal monsters are never overwritten by the import.

        Args:
            monster_data: Normalized monster dict from FguXmlParser.iter_monsters().
            skip_existing: When True (default), return the existing UUID without
                updating if a node with the same title already exists.

        Returns:
            The Drupal node UUID of the created or found node.

        Raises:
            DrupalSyncError: On HTTP error or unexpected response shape.
        """
        title = str(monster_data.get("name", ""))
        return self._upsert_node(
            "monster", title, self.build_monster_payload(monster_data), skip_existing=skip_existing
        )

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

    def _upsert_node(
        self,
        node_type: str,
        title: str,
        payload: Dict[str, Any],
        skip_existing: bool = False,
    ) -> str:
        """Create or update a Drupal node, returning its UUID.

        Looks up an existing node by content type and title.  When
        ``skip_existing`` is True and a match is found, returns the existing
        UUID without modifying the node.  Otherwise PATCHes the existing node.
        POSTs a new node when none is found.

        Args:
            node_type: Drupal machine name of the content type.
            title: Node title used for the duplicate lookup.
            payload: JSON:API resource object body.
            skip_existing: When True, never overwrite an existing node.

        Returns:
            UUID of the created, updated, or found node.

        Raises:
            DrupalSyncError: On HTTP error or unexpected response shape.
        """
        existing_uuid = self._find_node_uuid(node_type, title)
        if existing_uuid:
            if skip_existing:
                logger.info("Skipped %s '%s' (manual version kept)", node_type, title)
                return existing_uuid
            self._patch_node(node_type, existing_uuid, payload)
            logger.info("Updated %s '%s' (%s)", node_type, title, existing_uuid)
            return existing_uuid
        uuid = self._post_node(node_type, payload)
        logger.info("Created %s '%s' (%s)", node_type, title, uuid)
        return uuid

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
    def build_character_payload(data: Dict[str, Any]) -> Dict[str, Any]:
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
    def build_story_payload(title: str, body: str) -> Dict[str, Any]:
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

    @staticmethod
    def build_item_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a normalized FGU item dict to a JSON:API POST/PATCH payload.

        Rarity values already contain the Drupal slug (common/uncommon/rare/
        very_rare/legendary/artifact/vestige) as produced by FguXmlParser.
        Magic flag is derived from rarity: anything uncommon or above is magic.

        Args:
            data: Normalized item dict from FguXmlParser.iter_items().

        Returns:
            JSON:API resource object suitable for node--item.
        """
        magic_rarities = {"uncommon", "rare", "very_rare", "legendary", "artifact", "vestige"}
        rarity = str(data.get("rarity", ""))
        notes = str(data.get("description_text", ""))
        restriction = str(data.get("attunement_restriction", ""))
        if restriction:
            notes = f"{notes}\n\nAttunement restriction: {restriction}".strip()

        attrs: Dict[str, Any] = {
            "title": str(data.get("name", "")),
            "field_item_type": str(data.get("item_type", "item")),
            "field_is_magic": rarity in magic_rarities,
            "field_item_rarity": rarity,
            "field_item_requires_attunement": bool(data.get("attunement", False)),
            "field_notes": notes,
            "field_item_cost": str(data.get("cost", "")),
            "field_item_weight": data.get("weight", 0.0),
            "field_item_bonus": data.get("bonus", 0),
            "field_nonidentified_name": str(data.get("nonid_name", "")),
            "field_edition": str(data.get("version", "")),
        }

        if data.get("damage"):
            attrs["field_damage"] = str(data["damage"])
        if data.get("mastery"):
            attrs["field_weapon_mastery"] = str(data["mastery"])
        if data.get("properties"):
            attrs["field_weapon_properties"] = str(data["properties"])
        if data.get("subtype"):
            attrs["field_weapon_subtype"] = str(data["subtype"])
        if data.get("ac") is not None:
            attrs["field_armor_ac_base"] = int(data["ac"])
        if data.get("str_requirement") is not None:
            attrs["field_armor_str_requirement"] = int(data["str_requirement"])

        return {"data": {"type": "node--item", "attributes": attrs}}

    @staticmethod
    def build_monster_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a normalized FGU npc dict to a JSON:API POST/PATCH payload.

        Maps FGU <npc> stat blocks to node--monster.  Does NOT touch node--npc,
        which is reserved for CLI-sourced narrative NPC profiles.

        The field_ability_scores paragraph and field_type taxonomy reference
        are skipped in the Python push path (handled by the Migrate API bulk
        import instead).

        Args:
            data: Normalized monster dict from FguXmlParser.iter_monsters().

        Returns:
            JSON:API resource object suitable for node--monster.
        """
        speed_numeric = data.get("speed_numeric")
        attrs: Dict[str, Any] = {
            "title": str(data.get("name", "")),
            "field_challenge_rating": data.get("cr", 0.0),
            "field_armor_class": data.get("ac", 0),
            "field_maximum_hitpoints": data.get("hp", 0),
            "field_movement_speed": speed_numeric if speed_numeric is not None else 0,
            "field_monster_speed": str(data.get("speed", "")),
            "field_monster_size": str(data.get("size", "")),
            "field_monster_alignment": str(data.get("alignment", "")),
            "field_monster_senses": str(data.get("senses", "")),
            "field_monster_languages": str(data.get("languages", "")),
            "field_monster_skills": str(data.get("skills", "")),
            "field_monster_hit_dice": str(data.get("hit_dice", "")),
            "field_monster_xp": data.get("xp", 0),
            "field_specialized_abilities": str(data.get("traits_text", "")),
            "field_monster_actions": str(data.get("actions_text", "")),
            "field_monster_bonus_actions": str(data.get("bonus_actions_text", "")),
            "field_monster_reactions": str(data.get("reactions_text", "")),
            "field_monster_legendary_actions": str(data.get("legendary_actions_text", "")),
            "field_monster_lair_actions": str(data.get("lair_actions_text", "")),
            "field_monster_damage_immunities": str(data.get("damage_immunities", "")),
            "field_monster_damage_resistances": str(data.get("damage_resistances", "")),
        }
        return {"data": {"type": "node--monster", "attributes": attrs}}

    # ------------------------------------------------------------------
    # Wiki cache helpers (used by DrupalWikiCache in src/ai/rag_system.py)
    # ------------------------------------------------------------------

    def get_wiki_page_cache(self, url_hash: str) -> Optional[Dict[str, Any]]:
        """Fetch a cached wiki page by its URL hash.

        Args:
            url_hash: MD5 hash of the original URL (used as node title).

        Returns:
            Dict with field values or None if not found.

        Raises:
            DrupalSyncError: On HTTP or decoding error.
        """
        encoded = urllib.parse.quote(url_hash)
        fields = "title,field_wiki_url,field_wiki_fetched_at,field_wiki_content"
        url = (
            self._api_url("node", "wiki_cache")
            + f"?filter[title]={encoded}&page[limit]=1&fields[node--wiki_cache]={fields}"
        )
        try:
            result = self._request("GET", url)
        except DrupalSyncError as exc:
            logger.debug("Wiki cache lookup failed: %s", exc)
            return None
        items = result.get("data", [])
        if not items or not isinstance(items, list):
            return None
        attrs = items[0].get("attributes", {})
        return {
            "field_wiki_url": attrs.get("field_wiki_url", ""),
            "field_wiki_fetched_at": attrs.get("field_wiki_fetched_at", 0),
            "field_wiki_content": attrs.get("field_wiki_content", ""),
        }

    def set_wiki_page_cache(
        self,
        url_hash: str,
        url: str,
        fetched_at: float,
        content_json: str,
    ) -> str:
        """Upsert a wiki page cache entry in Drupal.

        Args:
            url_hash: MD5 hash of the URL (used as node title for keying).
            url: Original page URL.
            fetched_at: Unix timestamp of when the page was fetched.
            content_json: Serialized JSON of page sections.

        Returns:
            UUID of the created or updated node.

        Raises:
            DrupalSyncError: On HTTP error or unexpected response shape.
        """
        payload = {
            "data": {
                "type": "node--wiki_cache",
                "attributes": {
                    "title": url_hash,
                    "field_wiki_url": url,
                    "field_wiki_fetched_at": str(fetched_at),
                    "field_wiki_content": {
                        "value": content_json,
                        "format": "plain_text",
                    },
                },
            }
        }
        return self._upsert_node("wiki_cache", url_hash, payload)

    def delete_wiki_page_cache(self, url_hash: str) -> None:
        """Delete a wiki page cache entry by its URL hash.

        Args:
            url_hash: MD5 hash of the URL (used as node title).

        Raises:
            DrupalSyncError: On HTTP error.
        """
        existing_uuid = self._find_node_uuid("wiki_cache", url_hash)
        if not existing_uuid:
            return
        delete_url = self._api_url("node", "wiki_cache", existing_uuid)
        self._request("DELETE", delete_url)

    def count_wiki_page_cache(self) -> int:
        """Return the number of wiki_cache nodes in Drupal.

        Returns:
            Total count of wiki cache entries.

        Raises:
            DrupalSyncError: On HTTP error.
        """
        url = self._api_url("node", "wiki_cache") + "?page[limit]=1"
        result = self._request("GET", url)
        meta = result.get("meta", {})
        try:
            return int(meta.get("count", 0))
        except (TypeError, ValueError):
            return 0

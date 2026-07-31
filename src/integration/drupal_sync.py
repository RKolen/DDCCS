"""Drupal wiki cache client.

Backs :class:`src.ai.rag_system.DrupalWikiCache`: stores fetched wiki pages as
``wiki_cache`` nodes in Drupal so the CMS owns the cache and it survives
restarts.

All access goes through the GraphQL endpoint. The project standardises on
GraphQL for Drupal access; JSON:API is disabled server-side
(``jsonapi_extras.settings`` sets ``default_disabled: true``), so any JSON:API
call returns 404.

The ``wikiCacheEntry`` / ``wikiCacheCount`` queries and the
``setWikiCacheEntry`` / ``deleteWikiCacheEntry`` mutations are provided by the
``dnd_content`` Drupal module. They are hand-written resolvers rather than
graphql_compose exposure, so Gatsby never sources these nodes.
"""

import logging
from typing import Any, Dict, Optional

from src.config.config_types import DrupalConfig
from src.integration.drupal_graphql import (
    DrupalGraphQLError,
    mutate_drupal,
    query_drupal,
)

logger = logging.getLogger(__name__)

_ENTRY_FIELDS = "url fetchedAt content"

_GET_QUERY = f"""
query WikiCacheEntry($urlHash: String!) {{
  wikiCacheEntry(urlHash: $urlHash) {{ {_ENTRY_FIELDS} }}
}}
"""

_COUNT_QUERY = """
query WikiCacheCount {
  wikiCacheCount
}
"""

_SET_MUTATION = f"""
mutation SetWikiCacheEntry(
  $urlHash: String!
  $url: String!
  $fetchedAt: Float!
  $content: String!
) {{
  setWikiCacheEntry(
    urlHash: $urlHash
    url: $url
    fetchedAt: $fetchedAt
    content: $content
  ) {{ {_ENTRY_FIELDS} }}
}}
"""

_DELETE_MUTATION = """
mutation DeleteWikiCacheEntry($urlHash: String!) {
  deleteWikiCacheEntry(urlHash: $urlHash)
}
"""


class DrupalSyncError(Exception):
    """Raised when a Drupal wiki cache call fails."""


class DrupalSync:
    """Client for the Drupal-backed wiki page cache.

    Args:
        config: Drupal integration configuration. Passed through to every
            GraphQL call, so the connection this client was built with is the
            one actually used.
    """

    def __init__(self, config: DrupalConfig) -> None:
        self._config = config

    @property
    def config(self) -> DrupalConfig:
        """Return the Drupal configuration this client was built with."""
        return self._config

    def get_wiki_page_cache(self, url_hash: str) -> Optional[Dict[str, Any]]:
        """Fetch a cached wiki page by its URL hash.

        A miss and an unreachable Drupal are both reported as None: the caller's
        only sensible response either way is to re-fetch the page.

        Args:
            url_hash: MD5 hash of the original URL (used as the node title).

        Returns:
            Dict with ``field_wiki_url``, ``field_wiki_fetched_at`` and
            ``field_wiki_content`` keys, or None when nothing is cached.
        """
        data = query_drupal(_GET_QUERY, {"urlHash": url_hash}, self._config)
        entry = data.get("wikiCacheEntry")
        if not isinstance(entry, dict):
            return None
        return {
            "field_wiki_url": entry.get("url", ""),
            "field_wiki_fetched_at": entry.get("fetchedAt", 0),
            "field_wiki_content": entry.get("content", ""),
        }

    def set_wiki_page_cache(
        self,
        url_hash: str,
        url: str,
        fetched_at: float,
        content_json: str,
    ) -> str:
        """Create or replace a wiki page cache entry in Drupal.

        Args:
            url_hash: MD5 hash of the URL (used as the node title for keying).
            url: Original page URL.
            fetched_at: Unix timestamp of when the page was fetched.
            content_json: Serialized JSON of the page sections.

        Returns:
            The stored page URL, echoing what Drupal persisted.

        Raises:
            DrupalSyncError: On transport failure or a GraphQL error.
        """
        variables: Dict[str, Any] = {
            "urlHash": url_hash,
            "url": url,
            "fetchedAt": float(fetched_at),
            "content": content_json,
        }
        try:
            data = mutate_drupal(_SET_MUTATION, variables, self._config)
        except DrupalGraphQLError as exc:
            raise DrupalSyncError(f"Wiki cache write failed: {exc}") from exc

        entry = data.get("setWikiCacheEntry")
        if not isinstance(entry, dict):
            raise DrupalSyncError(f"setWikiCacheEntry returned no entry: {data}")
        return str(entry.get("url", ""))

    def delete_wiki_page_cache(self, url_hash: str) -> None:
        """Delete a wiki page cache entry by its URL hash.

        Deleting an entry that is not cached is a success: the caller wanted the
        cache not to hold that URL, and it does not.

        Args:
            url_hash: MD5 hash of the URL (used as the node title).

        Raises:
            DrupalSyncError: On transport failure, a GraphQL error, or when
                Drupal refuses the delete.
        """
        try:
            data = mutate_drupal(_DELETE_MUTATION, {"urlHash": url_hash}, self._config)
        except DrupalGraphQLError as exc:
            raise DrupalSyncError(f"Wiki cache delete failed: {exc}") from exc

        if data.get("deleteWikiCacheEntry") is not True:
            raise DrupalSyncError(
                f"Drupal refused to delete wiki cache entry '{url_hash}'"
            )

    def count_wiki_page_cache(self) -> int:
        """Return the number of wiki_cache nodes in Drupal.

        Returns:
            Total count of wiki cache entries, or 0 when Drupal is unreachable.
        """
        data = query_drupal(_COUNT_QUERY, None, self._config)
        try:
            return int(data.get("wikiCacheCount", 0))
        except (TypeError, ValueError):
            return 0

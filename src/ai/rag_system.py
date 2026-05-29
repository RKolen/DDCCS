"""
RAG (Retrieval-Augmented Generation) System for D&D Campaign Wikis

Provides wiki integration to enhance AI-generated stories with accurate
campaign setting lore, locations, and history.
"""

import functools
import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, FrozenSet, List, Optional, Set
from urllib.parse import quote

from src.utils.errors import DnDError, display_error
from src.config.config_loader import load_config
from src.items.item_registry import ItemRegistry
from src.integration.drupal_sync import DrupalSync, DrupalSyncError

logger = logging.getLogger(__name__)

_NPC_MATCH_FIRST_WORDS: int = 8
_NPC_MATCH_MIN_WORD_LEN: int = 5
_RULES_CONTEXT_BUDGET: int = 1500
_RULES_ENTITY_LIMIT: int = 10
_RULES_STOP_WORDS: FrozenSet[str] = frozenset({
    "A", "An", "And", "Are", "As", "At", "Be", "But", "By", "Could",
    "For", "From", "Has", "Had", "Have", "Her", "His", "How", "In", "Is",
    "Its", "May", "Might", "My", "Of", "On", "Or", "Our", "Should", "That",
    "The", "Their", "These", "This", "Those", "To", "Was", "Were", "What",
    "When", "Where", "Which", "Who", "Will", "With", "Would", "Your",
})

try:
    from src.ai.semantic_retriever import SemanticRetriever
    SEMANTIC_RETRIEVER_AVAILABLE = True
except ImportError:
    SEMANTIC_RETRIEVER_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup

    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    logger.warning(
        "RAG System: requests or beautifulsoup4 not installed. "
        "Install with: pip install requests beautifulsoup4"
    )


class DrupalWikiCache:
    """Drupal-backed cache for external wiki page data.

    Stores fetched wiki pages as wiki_cache nodes in Drupal so the CMS
    remains the single source of truth for all content. All operations
    degrade gracefully when Drupal is unreachable or not configured.
    """

    def __init__(
        self,
        drupal_sync: Optional[DrupalSync],
        ttl_seconds: int = 604800,
    ):
        """
        Args:
            drupal_sync: DrupalSync instance for JSON:API calls, or None to disable caching.
            ttl_seconds: Time-to-live in seconds (default: 7 days).
        """
        self._sync = drupal_sync
        self.ttl_seconds = ttl_seconds

    def _cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Return cached content for url, or None if missing, expired, or unavailable."""
        if self._sync is None:
            return None
        cache_key = self._cache_key(url)
        try:
            page_data = self._sync.get_wiki_page_cache(cache_key)
        except DrupalSyncError as exc:
            logger.debug("Drupal cache get failed: %s", exc)
            page_data = None
        if not page_data:
            return None
        try:
            fetched_at = float(page_data.get("field_wiki_fetched_at") or 0)
        except (TypeError, ValueError):
            fetched_at = 0.0
        if time.time() - fetched_at > self.ttl_seconds:
            self.delete(url)
            return None
        raw_content = page_data.get("field_wiki_content", "")
        if isinstance(raw_content, dict):
            raw_content = raw_content.get("value", "")
        if raw_content:
            try:
                return json.loads(str(raw_content))
            except (json.JSONDecodeError, ValueError):
                self.delete(url)
        return None

    def set(self, url: str, content: Dict[str, Any]) -> None:
        """Store content for url."""
        if self._sync is None:
            return
        cache_key = self._cache_key(url)
        try:
            self._sync.set_wiki_page_cache(
                url_hash=cache_key,
                url=url,
                fetched_at=time.time(),
                content_json=json.dumps(content),
            )
        except DrupalSyncError as exc:
            logger.warning("Drupal cache set failed for %r: %s", url, exc)

    def delete(self, url: str) -> None:
        """Delete cached content for url."""
        if self._sync is None:
            return
        cache_key = self._cache_key(url)
        try:
            self._sync.delete_wiki_page_cache(cache_key)
        except DrupalSyncError as exc:
            logger.debug("Drupal cache delete failed: %s", exc)

    def clear_expired(self) -> None:
        """TTL expiry is enforced per-entry in get(). No bulk operation needed."""
        logger.debug("clear_expired: TTL checked per-entry on read via Drupal JSON:API")

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        if self._sync is None:
            return {"entries": 0, "backend": "drupal (not configured)"}
        try:
            count = self._sync.count_wiki_page_cache()
        except DrupalSyncError as exc:
            logger.debug("Drupal cache stats failed: %s", exc)
            count = 0
        return {"entries": count, "backend": "drupal"}


class WikiClient:
    """Fetches and parses wiki pages with caching and optional homebrew item filtering."""

    def __init__(
        self, base_url: str, cache: Optional[DrupalWikiCache] = None, item_registry=None
    ):
        """
        Args:
            base_url: Base URL of the wiki (configured via RAG_WIKI_BASE_URL env var).
            cache: DrupalWikiCache instance (creates unconfigured cache if not provided).
            item_registry: ItemRegistry for homebrew filtering (optional).
        """
        self.base_url = base_url.rstrip("/")
        self.cache = cache or DrupalWikiCache(drupal_sync=None)
        self.item_registry = item_registry
        self.session = requests.Session() if SCRAPING_AVAILABLE else None
        if self.session:
            self.session.headers.update({"User-Agent": "DnD-Character-Consultant/1.0"})

    def _clean_wiki_text(self, text: str) -> str:
        """Remove references, edit links, and excessive whitespace."""
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\[edit\]", "", text)
        text = re.sub(r"\n\n+", "\n\n", text)
        return text.strip()

    def _extract_elem_content(self, elem) -> str:
        """Extract plain text from a p, ul, table, or aside element."""
        if elem.name == "p":
            return elem.get_text(strip=True)
        if elem.name == "ul":
            items = [li.get_text(strip=True) for li in elem.find_all("li")]
            return "\n".join(f"- {item}" for item in items) if items else ""
        if elem.name == "table":
            rows = []
            for row in elem.find_all("tr"):
                cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                if cells:
                    rows.append(" | ".join(cells))
            return "\n".join(rows) if rows else ""
        if elem.name == "aside":
            if "portable-infobox" not in (elem.get("class") or []):
                return ""
            labels = elem.find_all(class_="pi-data-label")
            values = elem.find_all(class_="pi-data-value")
            items = [
                f"{lbl.get_text(strip=True)}: {val.get_text(strip=True)}"
                for lbl, val in zip(labels, values)
            ]
            return "\n".join(items) if items else ""
        return ""

    def _parse_sections(self, content_elem) -> List[Dict[str, str]]:
        """Parse sections from wiki content element."""
        sections = []
        current_section: Dict[str, str] = {"title": "Introduction", "content": ""}
        for elem in content_elem.find_all(["h2", "h3", "p", "ul", "table", "aside"]):
            if elem.name in ("h2", "h3"):
                if current_section["content"]:
                    current_section["content"] = self._clean_wiki_text(
                        current_section["content"]
                    )
                    sections.append(current_section)
                section_title = re.sub(r"\[edit\]", "", elem.get_text(strip=True)).strip()
                current_section = {"title": section_title, "content": ""}
            else:
                content = self._extract_elem_content(elem)
                if content:
                    current_section["content"] += content + "\n\n"
        if current_section["content"]:
            current_section["content"] = self._clean_wiki_text(current_section["content"])
            sections.append(current_section)
        return sections

    def fetch_page(
        self, page_title: str, force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Fetch and cache a wiki page by title.

        Args:
            page_title: Title of the wiki page.
            force_refresh: Bypass cache and fetch fresh content.

        Returns:
            Dict with page content or None if fetch failed.
        """
        if not SCRAPING_AVAILABLE or self.session is None:
            logger.warning(
                "Cannot fetch wiki pages: requests/beautifulsoup4 not installed"
            )
            return None
        if self.item_registry and self.item_registry.is_custom(page_title):
            logger.debug("Blocked custom item lookup: %s (in custom registry)", page_title)
            return None
        page_url = f"{self.base_url}/{quote(page_title.replace(' ', '_'))}"
        if not force_refresh:
            cached = self.cache.get(page_url)
            if cached:
                logger.debug("Cache hit: %s", page_title)
                return cached
        page_data = None
        try:
            logger.debug("Fetching: %s", page_title)
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            title_elem = soup.find("h1", class_="page-header__title")
            if not title_elem:
                title_elem = soup.find("h1", id="firstHeading")
            title = title_elem.get_text(strip=True) if title_elem else page_title
            content_elem = soup.find("div", class_="mw-parser-output")
            if not content_elem:
                content_elem = soup.find("div", id="mw-content-text")
            if content_elem:
                sections = self._parse_sections(content_elem)
                page_data = {
                    "title": title,
                    "url": page_url,
                    "sections": sections,
                    "fetched_at": time.time(),
                }
                self.cache.set(page_url, page_data)
                logger.debug("Fetched: %s (%d sections)", title, len(sections))
            else:
                logger.warning("Could not find content for %s", page_title)
        except requests.RequestException as e:
            display_error(DnDError(
                message=f"Failed to fetch {page_title}: {e}",
                user_guidance="Check your internet connection and the wiki URL configuration."
            ))
        except (ValueError, AttributeError) as e:
            display_error(DnDError(
                message=f"Error parsing {page_title}: {e}",
                user_guidance="The wiki page format may have changed."
            ))
        return page_data

    def search_sections(
        self, page_data: Dict, query: str, max_results: int = 3
    ) -> List[Dict]:
        """
        Search for relevant sections within a page.

        Args:
            page_data: Page data from fetch_page().
            query: Search query.
            max_results: Maximum number of sections to return.

        Returns:
            List of relevant sections with relevance scores.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        results = []
        for section in page_data["sections"]:
            title = section["title"].lower()
            content = section["content"].lower()
            score = 0.0
            if query_lower in title:
                score += 2.0
            score += len(query_words & set(title.split())) * 0.5
            score += len(query_words & set(content.split())) * 0.1
            if score > 0:
                results.append({"section": section, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]


class RAGSystem:
    """
    Main RAG system for integrating wiki knowledge with AI generation.

    IMPORTANT: Homebrew content is NEVER looked up on external wikis.
    Use ItemRegistry to mark homebrew items/rules.
    """

    @staticmethod
    def _get_runtime_settings() -> Dict[str, Any]:
        """Load RAG settings from centralized config, with env fallback."""
        try:
            loaded_config = load_config()
            return {
                "enabled": loaded_config.rag.enabled,
                "wiki_base_url": loaded_config.rag.wiki_base_url,
                "rules_base_url": loaded_config.rag.rules_base_url,
                "cache_ttl": loaded_config.rag.cache_ttl,
            }
        except (ImportError, OSError, ValueError):
            try:
                cache_ttl = int(os.getenv("RAG_CACHE_TTL", "604800"))
            except ValueError:
                cache_ttl = 604800
            return {
                "enabled": os.getenv("RAG_ENABLED", "false").lower() == "true",
                "wiki_base_url": os.getenv("RAG_WIKI_BASE_URL", ""),
                "rules_base_url": os.getenv("RAG_RULES_BASE_URL", ""),
                "cache_ttl": cache_ttl,
            }

    @staticmethod
    def _build_cache(cache_ttl: int) -> DrupalWikiCache:
        """Create a Drupal-backed wiki cache; falls back to unconfigured cache."""
        try:
            drupal_config = load_config().drupal
            if drupal_config.base_url:
                return DrupalWikiCache(
                    drupal_sync=DrupalSync(drupal_config),
                    ttl_seconds=cache_ttl,
                )
        except (OSError, ValueError, AttributeError) as exc:
            logger.debug("Drupal wiki cache init skipped: %s", exc)
        return DrupalWikiCache(drupal_sync=None, ttl_seconds=cache_ttl)

    def __init__(self, item_registry=None, rag_config=None):
        """
        Initialize RAG system from configuration.

        Args:
            item_registry: Optional ItemRegistry instance for homebrew filtering.
            rag_config: Optional RAGConfig object from src.config (takes precedence).
        """
        runtime_settings = self._get_runtime_settings()

        if rag_config is not None:
            self.enabled = rag_config.enabled
            self.wiki_base_url = rag_config.wiki_base_url
            self.rules_base_url = rag_config.rules_base_url
            cache_ttl = rag_config.cache_ttl
        else:
            self.enabled = runtime_settings["enabled"]
            self.wiki_base_url = runtime_settings["wiki_base_url"]
            self.rules_base_url = runtime_settings["rules_base_url"]
            cache_ttl = int(runtime_settings["cache_ttl"])

        self.item_registry = item_registry
        if self.item_registry is None and ItemRegistry is not None:
            self.item_registry = ItemRegistry()

        if not self.enabled:
            self.client = None
            self.rules_client = None
            return

        if not SCRAPING_AVAILABLE:
            logger.warning(
                "RAG enabled but dependencies not installed. "
                "Install with: pip install requests beautifulsoup4"
            )
            self.client = None
            self.rules_client = None
            return

        cache = self._build_cache(cache_ttl=cache_ttl)

        if self.wiki_base_url:
            self.client = WikiClient(self.wiki_base_url, cache, self.item_registry)
            logger.debug("RAG Lore Wiki initialized: %s", self.wiki_base_url)
        else:
            self.client = None
            logger.warning("RAG_WIKI_BASE_URL not set - lore lookups disabled")

        if self.rules_base_url:
            self.rules_client = WikiClient(
                self.rules_base_url, cache, self.item_registry
            )
            logger.debug("RAG Rules Wiki initialized: %s", self.rules_base_url)
        else:
            self.rules_client = None
            logger.warning("RAG_RULES_BASE_URL not set - item/spell lookups disabled")

        if self.item_registry:
            custom_count = len(self.item_registry.get_all_custom_items())
            logger.debug(
                "Custom item filter: %d items - will NOT lookup on external wikis", custom_count
            )

    def get_relevant_context(self, prompt: str, campaign_name: str) -> str:
        """Return semantically relevant lore context via Milvus when available.

        Args:
            prompt: Current AI prompt text.
            campaign_name: Active campaign name for story-chunk scoping.

        Returns:
            Formatted context string, or empty string when Milvus is unavailable.
        """
        if not SEMANTIC_RETRIEVER_AVAILABLE:
            return ""
        retriever = SemanticRetriever()
        if not retriever.is_available():
            return ""
        lore_chunks = retriever.get_relevant_lore(prompt)
        story_chunks = retriever.get_relevant_story_context(prompt, campaign_name)
        parts: List[str] = []
        if lore_chunks:
            parts.append("=== SEMANTIC LORE CONTEXT ===")
            for chunk in lore_chunks:
                parts.append(chunk.get("chunk_text", ""))
            parts.append("=== END LORE CONTEXT ===")
        if story_chunks:
            parts.append("=== RELEVANT STORY CONTEXT ===")
            for chunk in story_chunks:
                parts.append(chunk.get("chunk_text", ""))
            parts.append("=== END STORY CONTEXT ===")
        return "\n\n".join(parts) if parts else ""

    def get_context_for_location(
        self, location_name: str, max_sections: int = 2
    ) -> str:
        """Return wiki context for a location.

        Args:
            location_name: Name of the location.
            max_sections: Maximum sections to include.

        Returns:
            Formatted context string to add to AI prompt.
        """
        if not self.enabled or not self.client:
            return ""
        page_data = self.client.fetch_page(location_name)
        if not page_data:
            return ""
        sections = page_data["sections"][:max_sections]
        context = f"\n\n=== LORE CONTEXT: {page_data['title']} ===\n"
        for section in sections:
            context += f"\n{section['title']}:\n{section['content']}\n"
        context += "=== END LORE CONTEXT ===\n\n"
        return context

    def get_context_for_query(
        self, query: str, pages_to_search: List[str], max_results: int = 3
    ) -> str:
        """Search multiple pages for relevant context.

        Args:
            query: What to search for.
            pages_to_search: List of page titles to search.
            max_results: Maximum results per page.

        Returns:
            Formatted context string.
        """
        if not self.enabled or not self.client:
            return ""
        context = f"\n\n=== LORE CONTEXT FOR: {query} ===\n"
        for page_title in pages_to_search:
            page_data = self.client.fetch_page(page_title)
            if not page_data:
                continue
            results = self.client.search_sections(page_data, query, max_results)
            if results:
                context += f"\nFrom {page_data['title']}:\n"
                for result in results:
                    section = result["section"]
                    context += f"\n{section['title']}:\n{section['content']}\n"
        context += "\n=== END LORE CONTEXT ===\n\n"
        return context

    def get_history_check_info(self, topic: str, dc_result: int) -> Optional[str]:
        """Return wiki information for a successful History check.

        Args:
            topic: What the character is trying to recall.
            dc_result: The check result (determines detail level).

        Returns:
            Information the character recalls, or None if check failed.
        """
        if not self.enabled or not self.client:
            return None
        page_data = self.client.fetch_page(topic)
        if not page_data:
            return None
        if dc_result < 10:
            sections = page_data["sections"][:1]
        elif dc_result < 15:
            sections = page_data["sections"][:2]
        elif dc_result < 20:
            sections = page_data["sections"][:3]
        else:
            sections = page_data["sections"]
        info = f"You recall the following about {page_data['title']}:\n\n"
        for section in sections:
            info += f"{section['title']}:\n{section['content']}\n\n"
        return info

    def fetch_item_info(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Fetch information about an item, respecting custom/homebrew filtering.

        Custom items are returned from the local registry; official items are
        looked up on the D&D 5e rules wiki.

        Args:
            item_name: Name of the item to lookup.

        Returns:
            Dict with item info or None if not found.
        """
        if not self.enabled or not self.rules_client:
            return None
        if self.item_registry:
            item = self.item_registry.get_item(item_name)
            if item:
                return {
                    "name": item.name,
                    "description": item.description,
                    "properties": item.properties,
                    "is_custom": True,
                    "is_magic": item.is_magic,
                    "source": "custom_registry",
                    "notes": item.notes,
                }
        page_data = self.rules_client.fetch_page(item_name)
        if not page_data:
            return None
        description = ""
        properties = {}
        for section in page_data.get("sections", []):
            title = section.get("title", "")
            content = section.get("content", "")
            if title.lower() in ["description", "overview", "summary"]:
                description = content
            else:
                properties[title] = content
        return {
            "name": page_data.get("title", item_name),
            "description": description,
            "properties": properties,
            "is_custom": False,
            "source": "rules_wiki",
            "url": page_data.get("url", ""),
        }

    def get_major_npc_context_for_prompt(
        self,
        prompt: str,
        major_npc_statuses: List[Dict[str, Any]],
        max_npcs: int = 2,
    ) -> str:
        """Return backstory and plot context for major NPCs relevant to a prompt.

        Keyword-matches NPC names, roles, and relationships against the prompt.

        Args:
            prompt: Current story or AI prompt text.
            major_npc_statuses: List of status dicts from NPCAgent.get_status().
            max_npcs: Maximum number of NPCs to include in the returned context.

        Returns:
            Formatted context string or empty string if no major NPCs match.
        """
        prompt_lower = prompt.lower()
        matched: List[Dict[str, Any]] = []
        for status in major_npc_statuses:
            name = status.get("name", "")
            role = status.get("role", "")
            notes = status.get("notes", "")
            relationships = status.get("relationships", {})
            is_match = (
                name.lower() in prompt_lower
                or role.lower() in prompt_lower
                or (notes and any(
                    w in prompt_lower
                    for w in notes.lower().split()[:_NPC_MATCH_FIRST_WORDS]
                    if len(w) >= _NPC_MATCH_MIN_WORD_LEN
                ))
                or any(k.lower() in prompt_lower for k in relationships)
            )
            if is_match:
                matched.append(status)
                if len(matched) >= max_npcs:
                    break
        if not matched:
            return ""
        parts = ["=== MAJOR NPC CONTEXT ==="]
        for status in matched:
            parts.append(
                f"\n**{status.get('name', '?')}** ({status.get('role', 'Major NPC')})"
            )
            notes = status.get("notes", "")
            plot_hooks = status.get("plot_hooks", [])
            defeat = status.get("defeat_conditions", [])
            if notes:
                parts.append(f"  Campaign role: {notes}")
            if plot_hooks:
                parts.append(f"  Active plot hooks: {'; '.join(plot_hooks[:2])}")
            if defeat:
                parts.append(f"  Defeat conditions: {defeat[0]}")
        parts.append("=== END MAJOR NPC CONTEXT ===")
        return "\n".join(parts)

    def get_rules_context_for_prompt(self, prompt: str) -> str:
        """Return D&D rules context for entities mentioned in a prompt.

        Extracts capitalised phrases, looks them up via the rules wiki, and
        returns a context block capped at _RULES_CONTEXT_BUDGET characters.

        Args:
            prompt: Story or AI prompt text.

        Returns:
            Formatted rules context string, or empty string if nothing found.
        """
        if not self.enabled or not self.rules_client:
            return ""
        raw_candidates: List[str] = re.findall(
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", prompt
        )
        seen: Set[str] = set()
        entities: List[str] = []
        for candidate in raw_candidates:
            if candidate in seen:
                continue
            if all(word in _RULES_STOP_WORDS for word in candidate.split()):
                continue
            seen.add(candidate)
            entities.append(candidate)
            if len(entities) >= _RULES_ENTITY_LIMIT:
                break
        if not entities:
            return ""
        descriptions: List[str] = []
        budget = _RULES_CONTEXT_BUDGET
        for entity in entities:
            if budget <= 0:
                break
            try:
                page_data = self.rules_client.fetch_page(entity)
                if not page_data or not page_data.get("sections"):
                    continue
                intro = page_data["sections"][0].get("content", "").strip()
                if not intro:
                    continue
                snippet = intro[:budget]
                descriptions.append(f"**{entity}**: {snippet}")
                budget -= len(snippet)
            except (AttributeError, KeyError, IndexError) as exc:
                logger.debug("Rules lookup failed for %r: %s", entity, exc)
        if not descriptions:
            return ""
        return "\n\nD&D Rules Context (for accurate portrayal):\n" + "\n".join(
            descriptions
        )


@functools.lru_cache(maxsize=1)
def get_rag_system() -> RAGSystem:
    """Get or create global RAG system instance."""
    return RAGSystem()

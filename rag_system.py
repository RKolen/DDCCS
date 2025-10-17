"""
RAG (Retrieval-Augmented Generation) System for D&D Campaign Wikis

This module provides wiki integration to enhance AI-generated stories with
accurate campaign setting lore, locations, and history.

Features:
- Fetch and cache wiki pages from configurable URLs
- Search for relevant lore when generating stories
- Integrate with character History checks
- Support multiple campaign settings (Exandria, Forgotten Realms, custom)

Configuration via .env:
    RAG_ENABLED=true
    RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki
    RAG_CACHE_TTL=604800  # 7 days
"""

import os
import json
import time
import hashlib
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import quote
import re

try:
    from item_registry import ItemRegistry
except ImportError:
    ItemRegistry = None

try:
    import requests
    from bs4 import BeautifulSoup

    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    print("⚠️  RAG System: requests or beautifulsoup4 not installed")
    print("   Install with: pip install requests beautifulsoup4")


class WikiCache:
    """
    Manages cached wiki content with TTL (time-to-live) support.
    All cached data is stored in .rag_cache/ directory (git-ignored).
    """

    def __init__(self, cache_dir: str = ".rag_cache", ttl_seconds: int = 604800):
        """
        Initialize wiki cache.

        Args:
            cache_dir: Directory to store cached pages
            ttl_seconds: Time-to-live for cached content (default: 7 days)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_seconds

        # Create index file
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return {}
        return {}

    def _save_index(self):
        """Save cache index to disk."""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2)

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[Dict]:
        """
        Retrieve cached content if available and not expired.

        Args:
            url: Wiki page URL

        Returns:
            Cached content dict or None if not available/expired
        """
        cache_key = self._get_cache_key(url)

        if cache_key not in self.index:
            return None

        entry = self.index[cache_key]

        # Check if expired
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            self.delete(url)
            return None

        # Load cached content
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def set(self, url: str, content: Dict):
        """
        Cache wiki page content.

        Args:
            url: Wiki page URL
            content: Page content dict with title, text, sections, etc.
        """
        cache_key = self._get_cache_key(url)

        # Save content
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)

        # Update index
        self.index[cache_key] = {
            "url": url,
            "timestamp": time.time(),
            "title": content.get("title", "Unknown"),
        }
        self._save_index()

    def delete(self, url: str):
        """Remove cached content."""
        cache_key = self._get_cache_key(url)

        if cache_key in self.index:
            del self.index[cache_key]
            self._save_index()

        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()

    def clear_expired(self):
        """Remove all expired cache entries."""
        expired_keys = []

        for cache_key, entry in self.index.items():
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                expired_keys.append(cache_key)

        for cache_key in expired_keys:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()
            del self.index[cache_key]

        if expired_keys:
            self._save_index()
            print(f"🧹 Cleared {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        return {
            "entries": len(self.index),
            "size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }


class WikiClient:
    """
    A client for fetching and parsing wiki pages, with caching and optional homebrew item filtering.

    This class provides methods to:
    - Fetch and cache wiki page content from a specified base URL.
    - Parse sections from wiki pages, cleaning and organizing content.
    - Search for relevant sections within a page based on a query.
    - Optionally block custom/homebrew item lookups via an item registry.

    Args:
        base_url (str): Base URL of the wiki (e.g., "https://criticalrole.fandom.com/wiki").
        cache (Optional[WikiCache]): Instance for caching page data. If not provided, a new
        cache is created.
        item_registry (optional): Registry for filtering custom/homebrew items.

    Attributes:
        base_url (str): The base URL for wiki requests.
        cache (WikiCache): The cache instance used for storing page data.
        item_registry: Registry for custom/homebrew item filtering.
        session (requests.Session or None): HTTP session for requests, if scraping is available.

    Methods:
        fetch_page(page_title: str, force_refresh: bool = False) -> Optional[Dict]:
            Fetches and parses a wiki page, returning its structured content.
        search_sections(page_data: Dict, query: str, max_results: int = 3) -> List[Dict]:
            Searches for relevant sections within a page based on a query string.

    Private Methods:
        _parse_sections(content_elem):
            Parses and organizes sections from the wiki page content element.
        _clean_wiki_text(text: str) -> str:
            Cleans wiki text by removing references, edit links, and excessive whitespace.
    """

    def _parse_sections(self, content_elem):
        """Helper to parse sections from wiki content element."""
        sections = []
        current_section = {"title": "Introduction", "content": ""}
        for elem in content_elem.find_all(["h2", "h3", "p", "ul"]):
            if elem.name in ["h2", "h3"]:
                if current_section["content"]:
                    current_section["content"] = self._clean_wiki_text(
                        current_section["content"]
                    )
                    sections.append(current_section)
                section_title = elem.get_text(strip=True)
                section_title = re.sub(r"\[edit\]", "", section_title).strip()
                current_section = {"title": section_title, "content": ""}
            elif elem.name == "p":
                text = elem.get_text(strip=True)
                if text:
                    current_section["content"] += text + "\n\n"
            elif elem.name == "ul":
                items = [li.get_text(strip=True) for li in elem.find_all("li")]
                if items:
                    current_section["content"] += (
                        "\n".join(f"• {item}" for item in items) + "\n\n"
                    )
        if current_section["content"]:
            current_section["content"] = self._clean_wiki_text(
                current_section["content"]
            )
            sections.append(current_section)
        return sections

    def __init__(
        self, base_url: str, cache: Optional[WikiCache] = None, item_registry=None
    ):
        """
        Initialize wiki client.

        Args:
            base_url: Base URL of the wiki (e.g., https://criticalrole.fandom.com/wiki)
            cache: WikiCache instance (creates new if not provided)
            item_registry: ItemRegistry for homebrew filtering (optional)
        """
        self.base_url = base_url.rstrip("/")
        self.cache = cache or WikiCache()
        self.item_registry = item_registry
        self.session = requests.Session() if SCRAPING_AVAILABLE else None
        if self.session:
            self.session.headers.update(
                {
                    "User-Agent": "DnD-Character-Consultant/1.0 "
                    "(Educational; +https://github.com/RKolen/DDCCS)"
                }
            )

    def _clean_wiki_text(self, text: str) -> str:
        """Clean wiki text by removing references, edit links, etc."""
        # Remove citation markers like [1], [2], etc.
        text = re.sub(r"\[\d+\]", "", text)

        # Remove edit links
        text = re.sub(r"\[edit\]", "", text)

        # Clean up excessive whitespace
        text = re.sub(r"\n\n+", "\n\n", text)
        text = text.strip()

        return text

    def fetch_page(
        self, page_title: str, force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Fetch wiki page content.

        Args:
            page_title: Title of the wiki page (e.g., "Tal'Dorei")
            force_refresh: Bypass cache and fetch fresh content

        Returns:
            Dict with page content or None if fetch failed
        """
        if not SCRAPING_AVAILABLE:
            print("⚠️  Cannot fetch wiki pages: requests/beautifulsoup4 not installed")
            return None
        if self.item_registry and self.item_registry.is_custom(page_title):
            print(f"🚫 Blocked custom item lookup: {page_title} (in custom registry)")
            return None
        page_url = f"{self.base_url}/{quote(page_title.replace(' ', '_'))}"
        if not force_refresh:
            cached = self.cache.get(page_url)
            if cached:
                print(f"✅ Cache hit: {page_title}")
                return cached
        page_data = None
        try:
            print(f"🌐 Fetching: {page_title}...")
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
                print(f"✅ Fetched: {title} ({len(sections)} sections)")
            else:
                print(f"⚠️  Could not find content for {page_title}")
        except requests.RequestException as e:
            print(f"❌ Failed to fetch {page_title}: {e}")
        except (ValueError, AttributeError) as e:
            print(f"❌ Error parsing {page_title}: {e}")
        return page_data

    def search_sections(
        self, page_data: Dict, query: str, max_results: int = 3
    ) -> List[Dict]:
        """
        Search for relevant sections within a page.

        Args:
            page_data: Page data from fetch_page()
            query: Search query
            max_results: Maximum number of sections to return

        Returns:
            List of relevant sections with relevance scores
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []

        for section in page_data["sections"]:
            title = section["title"].lower()
            content = section["content"].lower()

            # Calculate relevance score
            score = 0.0

            # Title match is worth more
            if query_lower in title:
                score += 2.0

            # Word matches in title
            title_words = set(title.split())
            title_matches = len(query_words & title_words)
            score += title_matches * 0.5

            # Word matches in content
            content_words = set(content.split())
            content_matches = len(query_words & content_words)
            score += content_matches * 0.1

            if score > 0:
                results.append({"section": section, "score": score})

        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]


class RAGSystem:
    """
    Main RAG system for integrating wiki knowledge with AI generation.

    IMPORTANT: Homebrew content is NEVER looked up on wikidot.
    Use ItemRegistry to mark homebrew items/rules.
    """

    def __init__(self, item_registry=None):
        """
        Initialize RAG system from .env configuration.

        Args:
            item_registry: Optional ItemRegistry instance for homebrew filtering
        """
        self.enabled = os.getenv("RAG_ENABLED", "false").lower() == "true"
        self.wiki_base_url = os.getenv("RAG_WIKI_BASE_URL", "")
        self.rules_base_url = os.getenv("RAG_RULES_BASE_URL", "")
        self.item_registry = item_registry

        # Load item registry if not provided
        if self.item_registry is None and ItemRegistry is not None:
            self.item_registry = ItemRegistry()

        if not self.enabled:
            self.client = None
            self.rules_client = None
            return

        if not SCRAPING_AVAILABLE:
            print("⚠️  RAG enabled but dependencies not installed")
            print("   Install with: pip install requests beautifulsoup4")
            self.client = None
            self.rules_client = None
            return

        # Initialize cache (shared between both clients)
        cache_ttl = int(os.getenv("RAG_CACHE_TTL", "604800"))  # 7 days default
        cache = WikiCache(ttl_seconds=cache_ttl)

        # Initialize lore wiki client (for locations, NPCs, etc.)
        if self.wiki_base_url:
            self.client = WikiClient(self.wiki_base_url, cache, self.item_registry)
            print(f"✅ RAG Lore Wiki initialized: {self.wiki_base_url}")
        else:
            self.client = None
            print("⚠️  RAG_WIKI_BASE_URL not set - lore lookups disabled")

        # Initialize rules wiki client (for items, spells, rules, etc.)
        if self.rules_base_url:
            self.rules_client = WikiClient(
                self.rules_base_url, cache, self.item_registry
            )
            print(f"✅ RAG Rules Wiki initialized: {self.rules_base_url}")
        else:
            self.rules_client = None
            print("⚠️  RAG_RULES_BASE_URL not set - item/spell lookups disabled")

        if self.item_registry:
            custom_count = len(self.item_registry.get_all_custom_items())
            print(
                f"   Custom item filter: {custom_count} items - will NOT lookup on wikidot"
            )

    def get_context_for_location(
        self, location_name: str, max_sections: int = 2
    ) -> str:
        """
        Get wiki context for a location.

        Args:
            location_name: Name of the location
            max_sections: Maximum sections to include

        Returns:
            Formatted context string to add to AI prompt
        """
        if not self.enabled or not self.client:
            return ""

        page_data = self.client.fetch_page(location_name)
        if not page_data:
            return ""

        # Get most relevant sections
        sections = page_data["sections"][:max_sections]

        context = f"\n\n=== LORE CONTEXT: {page_data['title']} ===\n"
        for section in sections:
            context += f"\n{section['title']}:\n{section['content']}\n"
        context += "=== END LORE CONTEXT ===\n\n"

        return context

    def get_context_for_query(
        self, query: str, pages_to_search: List[str], max_results: int = 3
    ) -> str:
        """
        Search multiple pages for relevant context.

        Args:
            query: What to search for
            pages_to_search: List of page titles to search
            max_results: Maximum results per page

        Returns:
            Formatted context string
        """
        if not self.enabled or not self.client:
            return ""

        context = f"\n\n=== LORE CONTEXT FOR: {query} ===\n"

        for page_title in pages_to_search:
            page_data = self.client.fetch_page(page_title)
            if not page_data:
                continue

            # Search for relevant sections
            results = self.client.search_sections(page_data, query, max_results)

            if results:
                context += f"\nFrom {page_data['title']}:\n"
                for result in results:
                    section = result["section"]
                    context += f"\n{section['title']}:\n{section['content']}\n"

        context += "\n=== END LORE CONTEXT ===\n\n"

        return context

    def get_history_check_info(self, topic: str, dc_result: int) -> Optional[str]:
        """
        Get information for a successful History check.

        Args:
            topic: What the character is trying to recall
            dc_result: The check result (determines detail level)

        Returns:
            Information the character recalls, or None if check failed
        """
        if not self.enabled or not self.client:
            return None

        # Fetch page
        page_data = self.client.fetch_page(topic)
        if not page_data:
            return None

        # Determine how much info based on check result
        if dc_result < 10:
            # Basic info - just introduction
            sections = page_data["sections"][:1]
        elif dc_result < 15:
            # Moderate info - 2 sections
            sections = page_data["sections"][:2]
        elif dc_result < 20:
            # Good info - 3 sections
            sections = page_data["sections"][:3]
        else:
            # Exceptional - all sections
            sections = page_data["sections"]

        # Format as character recall
        info = f"You recall the following about {page_data['title']}:\n\n"
        for section in sections:
            info += f"{section['title']}:\n{section['content']}\n\n"

        return info

    def fetch_item_info(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch information about an item, respecting custom/homebrew filtering.

        Logic:
        1. If item is in custom_items_registry.json -> return local info (do NOT lookup)
        2. If item is NOT in registry -> assume official, lookup on D&D 5e rules wiki

        Args:
            item_name: Name of the item to lookup

        Returns:
            Dict with item info, or None if not found
            {
                'name': str,
                'description': str,
                'properties': Dict[str, Any],
                'is_custom': bool,
                'is_magic': bool,
                'source': str ('custom_registry' or 'wikidot')
            }
        """
        if not self.enabled or not self.rules_client:
            return None

        # Check if item is in custom registry (homebrew)
        if self.item_registry:
            item = self.item_registry.get_item(item_name)

            # If item is in custom registry, return local info ONLY
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

        # Item not in custom registry - assume official, try D&D 5e rules wiki lookup
        page_data = self.rules_client.fetch_page(item_name)
        if not page_data:
            return None

        # Parse sections into description
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
            "is_magic": "magic" in item_name.lower(),  # Heuristic
            "source": "wikidot",
            "url": page_data.get("url", ""),
        }


def get_rag_system() -> RAGSystem:
    """Get or create global RAG system instance."""
    # Use closure to store singleton instance
    if not hasattr(get_rag_system, "instance"):
        get_rag_system.instance = RAGSystem()
    return get_rag_system.instance

"""Story search utilities.

Provides search functionality across story files within campaigns.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.path_utils import get_campaigns_dir
from src.utils.story_file_helpers import (
    STORY_PATTERN,
    get_story_file_paths_in_series,
    read_story_lines,
)


class SearchScope(Enum):
    """Scope for story searches."""

    CURRENT_STORY = "current"
    CURRENT_SERIES = "series"
    ALL_CAMPAIGNS = "all"


class SearchType(Enum):
    """Types of searches."""

    TEXT = "text"
    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    NPC = "npc"
    REGEX = "regex"


@dataclass
class SearchOptions:
    """Options for a story search operation."""

    case_sensitive: bool = False
    whole_word: bool = False


@dataclass
class SearchResult:
    """A single search result."""

    file_path: str
    line_number: int
    line_content: str
    match_span: tuple[int, int]
    context_before: str
    context_after: str
    relevance_score: float = 1.0


@dataclass
class SearchResults:
    """Collection of search results."""

    query: str
    search_type: SearchType
    scope: SearchScope
    results: list[SearchResult] = field(default_factory=list)
    total_matches: int = 0
    files_searched: int = 0

    def group_by_file(self) -> dict[str, list[SearchResult]]:
        """Group results by file path.

        Returns:
            Dictionary mapping file paths to their search results.
        """
        grouped: dict[str, list[SearchResult]] = {}
        for result in self.results:
            if result.file_path not in grouped:
                grouped[result.file_path] = []
            grouped[result.file_path].append(result)
        return grouped


class StorySearcher:
    """Search across story files."""

    _CONTEXT_LINES = 2
    _DIALOGUE_PATTERN = re.compile(r'"[^"]+"')

    def __init__(
        self,
        workspace_path: str,
        campaign_name: Optional[str] = None,
        story_path: Optional[str] = None,
    ) -> None:
        """Initialize searcher.

        Args:
            workspace_path: Root workspace path.
            campaign_name: Active campaign name (used for CURRENT_SERIES scope).
            story_path: Active story file path (used for CURRENT_STORY scope).
        """
        self.workspace_path = workspace_path
        self.campaign_name = campaign_name
        self.story_path = story_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        search_type: SearchType = SearchType.TEXT,
        scope: SearchScope = SearchScope.CURRENT_SERIES,
        options: Optional[SearchOptions] = None,
    ) -> SearchResults:
        """Search for content in stories.

        Args:
            query: Search query string.
            search_type: Type of search to perform.
            scope: Scope of the search.
            options: Optional SearchOptions for case sensitivity and word boundary.

        Returns:
            SearchResults with all matches.
        """
        resolved = options or SearchOptions()
        results = SearchResults(query=query, search_type=search_type, scope=scope)
        files = self._collect_files(scope)
        results.files_searched = len(files)
        pattern = self._build_pattern(query, search_type, resolved)
        for filepath in files:
            matches = self._search_file(filepath, pattern)
            results.results.extend(matches)
        results.total_matches = len(results.results)
        return results

    def search_character(
        self,
        character_name: str,
        scope: SearchScope = SearchScope.ALL_CAMPAIGNS,
    ) -> SearchResults:
        """Search for character appearances.

        Args:
            character_name: Name of character to find.
            scope: Search scope.

        Returns:
            SearchResults with character appearances.
        """
        opts = SearchOptions(whole_word=True)
        return self.search(
            character_name,
            search_type=SearchType.CHARACTER,
            scope=scope,
            options=opts,
        )

    def search_location(
        self,
        location_name: str,
        scope: SearchScope = SearchScope.ALL_CAMPAIGNS,
    ) -> SearchResults:
        """Search for location mentions.

        Args:
            location_name: Name of location to find.
            scope: Search scope.

        Returns:
            SearchResults with location mentions.
        """
        opts = SearchOptions(whole_word=True)
        return self.search(
            location_name,
            search_type=SearchType.LOCATION,
            scope=scope,
            options=opts,
        )

    def search_by_regex(
        self,
        pattern: str,
        scope: SearchScope = SearchScope.CURRENT_SERIES,
    ) -> SearchResults:
        """Search using regular expression.

        Args:
            pattern: Regex pattern to match.
            scope: Search scope.

        Returns:
            SearchResults with regex matches.
        """
        return self.search(pattern, search_type=SearchType.REGEX, scope=scope)

    def find_dialogue_by_character(
        self,
        character_name: str,
        scope: SearchScope = SearchScope.CURRENT_SERIES,
    ) -> SearchResults:
        """Find dialogue lines attributed to a character.

        Searches for lines where the character name appears close to
        quoted dialogue text.

        Args:
            character_name: Name of character.
            scope: Search scope.

        Returns:
            SearchResults with dialogue matches.
        """
        results = SearchResults(
            query=character_name,
            search_type=SearchType.CHARACTER,
            scope=scope,
        )
        files = self._collect_files(scope)
        results.files_searched = len(files)
        name_re = re.compile(r"\b" + re.escape(character_name) + r"\b", re.IGNORECASE)
        for filepath in files:
            results.results.extend(
                self._find_dialogue_matches(filepath, name_re)
            )
        results.total_matches = len(results.results)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_dialogue_matches(
        self,
        filepath: str,
        name_re: re.Pattern[str],
    ) -> list[SearchResult]:
        """Return dialogue search results for a single file.

        Args:
            filepath: Path to the story file.
            name_re: Compiled pattern for the character name.

        Returns:
            List of SearchResult objects for dialogue matches.
        """
        matches: list[SearchResult] = []
        lines = read_story_lines(filepath) or []
        for idx, line in enumerate(lines):
            has_name = name_re.search(line)
            has_dialogue = self._DIALOGUE_PATTERN.search(line)
            if has_name and has_dialogue:
                match = has_name
                ctx_before, ctx_after = self._extract_context(lines, idx)
                matches.append(
                    SearchResult(
                        file_path=filepath,
                        line_number=idx + 1,
                        line_content=line.rstrip(),
                        match_span=(match.start(), match.end()),
                        context_before=ctx_before,
                        context_after=ctx_after,
                    )
                )
        return matches

    def _collect_files(self, scope: SearchScope) -> list[str]:
        """Return list of story file paths for the given scope.

        Args:
            scope: The search scope.

        Returns:
            Sorted list of story markdown file paths.
        """
        campaigns_dir = get_campaigns_dir(self.workspace_path)
        files: list[str] = []

        if scope == SearchScope.CURRENT_STORY:
            if self.story_path and os.path.isfile(self.story_path):
                files = [self.story_path]
        elif scope == SearchScope.CURRENT_SERIES:
            if self.campaign_name:
                files = get_story_file_paths_in_series(
                    self.workspace_path, self.campaign_name
                )
        else:  # ALL_CAMPAIGNS
            if os.path.isdir(campaigns_dir):
                for entry in sorted(os.listdir(campaigns_dir)):
                    series_dir = os.path.join(campaigns_dir, entry)
                    if os.path.isdir(series_dir):
                        files.extend(self._story_files_in_dir(series_dir))
        return files

    def _story_files_in_dir(self, directory: str) -> list[str]:
        """Return sorted story file paths in a directory.

        Args:
            directory: Path to directory to scan.

        Returns:
            Sorted list of matching file paths.
        """
        if not os.path.isdir(directory):
            return []
        return sorted(
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if STORY_PATTERN.match(f)
        )

    def _build_pattern(
        self,
        query: str,
        search_type: SearchType,
        options: SearchOptions,
    ) -> re.Pattern[str]:
        """Build a compiled regex pattern for the search.

        Args:
            query: Search query string.
            search_type: Type of search.
            options: Search options controlling case and word boundaries.

        Returns:
            Compiled regular expression pattern.
        """
        flags = 0 if options.case_sensitive else re.IGNORECASE
        raw = query if search_type == SearchType.REGEX else re.escape(query)
        if options.whole_word:
            raw = r"\b" + raw + r"\b"
        return re.compile(raw, flags)

    def _search_file(
        self,
        filepath: str,
        pattern: re.Pattern[str],
    ) -> list[SearchResult]:
        """Search a single file for pattern matches.

        Args:
            filepath: Path to the story file.
            pattern: Compiled regex pattern.

        Returns:
            List of SearchResult objects for all matches found.
        """
        lines = read_story_lines(filepath) or []
        matches: list[SearchResult] = []
        for idx, line in enumerate(lines):
            for match in pattern.finditer(line):
                ctx_before, ctx_after = self._extract_context(lines, idx)
                matches.append(
                    SearchResult(
                        file_path=filepath,
                        line_number=idx + 1,
                        line_content=line.rstrip(),
                        match_span=(match.start(), match.end()),
                        context_before=ctx_before,
                        context_after=ctx_after,
                    )
                )
        return matches

    def _extract_context(
        self,
        lines: list[str],
        line_index: int,
    ) -> tuple[str, str]:
        """Extract context lines around a match.

        Args:
            lines: All lines in the file.
            line_index: Zero-based index of the matching line.

        Returns:
            Tuple of (context_before, context_after) as joined strings.
        """
        start = max(0, line_index - self._CONTEXT_LINES)
        end = min(len(lines), line_index + self._CONTEXT_LINES + 1)
        before = "".join(lines[start:line_index]).rstrip()
        after = "".join(lines[line_index + 1 : end]).rstrip()
        return before, after

"""Unified access point for all story tools.

Provides a single StoryTools facade that exposes all story utility
capabilities: search, statistics, comparison, validation,
import/export, and templates.
"""

from typing import Any, Optional

from src.stories.tools.story_comparator import StoryComparator, StoryDiff
from src.stories.tools.story_export_helpers import (
    StoryExportHelper,
    StoryExportOptions,
    SeriesExportOptions,
)
from src.stories.tools.story_import_helpers import (
    StoryImportHelper,
    ImportOptions,
    ImportResult,
)
from src.stories.tools.story_search import (
    SearchResults,
    SearchScope,
    SearchType,
    StorySearcher,
)
from src.stories.tools.story_statistics import SeriesMetrics, StoryMetrics, StoryStatistics
from src.stories.tools.story_templates import StorySnippet, StoryTemplate, TemplateManager
from src.stories.tools.story_validator import StoryValidator, ValidationResult


class StoryTools:
    """Facade providing unified access to all story tool modules.

    All tools share the same workspace_path and optional campaign context.
    Modules are instantiated lazily and stored in a single internal dict.
    """

    def __init__(
        self,
        workspace_path: str,
        campaign_name: Optional[str] = None,
        story_path: Optional[str] = None,
    ) -> None:
        """Initialize the story tools facade.

        Args:
            workspace_path: Root workspace path.
            campaign_name: Active campaign name for scoped operations.
            story_path: Active story file path for single-story operations.
        """
        self._workspace_path = workspace_path
        self._campaign_name = campaign_name
        self._story_path = story_path
        self._tools: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Lazy-loaded tool accessors
    # ------------------------------------------------------------------

    @property
    def searcher(self) -> StorySearcher:
        """Return the StorySearcher instance."""
        if "searcher" not in self._tools:
            self._tools["searcher"] = StorySearcher(
                self._workspace_path,
                self._campaign_name,
                self._story_path,
            )
        return self._tools["searcher"]

    @property
    def statistics(self) -> StoryStatistics:
        """Return the StoryStatistics instance."""
        if "statistics" not in self._tools:
            self._tools["statistics"] = StoryStatistics(self._workspace_path)
        return self._tools["statistics"]

    @property
    def comparator(self) -> StoryComparator:
        """Return the StoryComparator instance."""
        if "comparator" not in self._tools:
            self._tools["comparator"] = StoryComparator(self._workspace_path)
        return self._tools["comparator"]

    @property
    def validator(self) -> StoryValidator:
        """Return the StoryValidator instance."""
        if "validator" not in self._tools:
            self._tools["validator"] = StoryValidator(self._workspace_path)
        return self._tools["validator"]

    @property
    def exporter(self) -> StoryExportHelper:
        """Return the StoryExportHelper instance."""
        if "exporter" not in self._tools:
            self._tools["exporter"] = StoryExportHelper(self._workspace_path)
        return self._tools["exporter"]

    @property
    def importer(self) -> StoryImportHelper:
        """Return the StoryImportHelper instance."""
        if "importer" not in self._tools:
            self._tools["importer"] = StoryImportHelper(self._workspace_path)
        return self._tools["importer"]

    @property
    def templates(self) -> TemplateManager:
        """Return the TemplateManager instance."""
        if "templates" not in self._tools:
            self._tools["templates"] = TemplateManager(self._workspace_path)
        return self._tools["templates"]

    # ------------------------------------------------------------------
    # Convenience shortcuts
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        search_type: SearchType = SearchType.TEXT,
        scope: SearchScope = SearchScope.CURRENT_SERIES,
    ) -> SearchResults:
        """Search for content in stories.

        Args:
            query: Search query string.
            search_type: Type of search to perform.
            scope: Scope of the search.

        Returns:
            SearchResults with all matches.
        """
        return self.searcher.search(query, search_type, scope)

    def story_stats(
        self,
        story_path: str,
        character_names: Optional[list[str]] = None,
    ) -> StoryMetrics:
        """Calculate metrics for a single story.

        Args:
            story_path: Path to story file.
            character_names: Optional list of character names to track.

        Returns:
            StoryMetrics for the story.
        """
        return self.statistics.calculate_story_metrics(story_path, character_names)

    def series_stats(
        self,
        series_name: str,
        character_names: Optional[list[str]] = None,
    ) -> SeriesMetrics:
        """Calculate aggregated metrics for a series.

        Args:
            series_name: Name of the series.
            character_names: Optional list of character names to track.

        Returns:
            SeriesMetrics for the series.
        """
        return self.statistics.calculate_series_metrics(series_name, character_names)

    def diff(self, source_path: str, target_path: str) -> StoryDiff:
        """Compare two story files.

        Args:
            source_path: Path to source story file.
            target_path: Path to target story file.

        Returns:
            StoryDiff with all detected changes.
        """
        return self.comparator.compare_stories(source_path, target_path)

    def validate(
        self,
        story_path: str,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate a story file.

        Args:
            story_path: Path to story file.
            strict: Enable strict validation mode.

        Returns:
            ValidationResult with all issues found.
        """
        return self.validator.validate_story(story_path, strict)

    def export_story(
        self,
        story_path: str,
        output_path: str,
        options: Optional[StoryExportOptions] = None,
    ) -> str:
        """Export a single story to a file.

        Args:
            story_path: Path to story file.
            output_path: Destination path for the exported file.
            options: Export options.

        Returns:
            Path to the exported file.
        """
        return self.exporter.export_story(story_path, output_path, options)

    def export_series(
        self,
        series_name: str,
        output_path: str,
        options: Optional[SeriesExportOptions] = None,
    ) -> str:
        """Export an entire series.

        Args:
            series_name: Name of the series.
            output_path: Destination path.
            options: Export options.

        Returns:
            Path to the exported file or directory.
        """
        return self.exporter.export_series(series_name, output_path, options)

    def import_story(
        self,
        source_path: str,
        target_series: Optional[str] = None,
        options: Optional[ImportOptions] = None,
    ) -> ImportResult:
        """Import a story from an external file.

        Args:
            source_path: Path to source file.
            target_series: Optional series to add story to.
            options: Import options.

        Returns:
            ImportResult with import status.
        """
        return self.importer.import_story(source_path, target_series, options)

    def apply_template(
        self,
        template_name: str,
        values: dict[str, str],
    ) -> str:
        """Apply a template with placeholder values.

        Args:
            template_name: Name of the template.
            values: Placeholder name to value mapping.

        Returns:
            Template content with placeholders filled.
        """
        return self.templates.apply_template(template_name, values)

    def list_templates(self) -> list[StoryTemplate]:
        """List all available templates.

        Returns:
            List of StoryTemplate objects.
        """
        return self.templates.list_templates()

    def list_snippets(self) -> list[StorySnippet]:
        """List all available snippets.

        Returns:
            List of StorySnippet objects.
        """
        return self.templates.list_snippets()

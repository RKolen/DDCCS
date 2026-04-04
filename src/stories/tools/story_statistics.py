"""Story statistics and analytics utilities.

Provides word counts, character appearances, and other metrics
for individual story files and entire series.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from src.utils.file_io import read_text_file
from src.utils.story_file_helpers import get_story_file_paths_in_series

_WORDS_PER_MINUTE = 200
_SENTENCE_PATTERN = re.compile(r"[.!?]+")
_DIALOGUE_PATTERN = re.compile(r'"[^"]+"')
_COMBAT_KEYWORDS = re.compile(
    r"\b(attack|struck|sword|shield|battle|combat|fight|wound|blood|arrow)\b",
    re.IGNORECASE,
)
_EXPLORATION_KEYWORDS = re.compile(
    r"\b(travel|journey|path|road|forest|mountain|river|explored|discovered)\b",
    re.IGNORECASE,
)


@dataclass
class CharacterAppearance:
    """Statistics for a character's appearance in a story."""

    character_name: str
    mention_count: int
    dialogue_count: int
    action_count: int
    first_appearance_line: int
    last_appearance_line: int
    scenes_present: list[str] = field(default_factory=list)


@dataclass
class TextCounts:
    """Basic text metrics for a story file."""

    word_count: int = 0
    character_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    reading_time_minutes: float = 0.0


@dataclass
class ContentBreakdown:
    """Content-type breakdown percentages and location data."""

    dialogue_percentage: float = 0.0
    combat_percentage: float = 0.0
    exploration_percentage: float = 0.0
    location_mentions: dict[str, int] = field(default_factory=dict)


@dataclass
class StoryMetrics:
    """Metrics for a single story file."""

    file_path: str
    counts: TextCounts = field(default_factory=TextCounts)
    character_appearances: dict[str, CharacterAppearance] = field(default_factory=dict)
    breakdown: ContentBreakdown = field(default_factory=ContentBreakdown)


@dataclass
class SeriesSummary:
    """Aggregated numeric totals for a story series."""

    total_stories: int = 0
    total_word_count: int = 0
    total_reading_time_minutes: float = 0.0
    average_story_length: float = 0.0


@dataclass
class SeriesMetrics:
    """Aggregated metrics for a story series."""

    series_name: str
    summary: SeriesSummary = field(default_factory=SeriesSummary)
    character_appearances: dict[str, int] = field(default_factory=dict)
    location_mentions: dict[str, int] = field(default_factory=dict)
    story_metrics: list[StoryMetrics] = field(default_factory=list)


class StoryStatistics:
    """Calculate statistics and metrics for story files."""

    def __init__(self, workspace_path: str) -> None:
        """Initialize statistics calculator.

        Args:
            workspace_path: Root workspace path.
        """
        self.workspace_path = workspace_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_story_metrics(
        self,
        story_path: str,
        character_names: Optional[list[str]] = None,
    ) -> StoryMetrics:
        """Calculate metrics for a single story file.

        Args:
            story_path: Path to story file.
            character_names: Optional list of character names to track.

        Returns:
            StoryMetrics for the story.
        """
        content = read_text_file(story_path) or ""
        lines = content.splitlines()
        counts = self._build_text_counts(content)
        breakdown = self._build_content_breakdown(content, lines, counts.word_count)
        appearances = self._build_character_appearances(lines, character_names)
        return StoryMetrics(
            file_path=story_path,
            counts=counts,
            character_appearances=appearances,
            breakdown=breakdown,
        )

    def calculate_series_metrics(
        self,
        series_name: str,
        character_names: Optional[list[str]] = None,
    ) -> SeriesMetrics:
        """Calculate aggregated metrics for a series.

        Args:
            series_name: Name of the story series (campaign directory name).
            character_names: Optional list of character names to track.

        Returns:
            SeriesMetrics for the entire series.
        """
        story_files = get_story_file_paths_in_series(self.workspace_path, series_name)
        all_metrics = [
            self.calculate_story_metrics(fp, character_names) for fp in story_files
        ]
        summary = self._build_series_summary(all_metrics)
        char_totals = self._aggregate_character_appearances(all_metrics)
        return SeriesMetrics(
            series_name=series_name,
            summary=summary,
            character_appearances=char_totals,
            story_metrics=all_metrics,
        )

    def get_character_appearance_timeline(
        self,
        character_name: str,
        series_name: str,
    ) -> list[dict[str, object]]:
        """Get timeline of character appearances across a series.

        Args:
            character_name: Name of character to track.
            series_name: Name of the series.

        Returns:
            List of appearance records, one per story file.
        """
        series_metrics = self.calculate_series_metrics(series_name, [character_name])
        timeline: list[dict[str, object]] = []
        for story_m in series_metrics.story_metrics:
            appearance = story_m.character_appearances.get(character_name)
            timeline.append(
                {
                    "file_path": story_m.file_path,
                    "file_name": os.path.basename(story_m.file_path),
                    "mention_count": appearance.mention_count if appearance else 0,
                    "dialogue_count": appearance.dialogue_count if appearance else 0,
                    "first_line": appearance.first_appearance_line if appearance else 0,
                }
            )
        return timeline

    def calculate_readability_score(self, story_path: str) -> dict[str, float]:
        """Calculate readability scores for a story using Flesch-Kincaid formulas.

        Args:
            story_path: Path to story file.

        Returns:
            Dictionary with 'flesch_reading_ease' and 'flesch_kincaid_grade' scores.
        """
        content = read_text_file(story_path) or ""
        words = content.split()
        word_count = len(words)
        if word_count == 0:
            return {"flesch_reading_ease": 0.0, "flesch_kincaid_grade": 0.0}

        sentences = [s for s in _SENTENCE_PATTERN.split(content) if s.strip()]
        sentence_count = max(1, len(sentences))
        syllable_count = sum(self._count_syllables(w) for w in words)
        words_per_sentence = word_count / sentence_count
        syllables_per_word = syllable_count / word_count
        flesch_ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
        flesch_grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
        return {
            "flesch_reading_ease": round(flesch_ease, 2),
            "flesch_kincaid_grade": round(flesch_grade, 2),
        }

    def generate_statistics_report(
        self,
        metrics: StoryMetrics,
        output_format: str = "markdown",
    ) -> str:
        """Generate a formatted statistics report.

        Args:
            metrics: StoryMetrics to report.
            output_format: Output format - 'markdown' or 'text'.

        Returns:
            Formatted statistics report string.
        """
        file_name = os.path.basename(metrics.file_path)
        counts = metrics.counts
        breakdown = metrics.breakdown

        if output_format == "markdown":
            return self._markdown_report(file_name, counts, breakdown, metrics)
        return self._text_report(file_name, counts, breakdown)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_text_counts(self, content: str) -> TextCounts:
        """Compute basic text counts from story content.

        Args:
            content: Full story content string.

        Returns:
            Populated TextCounts dataclass.
        """
        words = content.split()
        word_count = len(words)
        sentences = [s for s in _SENTENCE_PATTERN.split(content) if s.strip()]
        paragraphs = [p for p in re.split(r"\n\s*\n", content) if p.strip()]
        reading_time = word_count / _WORDS_PER_MINUTE if word_count else 0.0
        return TextCounts(
            word_count=word_count,
            character_count=len(content),
            sentence_count=len(sentences),
            paragraph_count=len(paragraphs),
            reading_time_minutes=round(reading_time, 2),
        )

    def _build_content_breakdown(
        self,
        content: str,
        lines: list[str],
        word_count: int,
    ) -> ContentBreakdown:
        """Compute content-type percentages from story content.

        Args:
            content: Full story content string.
            lines: Story lines.
            word_count: Total word count (used as denominator).

        Returns:
            Populated ContentBreakdown dataclass.
        """
        dialogue_pct = self._dialogue_percentage(lines)
        combat_pct = self._keyword_percentage(content, _COMBAT_KEYWORDS, word_count)
        exploration_pct = self._keyword_percentage(
            content, _EXPLORATION_KEYWORDS, word_count
        )
        return ContentBreakdown(
            dialogue_percentage=dialogue_pct,
            combat_percentage=combat_pct,
            exploration_percentage=exploration_pct,
        )

    def _build_character_appearances(
        self,
        lines: list[str],
        character_names: Optional[list[str]],
    ) -> dict[str, CharacterAppearance]:
        """Build character appearance stats for each requested name.

        Args:
            lines: Story lines.
            character_names: Character names to track, or None to skip.

        Returns:
            Dict mapping character name to CharacterAppearance.
        """
        if not character_names:
            return {}
        return {
            name: app
            for name in character_names
            for app in [self._extract_character_appearance(name, lines)]
            if app.mention_count > 0
        }

    def _build_series_summary(self, all_metrics: list[StoryMetrics]) -> SeriesSummary:
        """Compute aggregated series summary from per-story metrics.

        Args:
            all_metrics: List of StoryMetrics for each story in the series.

        Returns:
            Populated SeriesSummary dataclass.
        """
        total_words = sum(m.counts.word_count for m in all_metrics)
        total_reading = sum(m.counts.reading_time_minutes for m in all_metrics)
        avg_length = total_words / len(all_metrics) if all_metrics else 0.0
        return SeriesSummary(
            total_stories=len(all_metrics),
            total_word_count=total_words,
            total_reading_time_minutes=round(total_reading, 2),
            average_story_length=round(avg_length, 2),
        )

    def _aggregate_character_appearances(
        self, all_metrics: list[StoryMetrics]
    ) -> dict[str, int]:
        """Sum character mention counts across all stories in a series.

        Args:
            all_metrics: List of StoryMetrics for each story.

        Returns:
            Dict mapping character name to total mention count.
        """
        char_totals: dict[str, int] = {}
        for story_m in all_metrics:
            for name, app in story_m.character_appearances.items():
                char_totals[name] = char_totals.get(name, 0) + app.mention_count
        return char_totals

    def _markdown_report(
        self,
        file_name: str,
        counts: TextCounts,
        breakdown: ContentBreakdown,
        metrics: StoryMetrics,
    ) -> str:
        """Build a markdown-formatted statistics report.

        Args:
            file_name: Story file base name.
            counts: TextCounts for the story.
            breakdown: ContentBreakdown for the story.
            metrics: Full StoryMetrics (for character appearances).

        Returns:
            Markdown report string.
        """
        lines: list[str] = [
            f"## Story Statistics: {file_name}",
            "",
            "### Counts",
            f"- Words: {counts.word_count:,}",
            f"- Sentences: {counts.sentence_count:,}",
            f"- Paragraphs: {counts.paragraph_count:,}",
            f"- Characters: {counts.character_count:,}",
            f"- Reading time: {counts.reading_time_minutes:.1f} min",
            "",
            "### Content Breakdown",
            f"- Dialogue: {breakdown.dialogue_percentage:.1f}%",
            f"- Combat: {breakdown.combat_percentage:.1f}%",
            f"- Exploration: {breakdown.exploration_percentage:.1f}%",
        ]
        if metrics.character_appearances:
            lines.append("")
            lines.append("### Character Appearances")
            for name, app in sorted(
                metrics.character_appearances.items(),
                key=lambda x: x[1].mention_count,
                reverse=True,
            ):
                lines.append(
                    f"- {name}: {app.mention_count} mentions, "
                    f"{app.dialogue_count} dialogue lines"
                )
        return "\n".join(lines)

    def _text_report(
        self,
        file_name: str,
        counts: TextCounts,
        breakdown: ContentBreakdown,
    ) -> str:
        """Build a plain-text statistics report.

        Args:
            file_name: Story file base name.
            counts: TextCounts for the story.
            breakdown: ContentBreakdown for the story.

        Returns:
            Plain-text report string.
        """
        lines = [
            f"Story Statistics: {file_name}",
            f"  Words: {counts.word_count:,}",
            f"  Sentences: {counts.sentence_count:,}",
            f"  Paragraphs: {counts.paragraph_count:,}",
            f"  Reading time: {counts.reading_time_minutes:.1f} min",
            f"  Dialogue: {breakdown.dialogue_percentage:.1f}%",
            f"  Combat: {breakdown.combat_percentage:.1f}%",
            f"  Exploration: {breakdown.exploration_percentage:.1f}%",
        ]
        return "\n".join(lines)

    def _dialogue_percentage(self, lines: list[str]) -> float:
        """Calculate percentage of lines containing dialogue.

        Args:
            lines: Lines of the story.

        Returns:
            Percentage (0-100) of lines with quoted dialogue.
        """
        if not lines:
            return 0.0
        dialogue_lines = sum(1 for line in lines if _DIALOGUE_PATTERN.search(line))
        return round(100.0 * dialogue_lines / len(lines), 2)

    def _keyword_percentage(
        self,
        content: str,
        pattern: re.Pattern[str],
        word_count: int,
    ) -> float:
        """Calculate percentage of words matching a keyword pattern.

        Args:
            content: Full story content.
            pattern: Compiled keyword pattern.
            word_count: Total word count.

        Returns:
            Percentage (0-100) of matching keyword occurrences.
        """
        if word_count == 0:
            return 0.0
        matches = len(pattern.findall(content))
        return round(100.0 * matches / word_count, 2)

    def _extract_character_appearance(
        self, name: str, lines: list[str]
    ) -> CharacterAppearance:
        """Extract appearance statistics for a character.

        Args:
            name: Character name.
            lines: Lines of the story file.

        Returns:
            CharacterAppearance with all stats populated.
        """
        name_re = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
        mention_count = 0
        dialogue_count = 0
        action_count = 0
        first_line = 0
        last_line = 0
        scenes: list[str] = []
        current_scene = ""

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("## ") or stripped.startswith("# "):
                current_scene = stripped.lstrip("#").strip()
            if name_re.search(line):
                mention_count += 1
                if mention_count == 1:
                    first_line = idx + 1
                last_line = idx + 1
                if _DIALOGUE_PATTERN.search(line):
                    dialogue_count += 1
                else:
                    action_count += 1
                if current_scene and current_scene not in scenes:
                    scenes.append(current_scene)

        return CharacterAppearance(
            character_name=name,
            mention_count=mention_count,
            dialogue_count=dialogue_count,
            action_count=action_count,
            first_appearance_line=first_line,
            last_appearance_line=last_line,
            scenes_present=scenes,
        )

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word using vowel group heuristic.

        Args:
            word: Word to count syllables for.

        Returns:
            Estimated syllable count (minimum 1).
        """
        cleaned = re.sub(r"[^a-zA-Z]", "", word.lower())
        if not cleaned:
            return 1
        vowel_groups = re.findall(r"[aeiou]+", cleaned)
        count = len(vowel_groups)
        if cleaned.endswith("e") and count > 1:
            count -= 1
        return max(1, count)

"""AI-powered character arc analysis."""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.character_arc.arc_criteria import (
    ArcCriteria,
    ArcDimension,
    ArcDirection,
    ArcStage,
)
from src.character_arc.arc_data import ArcDataPoint, CharacterArc

# Long session stories are split into chunks of this many characters and each
# chunk is analysed with its own small model call, then merged. This keeps every
# call's context small (bounded memory — a wide context window OOM'd Ollama)
# while still covering the whole story instead of just the opening scene.
_CHUNK_CHARS = 4000
# Cap chunks per story so a pathologically long story cannot spawn unbounded
# calls; 40 chunks * 4000 chars covers 160k characters.
_MAX_CHUNKS = 40
# Token ceiling for model calls. Local qwen3 models always "think" first (~2k+
# tokens, more on the larger model) even with disable_thinking, so the budget
# must outlast the reasoning or the answer is truncated to empty. This is a
# ceiling: fast per-story calls still stop early. Tunable for larger models.
_SYNTHESIS_MAX_TOKENS = int(os.getenv("ARC_SYNTHESIS_MAX_TOKENS", "8000"))


@dataclass
class AnalysisResult:
    """Result of arc analysis for a single dimension."""

    dimension: ArcDimension
    direction: ArcDirection
    confidence: float
    observations: List[str]
    evidence: List[str]


class ArcAnalyzer:
    """Analyzes character arcs using AI and pattern matching."""

    def __init__(
        self,
        ai_client: Optional[Any] = None,
        criteria: Optional[ArcCriteria] = None,
        pronouns: str = "",
    ):
        """Initialize the arc analyzer.

        Args:
            ai_client: Optional AIClient for enhanced analysis.
            criteria: Arc analysis criteria (uses defaults if omitted).
            pronouns: The character's pronouns (e.g. "she/her"), included in AI
                prompts so the model does not guess the character's gender.
        """
        self.ai_client = ai_client
        self.criteria = criteria or ArcCriteria()
        self.pronouns = pronouns.strip()

    def _pronoun_hint(self, character_name: str) -> str:
        """A prompt clause pinning the character's pronouns, or empty."""
        if not self.pronouns:
            return ""
        return f" Use {self.pronouns} pronouns for {character_name}."

    def analyze_story(
        self,
        story_content: str,
        character_name: str,
        story_file: str = "",
        session_id: str = "",
    ) -> ArcDataPoint:
        """Analyze a story for character development.

        Args:
            story_content: The story text to analyze.
            character_name: Name of the character to analyze.
            story_file: Path to the story file.
            session_id: Session identifier.

        Returns:
            ArcDataPoint with analysis results.
        """
        data_point = ArcDataPoint(
            story_file=story_file,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
        )

        if self.ai_client:
            ai_analysis = self._ai_analyze_story(story_content, character_name)
            data_point.metric_values = ai_analysis.get("metrics", {})
            data_point.observations = ai_analysis.get("observations", [])
            data_point.key_events = ai_analysis.get("key_events", [])
            data_point.ai_analysis = ai_analysis.get("summary", "")
        else:
            data_point.metric_values = self._pattern_analyze_story(
                story_content, character_name
            )

        return data_point

    def _ai_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call the AI for a JSON object response, returning ``{}`` on failure.

        Args:
            system_prompt: The system role instruction.
            user_prompt: The user role prompt.

        Returns:
            The parsed JSON object, or an empty dict when unavailable or invalid.
        """
        if self.ai_client is None:
            return {}
        try:
            messages = [
                self.ai_client.create_system_message(system_prompt),
                self.ai_client.create_user_message(user_prompt),
            ]
            # A large budget plus disabled thinking keeps qwen3 from leaving the
            # content empty; the JSON object is then parsed out of the reply.
            response = self.ai_client.chat_completion(
                messages, max_tokens=_SYNTHESIS_MAX_TOKENS, disable_thinking=True
            )
            return self._parse_ai_response(response)
        except (RuntimeError, OSError, ValueError):
            return {}

    def analyze_chunk(self, chunk: str, character_name: str) -> Dict[str, Any]:
        """Analyze one story chunk (small, memory-safe model call)."""
        prompt = (
            f"Analyze this excerpt for character development of "
            f"{character_name}.{self._pronoun_hint(character_name)}\n\n"
            f"Excerpt:\n{chunk}\n\n"
            "Provide analysis in the following JSON format:\n"
            "{\n"
            '    "metrics": {\n'
            '        "relationship_strength": <1-10>,\n'
            '        "trust_level": <1-10>,\n'
            '        "combat_effectiveness": <1-10>,\n'
            '        "confidence": <1-10>,\n'
            '        "trauma_level": <0-10>\n'
            "    },\n"
            '    "observations": [\n'
            f'        "A concrete note naming who {character_name} interacted '
            'with and how the relationship shifted"\n'
            "    ],\n"
            '    "key_events": [\n'
            f'        "A concrete event: who was involved (name them) and what '
            f'{character_name} did or what happened to them"\n'
            "    ],\n"
            '    "summary": "Brief summary of character development in this excerpt"\n'
            "}\n\n"
            "For trauma_level, higher means MORE trauma (0 = none, 10 = severe).\n"
            "Be specific and name other characters, goals, and events — do not "
            "write vague development statements. Focus on:\n"
            "1. How the character changed or grew\n"
            "2. Relationships (name the other characters and how bonds shifted)\n"
            "3. Skills or abilities used or gained\n"
            "4. Emotional or psychological changes\n"
            "5. Goals pursued or progressed"
        )
        return self._ai_json(
            "You are a narrative analyst. Return only valid JSON.", prompt
        )

    def _ai_analyze_story(
        self,
        story_content: str,
        character_name: str,
    ) -> Dict[str, Any]:
        """Analyze a full story by chunking it and merging per-chunk results.

        Long stories are split into small chunks so each model call has a small,
        memory-safe context; the per-chunk analyses are then merged into one.
        """
        chunks = _chunk_text(story_content, _CHUNK_CHARS)[:_MAX_CHUNKS]
        if not chunks:
            return {"metrics": {}, "observations": [], "key_events": [], "summary": ""}
        if len(chunks) == 1:
            return self.analyze_chunk(chunks[0], character_name)
        partials = [self.analyze_chunk(chunk, character_name) for chunk in chunks]
        return _merge_chunk_analyses(partials)

    def analyze_relationships(
        self,
        story_content: str,
        character_name: str,
    ) -> List[Dict[str, Any]]:
        """AI-extract the character's relationship arcs from narrative text.

        Args:
            story_content: Combined narrative text across the character's stories.
            character_name: The character whose relationships to extract.

        Returns:
            A list of relationship dicts (target, type, strength, trust, note);
            empty when AI is unavailable.
        """
        prompt = (
            f"List EVERY other named character who appears alongside "
            f"{character_name} in the following narrative, and characterise "
            f"{character_name}'s relationship with each — include allies, "
            "companions, rivals, and even brief or one-sided bonds. Do not return "
            f"an empty list unless no other character is named."
            f"{self._pronoun_hint(character_name)}\n\n"
            f"Narrative:\n{story_content[:12000]}\n\n"
            'Return only JSON. "target" is the other character\'s name:\n'
            '{ "relationships": [ { "target": "<other character name>", '
            '"type": "<ally|rival|mentor|friend|enemy|family|neutral>", '
            '"strength": <1-10>, "trust": <1-10>, '
            '"note": "<one sentence on this relationship\'s arc>" } ] }'
        )
        result = self._ai_json(
            "You are a narrative analyst. Return only valid JSON.", prompt
        )
        relationships = result.get("relationships", [])
        return relationships if isinstance(relationships, list) else []

    def analyze_goals(
        self,
        story_content: str,
        character_name: str,
    ) -> List[Dict[str, Any]]:
        """AI-extract the character's goals and their progress from narrative.

        Args:
            story_content: Combined narrative text across the character's stories.
            character_name: The character whose goals to extract.

        Returns:
            A list of goal dicts (description, status, progress); empty when AI
            is unavailable.
        """
        prompt = (
            f"Identify {character_name}'s goals and their progress across the "
            f"following narrative.{self._pronoun_hint(character_name)}\n\n"
            f"Narrative:\n{story_content[:12000]}\n\n"
            "Return only JSON in this format:\n"
            '{ "goals": [ { "description": "<goal>", '
            '"status": "<active|dormant|completed>", "progress": <0-100> } ] }'
        )
        result = self._ai_json(
            "You are a narrative analyst. Return only valid JSON.", prompt
        )
        goals = result.get("goals", [])
        return goals if isinstance(goals, list) else []

    def narrate_arc(
        self,
        character_name: str,
        narrative: str,
        facts: str,
    ) -> str:
        """Write a vivid, fact-grounded arc summary from collected material.

        Unlike a metric-only summary, this names the actual people, places, and
        turning points from the collected key events so the summary reads like a
        story rather than a list of number changes.

        Args:
            character_name: The character being summarized.
            narrative: Concatenated concrete key events / observations.
            facts: A pre-formatted block of relationships / goals / metric trends.

        Returns:
            A prose arc summary, or a short fallback when AI is unavailable.
        """
        if self.ai_client is None:
            return f"{character_name}'s arc spans the campaign."
        prompt = (
            f"Write a vivid 3 to 5 sentence character arc summary for "
            f"{character_name}.{self._pronoun_hint(character_name)}\n\n"
            f"Key events and observations across the campaign:\n"
            f"{narrative[:8000]}\n\n"
            f"{facts}\n\n"
            "Narrate the actual journey: name the people, places, and turning "
            "points from the events above, and describe how the character "
            "changed. Do not just restate numbers — tell the story of the arc."
        )
        try:
            messages = [self.ai_client.create_user_message(prompt)]
            # Local qwen3 models always "think" (~2k tokens) even with
            # disable_thinking; the budget must outlast the reasoning or the
            # answer is truncated to empty. Keep it generous.
            summary = self.ai_client.chat_completion(
                messages, max_tokens=_SYNTHESIS_MAX_TOKENS, disable_thinking=True
            ).strip()
            return summary or f"{character_name}'s arc spans the campaign."
        except (RuntimeError, OSError, ValueError):
            return f"{character_name}'s arc spans the campaign."

    def narrate_metrics(
        self,
        character_name: str,
        metrics: Dict[str, Dict[str, Any]],
        narrative: str,
    ) -> Dict[str, str]:
        """Write a one-sentence, event-grounded insight for each metric's trend.

        Replaces the templated "X rose from A to B" note with a sentence that
        explains what in the story drove the change. One model call covers every
        metric; a missing or malformed reply simply leaves the templated note.

        Args:
            character_name: The character being analyzed.
            metrics: The built metric series, keyed by metric key.
            narrative: The concatenated key events / observations.

        Returns:
            A mapping of metric key to a one-sentence insight (only keys the
            model answered for and left non-empty).
        """
        if self.ai_client is None or not metrics:
            return {}
        trend_lines = []
        for key, metric in metrics.items():
            series = metric.get("series", [])
            if not series:
                continue
            trend_lines.append(
                f'- {key} ("{metric.get("label", key)}"): '
                f"{series[0]:.0f} -> {series[-1]:.0f}"
            )
        system_prompt = (
            "You are a D&D character arc analyst. For each metric, write ONE "
            "concise sentence explaining what in the story drove its change. "
            "Name the people and events involved; do not just restate the numbers."
        )
        user_prompt = (
            f"Character: {character_name}.{self._pronoun_hint(character_name)}\n\n"
            f"Key events across the campaign:\n{narrative[:12000]}\n\n"
            f"Metric trends (key: start -> end):\n" + "\n".join(trend_lines) + "\n\n"
            "Return a JSON object mapping each metric key above to its "
            'one-sentence insight, e.g. {"confidence": "Rain grew surer after '
            'facing Ruthen."}. Use only the listed metric keys.'
        )
        result = self._ai_json(system_prompt, user_prompt)
        return {
            key: str(value).strip()
            for key, value in result.items()
            if key in metrics and isinstance(value, str) and str(value).strip()
        }

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI JSON response into structured data."""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if 0 <= start < end:
                parsed = json.loads(response[start:end])
                return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass
        return {}

    def _pattern_analyze_story(
        self,
        story_content: str,
        character_name: str,
    ) -> Dict[str, Any]:
        """Pattern-based analysis without AI."""
        metrics: Dict[str, Any] = {}

        char_pattern = re.compile(
            rf"\b{re.escape(character_name)}\b",
            re.IGNORECASE,
        )
        mentions = len(char_pattern.findall(story_content))
        metrics["engagement"] = min(10, mentions)

        combat_patterns = [
            r"\b(?:attacks?|strikes?|hits?|damage|wounds?)\b",
            r"\b(?:battle|combat|fight)\b",
        ]
        combat_score = sum(
            len(re.findall(p, story_content, re.IGNORECASE))
            for p in combat_patterns
        )
        metrics["combat_involvement"] = min(10, combat_score)

        social_patterns = [
            r"\b(?:talks?|speaks?|says?|replies?)\b",
            r"\b(?:negotiates?|persuades?|convinces?)\b",
        ]
        social_score = sum(
            len(re.findall(p, story_content, re.IGNORECASE))
            for p in social_patterns
        )
        metrics["social_involvement"] = min(10, social_score)

        return metrics

    def analyze_arc_progression(
        self,
        arc: CharacterArc,
    ) -> Dict[str, Any]:
        """Analyze the overall progression of a character arc.

        Args:
            arc: CharacterArc to analyze.

        Returns:
            Dict with direction, stage, summary, and dimension_analyses.
        """
        if len(arc.data_points) < self.criteria.min_stories_for_analysis:
            return {
                "direction": ArcDirection.STASIS.value,
                "stage": ArcStage.INTRODUCTION.value,
                "summary": "Insufficient data for arc analysis (need at least 2 stories).",
                "dimension_analyses": [],
            }

        dimension_analyses = [
            self._analyze_dimension(arc, dimension)
            for dimension in self.criteria.dimensions
        ]

        overall_direction = self._determine_overall_direction(dimension_analyses)
        arc_stage = self._determine_arc_stage(arc)
        summary = self._generate_arc_summary(arc, dimension_analyses)

        return {
            "direction": overall_direction,
            "stage": arc_stage,
            "summary": summary,
            "dimension_analyses": [
                {
                    "dimension": a.dimension.value,
                    "direction": a.direction.value,
                    "confidence": a.confidence,
                    "observations": a.observations,
                }
                for a in dimension_analyses
            ],
        }

    def _analyze_dimension(
        self,
        arc: CharacterArc,
        dimension: ArcDimension,
    ) -> AnalysisResult:
        """Analyze a specific dimension of character development."""
        metrics = self.criteria.get_metrics_for_dimension(dimension)

        observations: List[str] = []
        changes: List[float] = []

        for metric in metrics:
            progression = arc.get_metric_progression(metric.metric_id)

            if len(progression) >= 2:
                first_value = progression[0][1]
                last_value = progression[-1][1]

                if isinstance(first_value, (int, float)) and isinstance(
                    last_value, (int, float)
                ):
                    change = last_value - first_value
                    relative_change = abs(change) / max(abs(first_value), 1)

                    if relative_change >= self.criteria.significance_threshold:
                        changes.append(change)
                        observations.append(
                            f"{metric.name}: {first_value} -> {last_value}"
                        )

        if not changes:
            direction = ArcDirection.STASIS
            confidence = 0.5
        elif sum(1 for c in changes if c > 0) > len(changes) * 0.7:
            direction = ArcDirection.GROWTH
            confidence = 0.8
        elif sum(1 for c in changes if c < 0) > len(changes) * 0.7:
            direction = ArcDirection.DECLINE
            confidence = 0.8
        else:
            direction = ArcDirection.FLUCTUATION
            confidence = 0.6

        return AnalysisResult(
            dimension=dimension,
            direction=direction,
            confidence=confidence,
            observations=observations,
            evidence=[],
        )

    def _determine_overall_direction(
        self,
        analyses: List[AnalysisResult],
    ) -> str:
        """Determine overall arc direction from dimension analyses."""
        growth_count = sum(
            1 for a in analyses if a.direction == ArcDirection.GROWTH
        )
        decline_count = sum(
            1 for a in analyses if a.direction == ArcDirection.DECLINE
        )

        if growth_count > decline_count + 2:
            return ArcDirection.GROWTH.value
        if decline_count > growth_count + 2:
            return ArcDirection.DECLINE.value
        if growth_count == 0 and decline_count == 0:
            return ArcDirection.STASIS.value
        return ArcDirection.FLUCTUATION.value

    def _determine_arc_stage(self, arc: CharacterArc) -> str:
        """Determine the current stage of the character arc."""
        num_points = len(arc.data_points)
        thresholds = [
            (0, ArcStage.INTRODUCTION),
            (1, ArcStage.ESTABLISHMENT),
            (2, ArcStage.CHALLENGE),
            (4, ArcStage.DEVELOPMENT),
            (6, ArcStage.CLIMAX),
            (8, ArcStage.RESOLUTION),
        ]
        for threshold, stage in thresholds:
            if num_points <= threshold:
                return stage.value
        return ArcStage.AFTERMATH.value

    def _generate_arc_summary(
        self,
        arc: CharacterArc,
        analyses: List[AnalysisResult],
    ) -> str:
        """Generate a summary of the character arc."""
        if self.ai_client:
            return self._ai_generate_summary(arc, analyses)
        return self._pattern_generate_summary(arc, analyses)

    def _pattern_generate_summary(
        self,
        arc: CharacterArc,
        analyses: List[AnalysisResult],
    ) -> str:
        """Generate a pattern-based summary without AI."""
        parts = [f"{arc.character_name}'s arc shows"]

        direction_counts: Dict[str, int] = {}
        for analysis in analyses:
            key = analysis.direction.value
            direction_counts[key] = direction_counts.get(key, 0) + 1

        if direction_counts:
            main_direction = max(direction_counts, key=lambda k: direction_counts[k])
            parts.append(f"overall {main_direction}")

        for analysis in analyses:
            if analysis.observations:
                parts.append(
                    f"In {analysis.dimension.value}: "
                    f"{', '.join(analysis.observations[:2])}"
                )

        return ". ".join(parts) + "."

    def _ai_generate_summary(
        self,
        arc: CharacterArc,
        analyses: List[AnalysisResult],
    ) -> str:
        """Use AI to generate an arc summary grounded in the measured metrics."""
        if self.ai_client is None:
            return f"{arc.character_name}'s arc spans {len(arc.data_points)} stories."
        metric_text = "\n".join(
            f"- {m['label']}: {m['series'][0]:.0f} -> {m['series'][-1]:.0f} ({m['direction']})"
            for m in _build_metric_series(arc).values()
            if len(m["series"]) >= 2
        )
        analysis_text = "\n".join(
            f"- {a.dimension.value}: {a.direction.value} (confidence: {a.confidence:.0%})"
            for a in analyses
        )

        prompt = (
            f"Summarize the character arc for {arc.character_name}."
            f"{self._pronoun_hint(arc.character_name)}\n\n"
            f"Measured metric changes across {len(arc.data_points)} stories "
            f"(first -> last value):\n{metric_text or '(none)'}\n\n"
            f"Dimension trends:\n{analysis_text}\n\n"
            "Write a 2-3 sentence summary of the character's development. Stay "
            "consistent with the measured directions above: a RISING trauma "
            "value means MORE trauma (not healing); a FALLING confidence value "
            "means LESS confidence. Do not contradict the numbers."
        )

        try:
            messages = [
                self.ai_client.create_user_message(prompt),
            ]
            return self.ai_client.chat_completion(
                messages, max_tokens=1200, disable_thinking=True
            )
        except (RuntimeError, OSError, ValueError):
            return f"{arc.character_name}'s arc spans {len(arc.data_points)} stories."


def _chunk_text(text: str, size: int) -> List[str]:
    """Split text into chunks of at most ``size`` characters on paragraph
    boundaries, hard-splitting any single paragraph that is itself too long."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: List[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        while len(paragraph) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(paragraph[:size])
            paragraph = paragraph[size:]
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 2 > size:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks


def _merge_chunk_analyses(partials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge per-chunk analyses into one: metrics averaged, text collected."""
    metric_totals: Dict[str, float] = {}
    metric_counts: Dict[str, int] = {}
    observations: List[str] = []
    key_events: List[str] = []
    summaries: List[str] = []

    for partial in partials:
        metrics = partial.get("metrics")
        if isinstance(metrics, dict):
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    metric_totals[key] = metric_totals.get(key, 0.0) + float(value)
                    metric_counts[key] = metric_counts.get(key, 0) + 1
        observations.extend(partial.get("observations", []))
        key_events.extend(partial.get("key_events", []))
        summary = partial.get("summary")
        if summary:
            summaries.append(str(summary))

    metrics = {
        key: round(total / metric_counts[key], 1)
        for key, total in metric_totals.items()
    }
    return {
        "metrics": metrics,
        "observations": observations[:8],
        "key_events": key_events[:8],
        "summary": " ".join(summaries),
    }


_METRIC_LABELS: Dict[str, str] = {
    "relationship_strength": "Relationship Strength",
    "trust_level": "Trust",
    "combat_effectiveness": "Combat Effectiveness",
    "confidence": "Confidence",
    "trauma_level": "Trauma",
    "goal_progress": "Goal Progress",
    "engagement": "Engagement",
    "combat_involvement": "Combat Involvement",
    "social_involvement": "Social Involvement",
}


def _metric_direction(series: List[float]) -> str:
    """Classify a metric's direction from first-to-last change."""
    if len(series) < 2:
        return ArcDirection.STASIS.value
    delta = series[-1] - series[0]
    threshold = max(abs(series[0]) * 0.1, 0.5)
    if delta > threshold:
        return ArcDirection.GROWTH.value
    if delta < -threshold:
        return ArcDirection.DECLINE.value
    return ArcDirection.STASIS.value


def _metric_obs(label: str, series: List[float]) -> str:
    """A short factual note describing this metric's own trend across the arc."""
    if not series:
        return ""
    if len(series) < 2:
        return f"{label} observed once at {series[0]:.0f}."
    first, last = series[0], series[-1]
    if last > first:
        return f"{label} rose from {first:.0f} to {last:.0f} across the arc."
    if last < first:
        return f"{label} fell from {first:.0f} to {last:.0f} across the arc."
    return f"{label} held steady at {first:.0f} across the arc."


# Surfaced as its own richer section (the Goals list), so it is not also shown
# as a raw metric — the two were independent estimates that could contradict.
_EXCLUDED_METRICS = {"goal_progress"}


def _build_metric_series(arc: CharacterArc) -> Dict[str, Dict[str, Any]]:
    """Build per-metric series (label, values, direction, observation)."""
    ordered_keys: List[str] = []
    for data_point in arc.data_points:
        for key in data_point.metric_values:
            if key not in ordered_keys and key not in _EXCLUDED_METRICS:
                ordered_keys.append(key)

    metrics: Dict[str, Dict[str, Any]] = {}
    for key in ordered_keys:
        series = [
            float(dp.metric_values[key])
            for dp in arc.data_points
            if isinstance(dp.metric_values.get(key), (int, float))
        ]
        if not series:
            continue
        label = _METRIC_LABELS.get(key, key.replace("_", " ").title())
        metrics[key] = {
            "label": label,
            "series": series,
            "direction": _metric_direction(series),
            "obs": _metric_obs(label, series),
        }
    return metrics


def _enrich_metric_obs(
    analyzer: ArcAnalyzer,
    character_name: str,
    metrics: Dict[str, Dict[str, Any]],
    narrative: str,
) -> None:
    """Replace templated metric notes with model-written, event-grounded ones.

    Mutates ``metrics`` in place; a missing or malformed reply leaves the
    templated note untouched.
    """
    for key, obs in analyzer.narrate_metrics(character_name, metrics, narrative).items():
        metrics[key]["obs"] = obs


def analyze_story_datapoint(
    analyzer: ArcAnalyzer,
    content: str,
    character_name: str,
    title: str = "",
    story_number: Optional[int] = None,
) -> ArcDataPoint:
    """Analyze a single story into one arc data point.

    The per-story step of arc analysis, exposed separately so a caller can run
    stories one request at a time (each a single model call) and aggregate the
    stored data points afterwards — avoiding one long multi-call request.

    Args:
        analyzer: An :class:`ArcAnalyzer` configured with the AI client and the
            character's pronouns.
        content: The story text.
        character_name: The character to analyze.
        title: The story title (stored as the data point's ``story_file``).
        story_number: The story number (stored as ``session_id``).

    Returns:
        The story's :class:`ArcDataPoint`.
    """
    return analyzer.analyze_story(
        content,
        character_name,
        story_file=title,
        session_id="" if story_number is None else str(story_number),
    )


def facts_block(
    metrics: Dict[str, Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    goals: List[Dict[str, Any]],
) -> str:
    """Format the extracted relationships/goals/metric trends for the summary."""
    rel_text = "; ".join(
        f"{rel.get('target', '')} ({rel.get('type', '')})"
        for rel in relationships
        if rel.get("target")
    ) or "none noted"
    goal_text = "; ".join(
        str(goal.get("description", ""))
        for goal in goals
        if goal.get("description")
    ) or "none noted"
    metric_text = "; ".join(
        f"{metric['label']} {metric['direction']}"
        for metric in metrics.values()
    ) or "no clear trend"
    return (
        f"Relationships: {rel_text}\n"
        f"Goals: {goal_text}\n"
        f"Metric trends: {metric_text}"
    )


def _narrative_from_points(data_points: List[ArcDataPoint]) -> str:
    """Build a narrative for relationship/goal extraction from the concrete
    per-story facts (key events + observations first, then summaries), so the
    extractor sees named characters and events rather than vague blurbs."""
    parts: List[str] = []
    for data_point in data_points:
        parts.extend(data_point.key_events)
        parts.extend(data_point.observations)
        if data_point.ai_analysis:
            parts.append(data_point.ai_analysis)
    return "\n".join(parts)


def aggregate_arc(
    data_points: List[ArcDataPoint],
    character_name: str,
    campaign_name: str = "",
    ai_client: Optional[Any] = None,
    pronouns: str = "",
) -> Dict[str, Any]:
    """Aggregate per-story data points into a full character arc.

    Runs the progression (direction/stage/summary), builds the metric series,
    and extracts relationships and goals from the distilled per-story summaries.

    Args:
        data_points: The stored per-story :class:`ArcDataPoint` list.
        character_name: The character being analyzed.
        campaign_name: The campaign the character belongs to.
        ai_client: Optional AIClient for relationship/goal extraction.
        pronouns: The character's pronouns for the AI prompts.

    Returns:
        A dict with direction, stage, summary, stories_analyzed, updated_at,
        metrics, relationships, and goals.
    """
    analyzer = ArcAnalyzer(ai_client=ai_client, pronouns=pronouns)
    arc = CharacterArc(character_name=character_name, campaign_name=campaign_name)
    for data_point in data_points:
        arc.add_data_point(data_point)

    progression = analyzer.analyze_arc_progression(arc)
    narrative = _narrative_from_points(data_points)
    metrics = _build_metric_series(arc)
    _enrich_metric_obs(analyzer, character_name, metrics, narrative)
    relationships = analyzer.analyze_relationships(narrative, character_name)
    goals = analyzer.analyze_goals(narrative, character_name)
    summary = analyzer.narrate_arc(
        character_name, narrative, facts_block(metrics, relationships, goals)
    )

    return {
        "direction": progression["direction"],
        "stage": progression["stage"],
        "summary": summary,
        "stories_analyzed": len(arc.data_points),
        "updated_at": arc.state.updated_at,
        "metrics": metrics,
        "relationships": relationships,
        "goals": goals,
    }


def analyze_character_arc(
    stories: List[Dict[str, Any]],
    character_name: str,
    campaign_name: str = "",
    ai_client: Optional[Any] = None,
    pronouns: str = "",
) -> Dict[str, Any]:
    """Analyze a full character arc from ordered story texts (single-shot).

    Convenience wrapper that runs every story then aggregates. Prefer the
    two-step ``analyze_story_datapoint`` + ``aggregate_arc`` path for many
    stories so each request stays a single model call.

    Args:
        stories: Ordered story dicts, each with ``content`` and optional
            ``title`` / ``story_number``.
        character_name: The character to analyze.
        campaign_name: The campaign the character belongs to.
        ai_client: Optional AIClient; without it, pattern analysis is used and
            relationships/goals are empty.
        pronouns: The character's pronouns for the AI prompts.

    Returns:
        A dict with direction, stage, summary, stories_analyzed, updated_at,
        metrics, relationships, and goals.
    """
    analyzer = ArcAnalyzer(ai_client=ai_client, pronouns=pronouns)
    data_points: List[ArcDataPoint] = []
    for story in stories:
        content = str(story.get("content", ""))
        if not content.strip():
            continue
        number = story.get("story_number")
        data_points.append(
            analyze_story_datapoint(
                analyzer,
                content,
                character_name,
                title=str(story.get("title", "")),
                story_number=number if isinstance(number, int) else None,
            )
        )
    return aggregate_arc(
        data_points, character_name, campaign_name, ai_client, pronouns=pronouns
    )

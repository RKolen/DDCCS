"""AI-powered character arc analysis."""

import json
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
    ):
        """Initialize the arc analyzer.

        Args:
            ai_client: Optional AIClient for enhanced analysis.
            criteria: Arc analysis criteria (uses defaults if omitted).
        """
        self.ai_client = ai_client
        self.criteria = criteria or ArcCriteria()

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

    def _ai_analyze_story(
        self,
        story_content: str,
        character_name: str,
    ) -> Dict[str, Any]:
        """Use AI to analyze a story for character development."""
        if self.ai_client is None:
            return {"metrics": {}, "observations": [], "key_events": [], "summary": ""}
        prompt = (
            f"Analyze the following story for character development of {character_name}.\n\n"
            f"Story:\n{story_content[:4000]}\n\n"
            "Provide analysis in the following JSON format:\n"
            "{\n"
            '    "metrics": {\n'
            '        "relationship_strength": <1-10>,\n'
            '        "trust_level": <1-10>,\n'
            '        "combat_effectiveness": <1-10>,\n'
            '        "confidence": <1-10>,\n'
            '        "trauma_level": <0-10>,\n'
            '        "goal_progress": <0-100>\n'
            "    },\n"
            '    "observations": [\n'
            '        "Observation 1 about character development"\n'
            "    ],\n"
            '    "key_events": [\n'
            '        "Event that affected the character"\n'
            "    ],\n"
            '    "summary": "Brief summary of character development in this story"\n'
            "}\n\n"
            "Focus on:\n"
            "1. How the character changed or grew\n"
            "2. Relationship developments\n"
            "3. Skills or abilities used or gained\n"
            "4. Emotional or psychological changes\n"
            "5. Progress toward goals"
        )

        try:
            messages = [
                self.ai_client.create_system_message(
                    "You are a narrative analyst. Return only valid JSON."
                ),
                self.ai_client.create_user_message(prompt),
            ]
            response = self.ai_client.chat_completion(messages)
            return self._parse_ai_response(response)
        except (RuntimeError, OSError, ValueError):
            return {"metrics": {}, "observations": [], "key_events": [], "summary": ""}

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI JSON response into structured data."""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if 0 <= start < end:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"metrics": {}, "observations": [], "key_events": [], "summary": ""}

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
        """Use AI to generate an arc summary."""
        if self.ai_client is None:
            return f"{arc.character_name}'s arc spans {len(arc.data_points)} stories."
        analysis_text = "\n".join(
            f"- {a.dimension.value}: {a.direction.value} (confidence: {a.confidence:.0%})"
            for a in analyses
        )

        prompt = (
            f"Summarize the character arc for {arc.character_name} based on:\n\n"
            f"{analysis_text}\n\n"
            f"Number of story appearances: {len(arc.data_points)}\n\n"
            "Provide a 2-3 sentence summary of the character's development journey."
        )

        try:
            messages = [
                self.ai_client.create_user_message(prompt),
            ]
            return self.ai_client.chat_completion(messages)
        except (RuntimeError, OSError, ValueError):
            return f"{arc.character_name}'s arc spans {len(arc.data_points)} stories."

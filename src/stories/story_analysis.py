"""
Story Analysis Component.

Handles story file analysis including character actions extraction,
DC request parsing, and consistency checking.
"""

import os
from typing import Dict, Any, Optional
from src.characters.consultants.consultant_core import CharacterConsultant
from src.utils.file_io import read_text_file, file_exists
from src.utils.story_parsing_utils import extract_character_actions, extract_dc_requests


class StoryAnalyzer:
    """Analyzes story files for character actions and consistency."""

    def __init__(self, consultants: Dict[str, CharacterConsultant]):
        """
        Initialize story analyzer.

        Args:
            consultants: Dictionary of character consultants
        """
        self.consultants = consultants

    def analyze_story_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze a story file for character actions and consistency.

        Args:
            filepath: Path to the story file

        Returns:
            Dictionary containing analysis results
        """
        if not file_exists(filepath):
            return {"error": "Story file not found"}

        content = read_text_file(filepath)
        if content is None:
            return {"error": "Failed to read story file"}

        # Extract character actions using utility
        character_names = list(self.consultants.keys())
        character_actions = extract_character_actions(content, character_names)

        # Get consultant analysis for each character
        consultant_analyses = {}
        for character_name, actions in character_actions.items():
            if character_name in self.consultants:
                consultant = self.consultants[character_name]
                analysis = consultant.analyze_story_consistency(content, actions)
                consultant_analyses[character_name] = analysis

        # Extract DC requests using utility
        dc_requests = extract_dc_requests(content)
        dc_suggestions = {}
        for request in dc_requests:
            suggestions = self.get_dc_suggestions(request)
            dc_suggestions[request] = suggestions

        return {
            "story_file": (
                filepath.split(os.sep)[-1] if os.sep in filepath else filepath
            ),
            "character_actions": character_actions,
            "consultant_analyses": consultant_analyses,
            "dc_requests": dc_requests,
            "dc_suggestions": dc_suggestions,
            "overall_consistency": self._calculate_overall_consistency(
                consultant_analyses
            ),
        }

    def get_dc_suggestions(
        self, action_request: str, character_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get DC suggestions for a specific action request.

        Args:
            action_request: Description of the action
            character_name: Optional character attempting the action

        Returns:
            Dictionary of DC suggestions from consultants
        """
        suggestions = {}

        # If character specified, get their consultant's suggestion
        if character_name and character_name in self.consultants:
            consultant = self.consultants[character_name]
            suggestion = consultant.suggest_dc_for_action(action_request)
            suggestions[character_name] = suggestion
        else:
            # Try to identify which character from the request text
            for char_name, consultant in self.consultants.items():
                if char_name.lower() in action_request.lower():
                    suggestion = consultant.suggest_dc_for_action(action_request)
                    suggestions[char_name] = suggestion
                    break

            # If no specific character found, use first available consultant
            if not suggestions and self.consultants:
                first_consultant = next(iter(self.consultants.values()))
                suggestion = first_consultant.suggest_dc_for_action(action_request)
                suggestions["General"] = suggestion

        return suggestions

    def _calculate_overall_consistency(
        self, analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall consistency metrics.

        Args:
            analyses: Dictionary of character analyses

        Returns:
            Dictionary with overall consistency metrics
        """
        if not analyses:
            return {"score": 0, "rating": "No character actions to analyze"}

        total_score = sum(
            analysis["consistency_score"] for analysis in analyses.values()
        )
        average_score = total_score / len(analyses)

        all_issues = []
        all_positives = []

        for analysis in analyses.values():
            all_issues.extend(analysis["issues"])
            all_positives.extend(analysis["positive_notes"])

        return {
            "score": round(average_score, 2),
            "rating": self._get_overall_rating(average_score),
            "total_issues": len(all_issues),
            "total_positives": len(all_positives),
            "summary": (
                f"{len(analyses)} characters analyzed, "
                f"{len(all_positives)} positive notes, "
                f"{len(all_issues)} issues found"
            ),
        }

    def _get_overall_rating(self, score: float) -> str:
        """
        Convert overall score to rating.

        Args:
            score: Consistency score (0-1)

        Returns:
            Rating string
        """
        if score >= 0.8:
            return "Excellent - All characters very consistent"
        if score >= 0.6:
            return "Good - Most characters consistent"
        if score >= 0.4:
            return "Fair - Some character inconsistencies"
        if score >= 0.2:
            return "Poor - Multiple character issues"
        return "Very Poor - Major character problems"

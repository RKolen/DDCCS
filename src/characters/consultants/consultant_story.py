"""
Story Analysis Component for Character Consultant

Provides story consistency analysis, character development tracking,
and relationship management for character consultants.
"""

from typing import Dict, List, Any, Optional


class StoryAnalyzer:
    """Handles story analysis and character development tracking."""

    def __init__(self, profile, class_knowledge):
        """
        Initialize story analyzer.

        Args:
            profile: CharacterProfile instance
            class_knowledge: Class knowledge dictionary
        """
        self.profile = profile
        self.class_knowledge = class_knowledge

    def get_relationships(self) -> Dict[str, str]:
        """
        Get character's relationships.

        Returns:
            Dictionary of relationships
        """
        return self.profile.relationships

    def analyze_story_consistency(
        self, story_text: str, character_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze if character actions in a story are consistent with their profile.

        Args:
            story_text: Full story text for context
            character_actions: List of actions taken by the character

        Returns:
            Dictionary with consistency analysis including score, rating, issues, and suggestions
        """
        consistency_score = 0
        issues = []
        positive_notes = []

        # Check each action against character profile
        for action in character_actions:
            action_analysis = self._analyze_single_action(action, story_text)
            consistency_score += action_analysis["score"]
            issues.extend(action_analysis["issues"])
            positive_notes.extend(action_analysis["positives"])

        average_score = (
            consistency_score / len(character_actions) if character_actions else 0
        )

        return {
            "character": self.profile.name,
            "consistency_score": round(average_score, 2),
            "overall_rating": self._get_consistency_rating(average_score),
            "issues": issues,
            "positive_notes": positive_notes,
            "suggestions": self._get_improvement_suggestions(issues),
        }

    def _analyze_single_action(self, action: str, context: str) -> Dict[str, Any]:
        """
        Analyze a single character action for consistency.

        Args:
            action: The action taken by the character
            context: Story context surrounding the action

        Returns:
            Dictionary with score (0-1), issues list, and positives list
        """
        score = 0.5  # Neutral starting score
        issues = []
        positives = []

        action_lower = action.lower()

        # Check against class tendencies
        class_reactions = self.class_knowledge.get("common_reactions", {})
        for situation, expected in class_reactions.items():
            if situation in context.lower():
                if any(word in action_lower for word in expected.lower().split()):
                    score += 0.3
                    positives.append(
                        f"Action aligns with {self.profile.character_class.value} nature"
                    )

        # Check against personality
        if self.profile.personality_summary:
            personality_words = self.profile.personality_summary.lower().split()
            if any(word in action_lower for word in personality_words):
                score += 0.2
                positives.append("Action reflects established personality")

        # Check against motivations
        for motivation in self.profile.motivations:
            if any(word in action_lower for word in motivation.lower().split()):
                score += 0.2
                positives.append(f"Action driven by motivation: {motivation}")

        # Check against fears/weaknesses (should be hesitant or conflicted)
        for fear in self.profile.fears_weaknesses:
            if any(word in context.lower() for word in fear.lower().split()):
                if (
                    "hesitat" in action_lower
                    or "reluctant" in action_lower
                    or "afraid" in action_lower
                ):
                    score += 0.1
                    positives.append(f"Appropriately shows concern about: {fear}")
                else:
                    score -= 0.2
                    issues.append(f"Didn't acknowledge fear/weakness: {fear}")

        return {
            "score": max(0, min(1, score)),  # Clamp between 0 and 1
            "issues": issues,
            "positives": positives,
        }

    def _get_consistency_rating(self, score: float) -> str:
        """
        Convert numerical consistency score to rating.

        Args:
            score: Consistency score (0-1)

        Returns:
            Human-readable rating string
        """
        if score >= 0.8:
            return "Excellent - Very true to character"
        if score >= 0.6:
            return "Good - Mostly consistent"
        if score >= 0.4:
            return "Fair - Some inconsistencies"
        if score >= 0.2:
            return "Poor - Several character issues"
        return "Very Poor - Out of character"

    def _get_improvement_suggestions(self, issues: List[str]) -> List[str]:
        """
        Generate suggestions for improving character consistency.

        Args:
            issues: List of consistency issues found

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        if issues:
            suggestions.append(
                f"Consider how {self.profile.name}'s "
                f"{self.profile.character_class.value} training would influence their approach"
            )

            if self.profile.motivations:
                suggestions.append(
                    f"Remember {self.profile.name}'s primary motivation: "
                    f"{self.profile.motivations[0]}"
                )

            if self.profile.personality_summary:
                suggestions.append(
                    f"Keep {self.profile.name}'s {self.profile.personality_summary} "
                    f"personality in mind"
                )

        return suggestions

    def suggest_relationship_update(
        self, other_character: str, interaction_context: str
    ) -> Optional[str]:
        """
        Suggest updating relationships based on story interactions.

        Args:
            other_character: Name of other character/NPC
            interaction_context: Context of the interaction

        Returns:
            Suggestion string for adding/updating relationship, or None
        """
        current_relationships = self.get_relationships()

        # If no existing relationship, suggest creating one
        if other_character not in current_relationships:
            suggestions = {
                "positive_interaction": (
                    f"Appreciates {other_character}'s help in {interaction_context}"
                ),
                "conflict": (
                    f"Has tensions with {other_character} over {interaction_context}"
                ),
                "neutral": (
                    f"Working relationship with {other_character} "
                    f"after {interaction_context}"
                ),
                "suspicious": (
                    f"Remains cautious about {other_character} "
                    f"following {interaction_context}"
                ),
            }

            # Suggest based on character class tendencies
            class_name = self.profile.character_class.value.lower()

            if class_name in ["paladin", "cleric"]:
                return (
                    f"SUGGESTION: Add relationship - '{other_character}': "
                    f"'{suggestions['positive_interaction']}'"
                )
            if class_name in ["rogue", "warlock"]:
                return (
                    f"SUGGESTION: Add relationship - '{other_character}': "
                    f"'{suggestions['suspicious']}'"
                )
            return (
                f"SUGGESTION: Add relationship - '{other_character}': "
                f"'{suggestions['neutral']}'"
            )

        # If existing relationship, suggest updating it
        current = current_relationships[other_character]
        return (
            f"SUGGESTION: Update relationship with {other_character} - "
            f"Current: '{current}' - Consider how {interaction_context} affects this"
        )

    def suggest_plot_action_logging(
        self, action: str, reasoning: str, chapter: str
    ) -> str:
        """
        Suggest adding an action to major_plot_actions.

        Args:
            action: The action taken
            reasoning: Why the character took this action
            chapter: Chapter/story name

        Returns:
            Formatted suggestion string
        """
        return f"""SUGGESTION: Log this action to major_plot_actions:
{{
  "chapter": "{chapter}",
  "action": "{action}",
  "reasoning": "{reasoning}"
}}"""

    def suggest_character_development(
        self, new_behavior: str, context: str
    ) -> List[str]:
        """
        Suggest character file updates based on new behaviors.

        Args:
            new_behavior: Description of new behavior exhibited
            context: Context where behavior occurred

        Returns:
            List of development suggestions
        """
        suggestions = []

        # Check if this behavior suggests new personality traits
        if any(
            word in new_behavior.lower() for word in ["brave", "courageous", "bold"]
        ):
            suggestions.append(
                f"SUGGESTION: Consider adding personality trait: "
                f"'Shows courage in {context}'"
            )

        if any(
            word in new_behavior.lower() for word in ["cautious", "careful", "wary"]
        ):
            suggestions.append(
                f"SUGGESTION: Consider adding personality trait: "
                f"'Exercises caution when {context}'"
            )

        if any(word in new_behavior.lower() for word in ["lead", "command", "direct"]):
            suggestions.append(
                f"SUGGESTION: Consider adding personality trait: "
                f"'Takes leadership during {context}'"
            )

        # Check if this suggests new fears or motivations
        if any(
            word in new_behavior.lower() for word in ["afraid", "fear", "terrified"]
        ):
            suggestions.append(
                f"SUGGESTION: Consider adding to fears_weaknesses: "
                f"'Fear related to {context}'"
            )

        if any(word in new_behavior.lower() for word in ["protect", "save", "help"]):
            suggestions.append(
                f"SUGGESTION: Consider updating motivations to include "
                f"protecting others in {context}"
            )

        return suggestions

    def analyze_story_content(
        self, story_text: str, chapter_name: str
    ) -> Dict[str, List[str]]:
        """
        Analyze story content and provide comprehensive suggestions.

        Args:
            story_text: Full story text to analyze
            chapter_name: Name of the chapter/story

        Returns:
            Dictionary with categorized suggestions (relationships, plot_actions, etc.)
        """
        suggestions = {
            "relationships": [],
            "plot_actions": [],
            "character_development": [],
            "npc_creation": [],
        }

        lines = story_text.split("\n")

        for line in lines:
            # Look for CHARACTER: ACTION: REASONING: patterns
            if line.strip().startswith("CHARACTER:") and self.profile.name in line:
                # Extract action and reasoning from subsequent lines
                try:
                    idx = lines.index(line)
                    next_lines = lines[idx + 1 : idx + 4]
                    action_line = next(
                        (l for l in next_lines if l.strip().startswith("ACTION:")), ""
                    )
                    reasoning_line = next(
                        (l for l in next_lines if l.strip().startswith("REASONING:")),
                        "",
                    )

                    if action_line and reasoning_line:
                        action = action_line.replace("ACTION:", "").strip()
                        reasoning = reasoning_line.replace("REASONING:", "").strip()

                        # Suggest logging this action
                        suggestions["plot_actions"].append(
                            self.suggest_plot_action_logging(
                                action, reasoning, chapter_name
                            )
                        )

                        # Suggest character development updates
                        suggestions["character_development"].extend(
                            self.suggest_character_development(action, chapter_name)
                        )
                except (AttributeError, KeyError, ValueError):
                    pass

            # Look for mentions of other characters or potential NPCs
            if self.profile.name in line:
                # Find potential character interactions
                other_names = self._extract_character_names(line)
                for other_name in other_names:
                    if other_name != self.profile.name:
                        relationship_suggestion = self.suggest_relationship_update(
                            other_name, chapter_name
                        )
                        if relationship_suggestion:
                            suggestions["relationships"].append(relationship_suggestion)

        return suggestions

    def _extract_character_names(self, text: str) -> List[str]:
        """
        Extract potential character/NPC names from text (simple implementation).

        Args:
            text: Text to extract names from

        Returns:
            List of potential character names
        """
        # This is a basic implementation - could be enhanced with NLP
        words = text.split()
        potential_names = []

        for word in words:
            # Look for capitalized words that might be names
            if word.strip(",.:;!?").istitle() and len(word) > 2:
                potential_names.append(word.strip(",.:;!?"))

        return potential_names

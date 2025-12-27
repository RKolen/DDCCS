"""Story Consistency Analyzer

Analyzes story files for character behavioral consistency and narrative flow
across an entire story series. Checks character actions against their profiles
including backstory, personality traits, ideals, bonds, flaws, and plot actions.

Handles name variations (e.g., "Frodo Baggins" in JSON vs "Frodo" in story text).
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.stories.equipment_checker import (
    check_weapon_usage_consistency,
    format_equipment_issue,
)


class ConsistencyIssue(NamedTuple):
    """Represents a consistency issue found in analysis."""

    character_name: str
    story_file: str
    line_number: int
    action_text: str
    issue_type: str
    description: str
    suggestion: str
    score: int


class ActionContext(NamedTuple):
    """Context information for analyzing a character action."""

    character_name: str
    profile: Dict[str, Any]
    story_file: str
    line_num: int
    action_text: str


class CharacterNameMatcher:
    """Handles matching character names with variations in story text."""

    def find_mentions(self, text: str, character_name: str) -> List[Tuple[int, str]]:
        """Public method to find character mentions in text.

        Args:
            text: Story text to search
            character_name: Full character name

        Returns:
            List of (line_number, line_text) tuples where character is mentioned
        """
        return self.find_character_mentions(text, character_name)

    @staticmethod
    def build_name_patterns(full_name: str) -> List[str]:
        """Build regex patterns to match name variations.

        Args:
            full_name: Full character name (e.g., "Frodo Baggins")

        Returns:
            List of regex patterns to match variations
        """
        patterns = [re.escape(full_name)]

        # Add first name only pattern
        first_name = full_name.split()[0]
        patterns.append(r"\b" + re.escape(first_name) + r"\b")

        # Add last name only if multi-word name
        if " " in full_name:
            last_name = full_name.split()[-1]
            patterns.append(r"\b" + re.escape(last_name) + r"\b")

        return patterns

    @staticmethod
    def find_character_mentions(
        text: str, character_name: str
    ) -> List[Tuple[int, str]]:
        """Find all mentions of a character in text with line numbers.

        Args:
            text: Story text to search
            character_name: Full character name

        Returns:
            List of (line_number, line_text) tuples where character is mentioned
        """
        patterns = CharacterNameMatcher.build_name_patterns(character_name)
        mentions = []

        lines = text.split("\n")
        for line_num, line in enumerate(lines, start=1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    mentions.append((line_num, line.strip()))
                    break

        return mentions


class TacticalAnalyzer:
    """Analyzes tactical appropriateness of character actions."""

    def analyze(self, ctx: ActionContext) -> Optional[ConsistencyIssue]:
        """Public method to analyze tactical action.

        Args:
            ctx: Action context containing character and action details

        Returns:
            ConsistencyIssue if problem found, None otherwise
        """
        return self.analyze_tactical_action(ctx)

    @staticmethod
    def check_melee_preference(profile: Dict[str, Any], action_text: str) -> bool:
        """Check if melee weapon would be more appropriate.

        Args:
            profile: Character profile
            action_text: Action text

        Returns:
            True if melee would be better
        """
        weapons = profile.get("equipment", {}).get("weapons", [])
        has_melee = any("sword" in w.lower() or "blade" in w.lower() for w in weapons)

        close_range = any(
            word in action_text.lower()
            for word in ["close", "nearby", "beside", "next to", "defending"]
        )

        return has_melee and close_range

    @staticmethod
    def check_spell_preference(profile: Dict[str, Any]) -> bool:
        """Check if spells would be more appropriate.

        Args:
            profile: Character profile

        Returns:
            True if spells would be better
        """
        spells = profile.get("known_spells", [])
        return len(spells) > 0

    @staticmethod
    def check_stealth_preference(profile: Dict[str, Any]) -> bool:
        """Check if stealth approach would be more appropriate.

        Args:
            profile: Character profile

        Returns:
            True if stealth would be better
        """
        skills = profile.get("skills", {})
        return "Stealth" in skills and skills["Stealth"] > 5

    @staticmethod
    def _check_tactical_patterns(ctx: ActionContext) -> Optional[ConsistencyIssue]:
        """Check tactical patterns for character class.

        Args:
            ctx: Action context

        Returns:
            ConsistencyIssue if tactical problem found, None otherwise
        """
        action_lower = ctx.action_text.lower()
        char_class = ctx.profile.get("dnd_class", "").lower()

        # Decision table for tactical patterns
        tactical_checks = [
            (
                "ranger",
                ["drawing his bow", "draws his bow", "bow swiftly"],
                TacticalAnalyzer.check_melee_preference,
                "Consider melee combat with sword at close range",
                7,
            ),
            (
                "wizard",
                ["charges", "melee attack", "sword swing"],
                TacticalAnalyzer.check_spell_preference,
                "Wizards typically use spells rather than melee combat",
                6,
            ),
            (
                "rogue",
                ["charging forward", "frontal assault"],
                TacticalAnalyzer.check_stealth_preference,
                "Rogues typically use stealth and cunning rather than direct assault",
                7,
            ),
        ]

        for check_class, action_words, check_func, suggestion, score in tactical_checks:
            class_matches = char_class == check_class
            has_action_word = any(word in action_lower for word in action_words)
            if class_matches and has_action_word:
                is_melee_check = check_func.__name__ == "check_melee_preference"
                should_flag = (
                    check_func(ctx.profile, ctx.action_text)
                    if is_melee_check
                    else check_func(ctx.profile)
                )
                if should_flag:
                    desc = (
                        f"{ctx.character_name} ({char_class}) action may not be "
                        "tactically optimal"
                    )
                    return ConsistencyIssue(
                        character_name=ctx.character_name,
                        story_file=ctx.story_file,
                        line_number=ctx.line_num,
                        action_text=ctx.action_text,
                        issue_type="tactical",
                        description=desc,
                        suggestion=suggestion,
                        score=score,
                    )
        return None

    @staticmethod
    def check_equipment_availability(
        profile: Dict[str, Any], action_text: str
    ) -> Optional[tuple]:
        """Check if character has equipment mentioned in action.

        Args:
            profile: Character profile
            action_text: Action text

        Returns:
            Tuple of (equipment_name, issue_description) if missing, None otherwise
        """
        weapons = profile.get("equipment", {}).get("weapons", [])
        weapon_type = check_weapon_usage_consistency(action_text, weapons)

        if weapon_type:
            return format_equipment_issue(weapon_type)

        return None

    @staticmethod
    def analyze_tactical_action(ctx: ActionContext) -> Optional[ConsistencyIssue]:
        """Check tactical appropriateness of action.

        Args:
            ctx: Action context containing character and action details

        Returns:
            ConsistencyIssue if problem found, None otherwise
        """
        # First, check equipment availability - highest priority
        equipment_check = TacticalAnalyzer.check_equipment_availability(
            ctx.profile, ctx.action_text
        )
        if equipment_check:
            _, issue_desc = equipment_check
            available_weapons = ctx.profile.get("equipment", {}).get("weapons", [])
            return ConsistencyIssue(
                character_name=ctx.character_name,
                story_file=ctx.story_file,
                line_number=ctx.line_num,
                action_text=ctx.action_text,
                issue_type="equipment",
                description=f"{ctx.character_name} - {issue_desc}",
                suggestion=f"Character should use available equipment: "
                f"{', '.join(available_weapons)}",
                score=9,
            )

        # Then check tactical patterns
        return TacticalAnalyzer._check_tactical_patterns(ctx)


class PersonalityAnalyzer:
    """Analyzes personality consistency of character actions."""

    def analyze(self, ctx: ActionContext) -> Optional[ConsistencyIssue]:
        """Public method to analyze personality consistency.

        Args:
            ctx: Action context containing character and action details

        Returns:
            ConsistencyIssue if problem found, None otherwise
        """
        return self.analyze_personality_action(ctx)

    @staticmethod
    def analyze_personality_action(ctx: ActionContext) -> Optional[ConsistencyIssue]:
        """Check if action aligns with personality traits.

        Args:
            ctx: Action context containing character and action details

        Returns:
            ConsistencyIssue if problem found, None otherwise
        """
        flaws = ctx.profile.get("flaws", [])
        action_lower = ctx.action_text.lower()

        # Check for actions conflicting with flaws
        flaw_conflicts = [
            (
                ["fear", "afraid", "scared"],
                "recklessly charges",
                "Action seems reckless for character with fears",
            ),
            (
                ["burden", "weight"],
                "carelessly",
                "Action seems careless for burdened character",
            ),
        ]

        for flaw_words, action_word, description in flaw_conflicts:
            if any(any(fw in str(f).lower() for fw in flaw_words) for f in flaws):
                if action_word in action_lower:
                    suggestion = f"Consider character's flaws: {', '.join(flaws)}"
                    return ConsistencyIssue(
                        character_name=ctx.character_name,
                        story_file=ctx.story_file,
                        line_number=ctx.line_num,
                        action_text=ctx.action_text,
                        issue_type="personality",
                        description=description,
                        suggestion=suggestion,
                        score=8,
                    )

        return None


class AIAnalyzer:
    """AI-enhanced analysis of character actions."""

    def __init__(self, ai_client=None):
        """Initialize AI analyzer.

        Args:
            ai_client: Optional AI client for enhanced analysis
        """
        self.ai_client = ai_client

    def analyze(self, ctx: ActionContext) -> List[ConsistencyIssue]:
        """Public method to analyze with AI.

        Args:
            ctx: Action context containing character and action details

        Returns:
            List of AI-identified issues
        """
        return self.analyze_with_ai(ctx)

    def analyze_with_ai(self, ctx: ActionContext) -> List[ConsistencyIssue]:
        """Use AI to analyze action consistency.

        Args:
            ctx: Action context containing character and action details

        Returns:
            List of AI-identified issues
        """
        if not self.ai_client:
            return []

        prompt = self._build_prompt(ctx.character_name, ctx.profile, ctx.action_text)

        try:
            response = self.ai_client.generate_text(
                prompt=prompt, temperature=0.3, max_tokens=500
            )

            return self._parse_response(response, ctx)
        except (ValueError, AttributeError, OSError):
            return []

    def _build_prompt(
        self, character_name: str, profile: Dict[str, Any], action_text: str
    ) -> str:
        """Build AI prompt for action analysis.

        Args:
            character_name: Character name
            profile: Character profile
            action_text: Action text

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "Analyze this D&D character action for consistency:\n",
            f"Character: {character_name}",
            f"Class: {profile.get('dnd_class', 'Unknown')}",
            f"Level: {profile.get('level', 'Unknown')}",
        ]

        profile_fields = [
            ("backstory", "Backstory", 200),
            ("personality_traits", "Personality", None),
            ("ideals", "Ideals", None),
            ("bonds", "Bonds", None),
            ("flaws", "Flaws", None),
        ]

        for field_name, label, max_len in profile_fields:
            if profile.get(field_name):
                value = profile[field_name]
                if isinstance(value, list):
                    value = ", ".join(value)
                elif max_len:
                    value = value[:max_len]
                prompt_parts.append(f"{label}: {value}")

        prompt_parts.extend(
            [
                f"\nAction in Story:\n{action_text}",
                "\nProvide brief analysis:",
                "1. Is this tactically appropriate for their class?",
                "2. Does it match their personality and ideals?",
                "3. What would be more in-character?",
                "\nKeep response under 200 words.",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_response(
        self, response: str, ctx: ActionContext
    ) -> List[ConsistencyIssue]:
        """Parse AI response into consistency issues.

        Args:
            response: AI response text
            ctx: Action context containing character and action details

        Returns:
            List of parsed issues
        """
        suggestion_words = [
            "should",
            "could",
            "better",
            "instead",
            "consider",
            "more appropriate",
        ]

        if any(word in response.lower() for word in suggestion_words):
            return [
                ConsistencyIssue(
                    character_name=ctx.character_name,
                    story_file=ctx.story_file,
                    line_number=ctx.line_num,
                    action_text=ctx.action_text,
                    issue_type="ai_suggestion",
                    description="AI identified potential improvement",
                    suggestion=response[:300],
                    score=8,
                )
            ]

        return []


class StoryConsistencyAnalyzer:
    """Analyzes story consistency across a series."""

    def __init__(self, workspace_path: str, ai_client=None):
        """Initialize analyzer.

        Args:
            workspace_path: Root workspace path
            ai_client: Optional AI client for enhanced analysis
        """
        self.workspace_path = workspace_path
        self.ai_client = ai_client
        self.name_matcher = CharacterNameMatcher()
        self.tactical_analyzer = TacticalAnalyzer()
        self.personality_analyzer = PersonalityAnalyzer()
        self.ai_analyzer = AIAnalyzer(ai_client)

    def get_workspace_path(self) -> str:
        """Get the workspace path.

        Returns:
            Workspace path string
        """
        return self.workspace_path

    def analyze_series(
        self, series_name: str, story_files: List[str], party_members: List[str]
    ) -> Dict[str, Any]:
        """Analyze entire story series for consistency.

        Args:
            series_name: Name of the story series
            story_files: List of story filenames in order
            party_members: List of party member names

        Returns:
            Dictionary with analysis results
        """
        series_path = os.path.join(
            self.workspace_path, "game_data", "campaigns", series_name
        )

        profiles = self._load_character_profiles(party_members)
        all_issues = []
        story_analyses = []

        for story_file in story_files:
            story_path = os.path.join(series_path, story_file)
            if not file_exists(story_path):
                continue

            story_text = read_text_file(story_path)
            if story_text is None:
                continue
            story_issues = self._analyze_story_file(story_file, story_text, profiles)

            all_issues.extend(story_issues)
            story_analyses.append({"filename": story_file, "issues": story_issues})

        report_path = self._generate_report(
            series_name, series_path, story_analyses, profiles
        )

        return {
            "series_name": series_name,
            "stories_analyzed": len(story_files),
            "total_issues": len(all_issues),
            "report_path": report_path,
            "issues": all_issues,
        }

    def _load_character_profiles(
        self, party_members: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Load character profiles for party members.

        Args:
            party_members: List of party member names

        Returns:
            Dictionary mapping character names to their profiles
        """
        profiles = {}

        for member_name in party_members:
            char_file = self._find_character_file(member_name)
            if char_file:
                profile = self._load_character_file(char_file)
                if profile:
                    profiles[member_name] = profile

        return profiles

    def _find_character_file(self, character_name: str) -> Optional[str]:
        """Find character JSON file for given character name.

        Args:
            character_name: Character name to search for

        Returns:
            Full path to character file, or None if not found
        """
        chars_dir = os.path.join(self.workspace_path, "game_data", "characters")
        if not os.path.isdir(chars_dir):
            return None

        # Try exact filename match first
        normalized_name = character_name.lower().replace(" ", "_")
        candidate = os.path.join(chars_dir, f"{normalized_name}.json")
        if file_exists(candidate):
            return candidate

        # Try first name only
        first_name = character_name.split()[0].lower()
        candidate = os.path.join(chars_dir, f"{first_name}.json")
        if file_exists(candidate):
            return candidate

        return None

    def _load_character_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load character JSON file.

        Args:
            filepath: Path to character JSON file

        Returns:
            Character data dictionary, or None on error
        """
        try:
            with open(filepath, "r", encoding="utf-8") as file_handle:
                return json.load(file_handle)
        except (OSError, ValueError):
            return None

    def _analyze_story_file(
        self, story_file: str, story_text: str, profiles: Dict[str, Dict[str, Any]]
    ) -> List[ConsistencyIssue]:
        """Analyze single story file for consistency issues.

        Args:
            story_file: Story filename
            story_text: Story text content
            profiles: Character profiles dictionary

        Returns:
            List of consistency issues found
        """
        issues = []

        for char_name, profile in profiles.items():
            char_issues = self._analyze_character_in_story(
                char_name, profile, story_file, story_text
            )
            issues.extend(char_issues)

        return issues

    def _analyze_character_in_story(
        self,
        character_name: str,
        profile: Dict[str, Any],
        story_file: str,
        story_text: str,
    ) -> List[ConsistencyIssue]:
        """Analyze character's actions in a story file.

        Args:
            character_name: Character name
            profile: Character profile data
            story_file: Story filename
            story_text: Story text content

        Returns:
            List of consistency issues for this character
        """
        issues = []

        mentions = self.name_matcher.find_character_mentions(story_text, character_name)

        for line_num, line_text in mentions:
            ctx = ActionContext(
                character_name, profile, story_file, line_num, line_text
            )
            char_issues = self._check_action_consistency(ctx)
            issues.extend(char_issues)

        return issues

    def _check_action_consistency(self, ctx: ActionContext) -> List[ConsistencyIssue]:
        """Check if action is consistent with character profile.

        Args:
            ctx: Action context containing character and action details

        Returns:
            List of issues found
        """
        issues = []

        tactical_issue = self.tactical_analyzer.analyze_tactical_action(ctx)
        if tactical_issue:
            issues.append(tactical_issue)

        personality_issue = self.personality_analyzer.analyze_personality_action(ctx)
        if personality_issue:
            issues.append(personality_issue)

        if self.ai_client:
            ai_issues = self.ai_analyzer.analyze_with_ai(ctx)
            issues.extend(ai_issues)

        return issues

    def _generate_report(
        self,
        series_name: str,
        series_path: str,
        story_analyses: List[Dict[str, Any]],
        profiles: Dict[str, Dict[str, Any]],
    ) -> str:
        """Generate analysis report markdown file.

        Args:
            series_name: Series name
            series_path: Path to series folder
            story_analyses: List of per-story analyses
            profiles: Character profiles

        Returns:
            Path to generated report file
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        report_filename = f"series_analysis_{timestamp}.md"
        report_path = os.path.join(series_path, report_filename)

        lines = [
            f"# Story Consistency Analysis: {series_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Stories Analyzed: {len(story_analyses)}",
            f"Party Members: {', '.join(profiles.keys())}",
            "",
            "## Overall Summary",
            "",
        ]

        total_issues = sum(len(sa["issues"]) for sa in story_analyses)
        lines.append(f"- Total issues found: {total_issues}")
        lines.append(f"- Characters analyzed: {len(profiles)}")
        lines.append("")

        for story_analysis in story_analyses:
            lines.extend(self._format_story_section(story_analysis, profiles))

        report_content = "\n".join(lines)
        write_text_file(report_path, report_content)

        return report_path

    def _format_story_section(
        self, story_analysis: Dict[str, Any], profiles: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Format a single story's analysis section.

        Args:
            story_analysis: Analysis data for one story
            profiles: Character profiles

        Returns:
            List of formatted lines
        """
        lines = [f"## Story: {story_analysis['filename']}", ""]

        issues = story_analysis["issues"]
        if not issues:
            lines.append("No consistency issues detected.")
            lines.append("")
            return lines

        issues_by_char: Dict[str, List[ConsistencyIssue]] = {}
        for issue in issues:
            if issue.character_name not in issues_by_char:
                issues_by_char[issue.character_name] = []
            issues_by_char[issue.character_name].append(issue)

        for char_name in sorted(issues_by_char.keys()):
            char_issues = issues_by_char[char_name]
            lines.extend(
                self._format_character_issues(char_name, char_issues, profiles)
            )

        lines.append("")
        return lines

    def _format_character_issues(
        self,
        character_name: str,
        issues: List[ConsistencyIssue],
        profiles: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Format issues for a single character.

        Args:
            character_name: Character name
            issues: List of issues for this character
            profiles: Character profiles

        Returns:
            List of formatted lines
        """
        lines = [f"### {character_name}", ""]

        profile = profiles.get(character_name, {})
        if profile:
            char_class = profile.get("dnd_class", "Unknown")
            level = profile.get("level", "?")
            lines.append(f"**Class:** {char_class} (Level {level})")
            lines.append("")

        for issue in issues:
            lines.extend(
                [
                    f"**Line {issue.line_number}:** {issue.action_text[:100]}...",
                    "",
                    f"**Issue Type:** {issue.issue_type.title()}",
                    f"**Analysis:** {issue.description}",
                    f"**Suggestion:** {issue.suggestion}",
                    f"**Consistency Score:** {issue.score}/10",
                    "",
                    "---",
                    "",
                ]
            )

        return lines

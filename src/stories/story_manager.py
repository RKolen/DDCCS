"""
Story Management System for VSCode Integration
Manages markdown story files and character consultant integration.
"""

import os
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.characters.consultants.character_consultants import CharacterConsultant, CharacterProfile
from src.characters.character_sheet import DnDClass
from src.validation.character_validator import validate_character_file
USE_CHARACTER_VALIDATION = True


class StoryManager:
    """Manages the 001<storyname>.md story sequence system."""

    # Allowed folder suffixes for story series
    VALID_SUFFIXES = ["_Campaign", "_Quest", "_Story", "_Adventure"]

    def __init__(self, workspace_path: str, ai_client=None):
        self.workspace_path = workspace_path
        self.stories_path = workspace_path
        self.characters_path = os.path.join(workspace_path, "characters")
        self.consultants = {}
        self.ai_client = ai_client  # Optional AI client for character consultants

        # Ensure directories exist
        os.makedirs(self.characters_path, exist_ok=True)

        # Load existing characters
        self.load_characters()

    def _validate_series_name(self, series_name: str) -> str:
        """
        Validate and fix series name to ensure it ends with a valid suffix.
        z
        Args:
            series_name: The proposed series name

        Returns:
            Valid series name with proper suffix

        Raises:
            ValueError: If series name cannot be made valid
        """
        # Check if already has valid suffix
        for suffix in self.VALID_SUFFIXES:
            if series_name.endswith(suffix):
                return series_name

        # If no valid suffix, suggest adding _Quest as default
        suggested_name = f"{series_name}_Quest"
        raise ValueError(
            f"Series name '{series_name}' must end with one of: {', '.join(self.VALID_SUFFIXES)}.\n"
            f"Suggestion: Use '{suggested_name}' instead."
        )

    def load_characters(self):
        """Load all character profiles and create consultants."""
        if not os.path.exists(self.characters_path):
            return

        use_validation = USE_CHARACTER_VALIDATION
        if not use_validation:
            print("Warning: character_validator module not found, skipping validation")

        for filename in os.listdir(self.characters_path):
            # Skip template and example files
            if (
                filename.endswith(".json")
                and not filename.startswith("class.example")
                and not filename.endswith(".example.json")
                and not filename.startswith("template")
            ):

                filepath = os.path.join(self.characters_path, filename)

                # Validate character JSON before loading
                if use_validation:
                    is_valid, errors = validate_character_file(filepath)
                    if not is_valid:
                        print(f"✗ Validation failed for {filename}:")
                        for error in errors:
                            print(f"  - {error}")
                        continue

                try:
                    profile = CharacterProfile.load_from_file(filepath)
                    self.consultants[profile.name] = CharacterConsultant(
                        profile, ai_client=self.ai_client
                    )
                    if use_validation:
                        print(f"✓ Loaded and validated: {filename}")
                except (OSError, IOError) as e:
                    print(f"Warning: Could not load character {filename}: {e}")

    def create_default_party(self) -> List[CharacterProfile]:
        """Create default character profiles for all 12 classes."""
        default_profiles = []

        class_defaults = {
            DnDClass.BARBARIAN: {
                "name": "Thorgar Ironbreaker",
                "personality": "Hot-tempered but fiercely loyal",
                "background": (
                    "A tribal warrior seeking to prove their worth "
                    "in civilized lands."
                ),
            },
            DnDClass.BARD: {
                "name": "Melody Brightstring",
                "personality": "Charismatic storyteller who loves attention",
                "background": (
                    "A traveling performer collecting stories and songs "
                    "from across the realm."
                ),
            },
            DnDClass.CLERIC: {
                "name": "Brother Marcus Lightbringer",
                "personality": "Devout and compassionate healer",
                "background": (
                    "A devoted priest on a sacred mission to spread "
                    "their deity's influence."
                ),
            },
            DnDClass.DRUID: {
                "name": "Willow Moonwhisper",
                "personality": "Wise but distrustful of civilization",
                "background": (
                    "A guardian of ancient forests who reluctantly "
                    "ventures into towns."
                ),
            },
            DnDClass.FIGHTER: {
                "name": "Sir Gareth Steelhand",
                "personality": "Disciplined and honor-bound",
                "background": (
                    "A seasoned knight seeking to uphold justice and "
                    "protect the innocent."
                ),
            },
            DnDClass.MONK: {
                "name": "Zen Shadowstep",
                "personality": "Contemplative and disciplined",
                "background": (
                    "A seeker of enlightenment who has left their "
                    "monastery to learn from the world."
                ),
            },
            DnDClass.PALADIN: {
                "name": "Aurelia Dawnbreaker",
                "personality": "Righteous and inspiring",
                "background": (
                    "A holy warrior bound by sacred oaths to fight evil "
                    "wherever it lurks."
                ),
            },
            DnDClass.RANGER: {
                "name": "Finn Swiftarrow",
                "personality": "Independent and observant",
                "background": (
                    "A skilled tracker who protects civilization's "
                    "borders from monsters."
                ),
            },
            DnDClass.ROGUE: {
                "name": "Shadow Quickfingers",
                "personality": "Cautious and opportunistic",
                "background": (
                    "A reformed thief using their skills for the "
                    "greater good (mostly)."
                ),
            },
            DnDClass.SORCERER: {
                "name": "Ember Starborn",
                "personality": "Emotional and intuitive",
                "background": (
                    "A young magic-wielder learning to control their "
                    "inherited arcane power."
                ),
            },
            DnDClass.WARLOCK: {
                "name": "Raven Darkpact",
                "personality": "Mysterious and driven",
                "background": (
                    "Bound by an otherworldly pact, seeking to fulfill "
                    "their patron's agenda."
                ),
            },
            DnDClass.WIZARD: {
                "name": "Elara Scrollkeeper",
                "personality": "Scholarly and methodical",
                "background": (
                    "A learned scholar fascinated by the mysteries of "
                    "arcane magic."
                ),
            },
        }

        for dnd_class, defaults in class_defaults.items():
            profile = CharacterProfile(
                name=defaults["name"],
                character_class=dnd_class,
                level=3,  # Starting at level 3 for more interesting abilities
                background_story=defaults["background"],
                personality_summary=defaults["personality"],
                motivations=["Serve the party's needs", "Grow in power and wisdom"],
                goals=["Complete the current adventure", "Discover personal destiny"],
                decision_making_style=f"As a {dnd_class.value} would - see class guidelines",
            )
            default_profiles.append(profile)

        return default_profiles

    def save_character_profile(self, profile: CharacterProfile):
        """Save a character profile and update consultant."""
        filename = f"{profile.name.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.characters_path, filename)
        profile.save_to_file(filepath)

        # Update consultant with AI client
        self.consultants[profile.name] = CharacterConsultant(
            profile, ai_client=self.ai_client
        )
        print(f"✅ Saved character profile: {profile.name}")

    def get_existing_stories(self) -> List[str]:
        """Get existing story files in the root directory (legacy stories)."""
        story_files = []
        for filename in os.listdir(self.stories_path):
            if re.match(r"\d{3}.*\.md$", filename):
                story_files.append(filename)

        return sorted(story_files)

    def get_story_series(self) -> List[str]:
        """Get available story series (folders with numbered stories)."""
        series_folders = []
        for item in os.listdir(self.stories_path):
            item_path = os.path.join(self.stories_path, item)
            if (
                os.path.isdir(item_path)
                and not item.startswith(".")
                and item != "characters"
                and item != "npcs"
                and item != "__pycache__"
            ):
                # Check if folder contains numbered story files
                if any(
                    re.match(r"\d{3}.*\.md$", f)
                    for f in os.listdir(item_path)
                    if f.endswith(".md")
                ):
                    series_folders.append(item)

        return sorted(series_folders)

    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """Get story files within a specific series folder."""
        series_path = os.path.join(self.stories_path, series_name)
        if not os.path.exists(series_path):
            return []

        story_files = []
        for filename in os.listdir(series_path):
            if re.match(r"\d{3}.*\.md$", filename):
                story_files.append(filename)

        return sorted(story_files)

    def get_story_files(self) -> List[str]:
        """Get all story files in sequence order (legacy method for backward compatibility)."""
        return self.get_existing_stories()

    def create_new_story_series(
        self, series_name: str, first_story_name: str, description: str = ""
    ) -> str:
        """
        Create a new story series in its own folder.

        Series name MUST end with: _Campaign, _Quest, _Story, or _Adventure
        """
        # Validate series name has proper suffix
        validated_name = self._validate_series_name(series_name)

        # Create series folder
        clean_series_name = re.sub(r"[^a-zA-Z0-9_-]", "_", validated_name)
        series_path = os.path.join(self.stories_path, clean_series_name)
        os.makedirs(series_path, exist_ok=True)

        # Create first story in series
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", first_story_name)
        filename = f"001_{clean_name}.md"
        filepath = os.path.join(series_path, filename)

        # Create story template
        template = self._create_story_template(first_story_name, description)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"OK Created new story series: {clean_series_name}")
        print(f"OK Created first story: {filename}")
        return filepath

    def create_story_in_series(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """Create a new story in an existing series."""
        series_path = os.path.join(self.stories_path, series_name)
        if not os.path.exists(series_path):
            raise ValueError(f"Story series '{series_name}' does not exist")

        # Get existing stories in series to determine next number
        existing_stories = self.get_story_files_in_series(series_name)

        if existing_stories:
            last_number = max(int(f[:3]) for f in existing_stories)
            next_number = last_number + 1
        else:
            next_number = 1

        # Create filename
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
        filename = (
            f"{next_number:03d}_{clean_name}.md"
        )
        filepath = os.path.join(series_path, filename)

        # Create story template
        template = self._create_story_template(story_name, description)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"OK Created new story in {series_name}: {filename}")
        return filepath

    def create_new_story(self, story_name: str, description: str = "") -> str:
        """Create a new story file with the next sequence number "
        "(for existing/legacy stories in root)."""
        existing_stories = self.get_existing_stories()

        # Determine next sequence number
        if existing_stories:
            last_number = max(int(f[:3]) for f in existing_stories)
            next_number = last_number + 1
        else:
            next_number = 1

        # Create filename
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(self.stories_path, filename)

        # Create story template
        template = self._create_story_template(story_name, description)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"OK Created new story: {filename}")
        return filepath

    def _create_story_template(self, story_name: str, description: str) -> str:
        """Create a markdown template for a new story using story_template.md as base."""
        template_path = os.path.join(
            self.workspace_path, "templates", "story_template.md"
        )
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            # Optionally inject story_name and description at the top
            header = (
                f"# {story_name}\n\n**Created:** "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"**Description:** {description}\n\n---\n"
            )
            return header + template
        # Fallback to a minimal template
        return (
            f"# {story_name}\n\n**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Description:** {description}\n\n---\n\n## DC Suggestions Needed\n"
            "*List any actions that need DC suggestions from the character consultants.*\n\n"
            "## Combat Summary\n*Paste combat prompts*\n\n"
            "## Story Narrative\n*The final narrative version of events will go here.*\n"
        )

    def analyze_story_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a story file for character actions and consistency."""
        if not os.path.exists(filepath):
            return {"error": "Story file not found"}

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract character actions
        character_actions = self._extract_character_actions(content)

        # Get consultant analysis for each character
        consultant_analyses = {}
        for character_name, actions in character_actions.items():
            if character_name in self.consultants:
                consultant = self.consultants[character_name]
                analysis = consultant.analyze_story_consistency(content, actions)
                consultant_analyses[character_name] = analysis

        # Extract DC requests
        dc_requests = self._extract_dc_requests(content)
        dc_suggestions = {}
        for request in dc_requests:
            suggestions = self._get_dc_suggestions_for_request(request)
            dc_suggestions[request] = suggestions

        return {
            "story_file": os.path.basename(filepath),
            "character_actions": character_actions,
            "consultant_analyses": consultant_analyses,
            "dc_requests": dc_requests,
            "dc_suggestions": dc_suggestions,
            "overall_consistency": self._calculate_overall_consistency(
                consultant_analyses
            ),
        }

    def _extract_character_actions(self, content: str) -> Dict[str, List[str]]:
        """Extract character actions from story content."""
        actions = {}

        # Look for Character Action Log sections
        action_pattern = (
            r"CHARACTER:\s*([^\n]+)\nACTION:\s*([^\n]+)"
            r"(?:\nREASONING:\s*([^\n]+))?"
        )
        matches = re.findall(action_pattern, content, re.MULTILINE)

        for match in matches:
            character = match[0].strip()
            action = match[1].strip()
            reasoning = match[2].strip() if len(match) > 2 else ""

            if character not in actions:
                actions[character] = []

            action_with_reasoning = (
                f"{action} (Reasoning: {reasoning})" if reasoning else action
            )
            actions[character].append(action_with_reasoning)

        # Also look for narrative mentions of characters
        for character_name in self.consultants:
            if character_name in content and character_name not in actions:
                # Find sentences mentioning this character
                sentences = re.findall(
                    f"[^.!?]*{re.escape(character_name)}[^.!?]*[.!?]", content
                )
                if sentences:
                    actions[character_name] = sentences[:3]  # Limit to first 3 mentions

        return actions

    def _extract_dc_requests(self, content: str) -> List[str]:
        """Extract DC suggestion requests from story content."""
        # Look for DC Suggestions Needed section
        dc_section_match = re.search(
            r"## DC Suggestions Needed\\s*\\n([^#]*)", content, re.MULTILINE
        )
        if not dc_section_match:
            return []

        dc_section = dc_section_match.group(1)

        # Extract individual requests (lines that aren't empty or just whitespace)
        requests = []
        for line in dc_section.split("\\n"):
            line = line.strip()
            if line and not line.startswith("*") and line != "*":
                # Remove markdown formatting
                line = re.sub(r"[*_`]", "", line)
                requests.append(line)

        return requests

    def _get_dc_suggestions_for_request(
        self, request: str
    ) -> Dict[str, Any]:
        """Get DC suggestions from relevant character consultants."""
        suggestions = {}

        # Try to identify which character is attempting the action
        for character_name, consultant in self.consultants.items():
            if character_name.lower() in request.lower():
                suggestion = consultant.suggest_dc_for_action(request)
                suggestions[character_name] = suggestion
                break

        # If no specific character found, get suggestions from most relevant class
        if not suggestions:
            # Use a general consultant (first available)
            if self.consultants:
                first_consultant = next(iter(self.consultants.values()))
                suggestion = first_consultant.suggest_dc_for_action(request)
                suggestions["General"] = suggestion

        return suggestions

    def _calculate_overall_consistency(
        self, analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall consistency metrics."""
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
        """Convert overall score to rating."""
        if score >= 0.8:
            return "Excellent - All characters very consistent"
        if score >= 0.6:
            return "Good - Most characters consistent"
        if score >= 0.4:
            return "Fair - Some character inconsistencies"
        if score >= 0.2:
            return "Poor - Multiple character issues"
        return "Very Poor - Major character problems"

    def update_story_with_analysis(self, filepath: str, analysis: Dict[str, Any]):
        """Update story file with consultant analysis."""
        if not os.path.exists(filepath):
            return

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Generate consultant notes section
        consultant_notes = self._generate_consultant_notes(analysis)

        # Generate consistency analysis section
        consistency_section = self._generate_consistency_section(analysis)

        # Replace or add the consultant sections
        content = self._update_section(
            content, "Character Consultant Notes", consultant_notes
        )
        content = self._update_section(
            content, "Consistency Analysis", consistency_section
        )

        # Write back to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(
            (
                f"✅ Updated story file with consultant analysis: "
                f"{os.path.basename(filepath)}"
            )
        )

    def _generate_consultant_notes(self, analysis: Dict[str, Any]) -> str:
        """Generate the consultant notes section content."""
        notes = []

        # DC Suggestions
        if analysis.get("dc_suggestions"):
            notes.append("### DC Suggestions\\n")
            for request, suggestions in analysis["dc_suggestions"].items():
                notes.append(f"**{request}:**\\n")
                for character, suggestion in suggestions.items():
                    notes.append(
                        (
                            f"- {character}: DC {suggestion['suggested_dc']} "
                            f"({suggestion['reasoning']})"
                        )
                    )
                    if suggestion.get("alternative_approaches"):
                        notes.append(
                            f"  - Alternatives: {', '.join(suggestion['alternative_approaches'])}"
                        )
                notes.append("")

        # Character-specific consultant advice
        if analysis.get("consultant_analyses"):
            notes.append("### Character Behavior Guidance\\n")
            for character, char_analysis in analysis["consultant_analyses"].items():
                if char_analysis.get("suggestions"):
                    notes.append(f"**{character}:**")
                    for suggestion in char_analysis["suggestions"]:
                        notes.append(f"- {suggestion}")
                    notes.append("")

        return "\\n".join(notes) if notes else "*No consultant notes generated.*"

    def _generate_consistency_section(self, analysis: Dict[str, Any]) -> str:
        """Generate the consistency analysis section content."""
        sections = []

        # Overall summary
        overall = analysis.get("overall_consistency", {})
        sections.append(f"### Overall Consistency: {overall.get('rating', 'Unknown')}")
        sections.append(f"**Score:** {overall.get('score', 0)}/1.0")
        sections.append(
            f"**Summary:** {overall.get('summary', 'No analysis available')}"
        )
        sections.append("")

        # Individual character analyses
        if analysis.get("consultant_analyses"):
            sections.append("### Individual Character Analysis\\n")

            for character, char_analysis in analysis["consultant_analyses"].items():
                sections.append(
                    f"**{character}** - {char_analysis.get('overall_rating', 'Unknown')}"
                )
                sections.append(
                    f"Score: {char_analysis.get('consistency_score', 0)}/1.0\\n"
                )

                if char_analysis.get("positive_notes"):
                    sections.append("✅ **Positive aspects:**")
                    for note in char_analysis["positive_notes"]:
                        sections.append(f"- {note}")
                    sections.append("")

                if char_analysis.get("issues"):
                    sections.append("⚠️ **Issues to address:**")
                    for issue in char_analysis["issues"]:
                        sections.append(f"- {issue}")
                    sections.append("")

                sections.append("---\\n")

        return (
            "\\n".join(sections) if sections else "*No consistency analysis available.*"
        )

    def _update_section(self, content: str, section_name: str, new_content: str) -> str:
        """Update or add a section in the markdown content."""
        section_pattern = f"## {re.escape(section_name)}\\s*\\n([^#]*)"

        if re.search(section_pattern, content):
            # Replace existing section
            replacement = f"## {section_name}\\n{new_content}\\n\\n"
            content = re.sub(section_pattern, replacement, content)
        else:
            # Add section at the end
            content += f"\\n\\n## {section_name}\\n{new_content}\\n"

        return content

    def get_character_list(self) -> List[str]:
        """Get list of all character names."""
        return list(self.consultants.keys())

    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """Get a character's profile."""
        consultant = self.consultants.get(character_name)
        return consultant.profile if consultant else None

    def suggest_character_reaction(
        self, character_name: str, situation: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get character reaction suggestion."""
        if character_name not in self.consultants:
            return {"error": f"Character {character_name} not found"}

        consultant = self.consultants[character_name]
        return consultant.suggest_reaction(situation, context)

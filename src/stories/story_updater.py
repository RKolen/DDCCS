"""
Story Updater Component.

Handles updating story files with analysis results, including consultant notes,
consistency sections, combat narratives, and AI-generated continuations.
"""

import os
import json
from typing import Dict, Any, List
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.utils.markdown_utils import update_markdown_section
from src.utils.story_formatting_utils import (
    generate_consultant_notes,
    generate_consistency_section
)
from src.npcs.npc_auto_detection import detect_npc_suggestions
from src.stories.hooks_and_analysis import (
    create_story_hooks_file,
    convert_ai_hooks_to_list
)
from src.stories.session_results_manager import (
    StorySession,
    create_session_results_file
)
from src.stories.story_ai_generator import (
    generate_session_results_from_story,
    generate_story_hooks_from_content
)
from src.cli.party_config_manager import load_party_with_profiles


class ContinuationConfig:
    """Configuration builder for story continuation operations."""

    def __init__(self):
        """Initialize empty config."""
        self.filepath = None
        self.continuation = None
        self.campaign_dir = None
        self.workspace_path = None
        self.ai_client = None

    def set_paths(
        self, filepath: str, campaign_dir: str, workspace_path: str
    ) -> 'ContinuationConfig':
        """Set file and directory paths.

        Args:
            filepath: Path to the story file
            campaign_dir: Path to the campaign directory
            workspace_path: Path to the workspace root

        Returns:
            Self for method chaining
        """
        self.filepath = filepath
        self.campaign_dir = campaign_dir
        self.workspace_path = workspace_path
        return self

    def set_content(self, continuation: str) -> 'ContinuationConfig':
        """Set continuation content.

        Args:
            continuation: AI-generated continuation text

        Returns:
            Self for method chaining
        """
        self.continuation = continuation
        return self

    def set_ai_client(self, ai_client) -> 'ContinuationConfig':
        """Set optional AI client.

        Args:
            ai_client: Optional AI client for analysis

        Returns:
            Self for method chaining
        """
        self.ai_client = ai_client
        return self

    def validate(self) -> bool:
        """Validate that all required fields are set.

        Returns:
            True if valid, False otherwise
        """
        return all([
            self.filepath,
            self.continuation,
            self.campaign_dir,
            self.workspace_path,
        ])


class StoryUpdater:
    """Updates story files with consultant analysis and consistency notes."""

    def update_story_with_analysis(self, filepath: str, analysis: Dict[str, Any]):
        """
        Update story file with consultant analysis.

        Args:
            filepath: Path to the story file
            analysis: Analysis results dictionary
        """
        if not file_exists(filepath):
            return

        content = read_text_file(filepath)

        # Generate sections using formatting utilities
        consultant_notes = generate_consultant_notes(analysis)
        consistency_section = generate_consistency_section(analysis)

        # Replace or add the consultant sections
        content = update_markdown_section(
            content, "Character Consultant Notes", consultant_notes
        )
        content = update_markdown_section(
            content, "Consistency Analysis", consistency_section
        )

        # Write back to file
        write_text_file(filepath, content)

        print(
            f"[SUCCESS] Updated story file with consultant analysis: "
            f"{os.path.basename(filepath)}"
        )

    def append_combat_narrative(self, filepath: str, narrative: str):
        """
        Append combat narrative to story file.

        Args:
            filepath: Path to the story file
            narrative: Combat narrative text to append
        """
        if not file_exists(filepath):
            return

        content = read_text_file(filepath)

        # Add combat section
        combat_section = f"\n\n## Combat Scene\n\n{narrative}\n"
        content += combat_section

        write_text_file(filepath, content)

        print(
            f"[SUCCESS] Appended combat narrative to story file: "
            f"{os.path.basename(filepath)}"
        )

    def append_ai_continuation(self, config: ContinuationConfig) -> bool:
        """Append AI-generated continuation to story and supporting files.

        Cleans existing content, appends continuation with section title, and
        generates story_hooks and session_results files with NPC detection.

        Args:
            config: ContinuationConfig with filepath, continuation text,
                   campaign_dir, workspace_path, and optional ai_client

        Returns:
            True if successful, False if an error occurred
        """
        if not config.validate():
            print("[ERROR] Invalid continuation config: missing required fields")
            return False

        return self._append_continuation(config)

    def _append_continuation(self, config: ContinuationConfig) -> bool:
        """Append continuation using config object.

        Args:
            config: ContinuationConfig with all parameters

        Returns:
            True if successful, False if an error occurred
        """
        if not file_exists(config.filepath):
            return False

        try:
            current_content = read_text_file(config.filepath)
            cleaned_content = self._clean_story_content(current_content)
            continuation_title = self._extract_narrative_title(
                config.continuation
            )

            new_content = self._build_story_content_with_continuation(
                cleaned_content, continuation_title, config.continuation
            )

            write_text_file(config.filepath, new_content)

            self._generate_supporting_files(
                config.filepath, config.campaign_dir,
                config.workspace_path, ai_client=config.ai_client
            )

            print(
                f"[SUCCESS] Appended AI continuation to story file: "
                f"{os.path.basename(config.filepath)}"
            )
            return True

        except OSError as e:
            print(f"[ERROR] Failed to update story: {e}")
            return False

    def _clean_story_content(self, content: str) -> str:
        """Remove duplicate headers and metadata from story content.

        Args:
            content: Raw story content with potential duplicates

        Returns:
            Cleaned story content
        """
        lines = content.split("\n")
        cleaned_lines = []
        seen_header = False

        for line in lines:
            # Skip duplicate headers
            if line.startswith("# "):
                if seen_header:
                    continue
                seen_header = True
                cleaned_lines.append(line)
            # Skip duplicate metadata
            elif line.startswith("**Created:**") or \
                 line.startswith("**Description:**"):
                if cleaned_lines and any(
                    "**Created:**" in l or "**Description:**" in l
                    for l in cleaned_lines[-5:]
                ):
                    continue
                cleaned_lines.append(line)
            # Skip duplicate separators
            elif line.strip() == "---":
                if cleaned_lines and cleaned_lines[-1].strip() == "---":
                    continue
                cleaned_lines.append(line)
            # Keep other lines
            else:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _filter_template_text(self, content: str) -> str:
        """Remove template guidance, keep only story content.

        Strips template sections and guidance keywords that should not appear
        in finalized story narratives. Also removes trailing separators and
        excessive blank lines.

        Args:
            content: Story content that may include template text

        Returns:
            Content with template text removed
        """
        lines = content.split("\n")
        kept_lines = []
        skip_until_next_section = False

        template_sections = [
            "Scene Title",
            "Story Content",
            "Character Development",
            "DC Suggestions",
            "Combat Summary",
            "Story Narrative (Final)",
        ]

        template_keywords = [
            "[Add",
            "[Paste",
            "[Clean",
            "[Include",
            "[Write your narrative",
            "Write pure narrative",
            "Focus on:",
            "Character actions and dialogue",
            "Environmental descriptions",
            "Plot developments",
            "NPC interactions",
            "Example narrative",
            "For character",
            "For DC",
            "- CHARACTER/",
            "- Personality trait",
            "- Relationship developments",
            "- Major plot",
            "- Character consistency",
            "`character_development",
            "`story_dc_suggestions",
        ]

        for line in lines:
            # Detect start of template section
            if line.startswith("## "):
                is_template = any(x in line for x in template_sections)
                if is_template:
                    skip_until_next_section = True
                    continue

                skip_until_next_section = False
                kept_lines.append(line)
            # Skip template content while in template section
            elif skip_until_next_section:
                if line.startswith("## "):
                    skip_until_next_section = False
                    kept_lines.append(line)
                continue
            # Skip lines containing template keywords
            elif any(keyword in line for keyword in template_keywords):
                continue
            # Keep narrative content
            else:
                kept_lines.append(line)

        # Post-process: remove trailing separators and clean up blank lines
        result = "\n".join(kept_lines).strip()

        # Remove trailing separator lines
        while result.endswith("\n---"):
            result = result[:-4].rstrip()

        # Clean up excessive consecutive blank lines (keep max 2)
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result

    def _extract_narrative_title(self, text: str) -> str:
        """Extract a narrative title from the first line of text.

        Attempts to identify location names or key subjects from the opening
        text and constructs an appropriate section title.

        Args:
            text: The continuation text

        Returns:
            A narrative title for the section (e.g., "The Prancing Pony")
        """
        if not text or not text.strip():
            return "Story Continuation"

        # Get first line and extract location/subject
        first_line = text.split("\n")[0].strip()

        # Common location patterns
        locations = [
            "tavern", "inn", "castle", "village", "town", "city", "forest",
            "dungeon", "cave", "tower", "temple", "shrine", "market",
            "garden", "hall", "chamber", "room", "passage", "throne",
        ]

        # Try to find a location name (capitalize first noun before location)
        words = first_line.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip(".,!?;:")
            if word_lower in locations:
                # Try to get the name before the location
                if i > 0:
                    prev_word = words[i - 1].strip(".,!?;:")
                    if prev_word and prev_word[0].isupper():
                        return f"The {prev_word} {word_lower.capitalize()}"
                return f"The {word_lower.capitalize()}"

        # Fallback: use first few capitalized words
        capitalized = [
            w.strip(".,!?;:") for w in words
            if w and w[0].isupper() and w.lower() not in ["a", "an", "the"]
        ]
        if capitalized:
            return " ".join(capitalized[:3])

        return "Story Continuation"

    def _build_story_content_with_continuation(
        self, cleaned_content: str, title: str, continuation: str
    ) -> str:
        """Build story content with template removal and new continuation.

        Combines the cleaned existing content with a new continuation section,
        preserving headers and removing leftover template text.

        Args:
            cleaned_content: Cleaned story content (from _clean_story_content)
            title: Narrative title for the continuation
            continuation: AI-generated continuation text

        Returns:
            Final story content with continuation appended
        """
        # Try to find header section (separated by ---)
        parts = cleaned_content.split("---", 2)
        if len(parts) >= 2:
            # File has header section with metadata
            header_section = parts[0] + "---"
            rest = "---".join(parts[1:]) if len(parts) > 2 else ""
        else:
            # No header section - content is all story/template
            header_section = ""
            rest = cleaned_content

        # Remove template text from story content
        kept_content = self._filter_template_text(rest)

        # Combine: header (if any) + kept content + new continuation
        if header_section:
            if kept_content.strip():
                new_content = (
                    f"{header_section}\n{kept_content}\n\n"
                    f"## {title}\n\n{continuation}\n"
                )
            else:
                new_content = (
                    f"{header_section}\n\n## {title}\n\n"
                    f"{continuation}\n"
                )
        else:
            if kept_content.strip():
                new_content = (
                    f"{kept_content}\n\n"
                    f"## {title}\n\n{continuation}\n"
                )
            else:
                new_content = (
                    f"## {title}\n\n{continuation}\n"
                )

        return new_content

    def _generate_story_hooks_file(self, hooks_config: Dict[str, Any]) -> None:
        """Generate or append story hooks from story content.

        Generates story hooks using AI if available, falls back to placeholders.

        Args:
            hooks_config: Dict with keys:
                - campaign_dir: Path to the campaign directory
                - story_name: Name of the story file
                - story_content: Full story text content
                - workspace_path: Path to the workspace root
                - party_names: List of party member names
                - npc_suggestions: NPC detection results
                - ai_client: Optional AI client for generation
        """
        hooks_path = os.path.join(
            hooks_config["campaign_dir"], "story_hooks_001.md"
        )
        if os.path.exists(hooks_path):
            return

        hooks = None
        if hooks_config.get("ai_client"):
            party_characters = load_party_with_profiles(
                hooks_config["campaign_dir"], hooks_config["workspace_path"]
            )
            ai_hooks = generate_story_hooks_from_content(
                hooks_config["ai_client"], hooks_config["story_content"],
                party_characters, hooks_config["party_names"]
            )
            if ai_hooks:
                hooks = convert_ai_hooks_to_list(ai_hooks)

        if hooks is None:
            hooks = ["[Primary plot thread to pursue]",
                     "[Secondary subplot]"]

        create_story_hooks_file(
            hooks_config["campaign_dir"], hooks_config["story_name"], hooks,
            npc_suggestions=hooks_config["npc_suggestions"]
        )

    def _generate_session_results_file(self, results_config: Dict[str, Any]) -> None:
        """Generate or update session results file.

        Creates session results with AI generation or placeholders.

        Args:
            results_config: Dict with keys:
                - campaign_dir: Path to the campaign directory
                - story_name: Name of the story
                - story_content: Full story text
                - party_names: List of party member names
                - ai_client: Optional AI client for generation
        """
        results_path = os.path.join(
            results_config["campaign_dir"], "session_results_001.md"
        )
        if os.path.exists(results_path):
            return

        session = StorySession(results_config["story_name"])

        if results_config.get("ai_client"):
            ai_results = generate_session_results_from_story(
                results_config["ai_client"], results_config["story_content"],
                results_config["party_names"]
            )
            if ai_results:
                for action in ai_results.get("character_actions", []):
                    session.character_actions.append(action)
                for event in ai_results.get("narrative_events", []):
                    session.narrative_events.append(event)
            else:
                for member in results_config["party_names"]:
                    session.character_actions.append(
                        f"{member}: [Action/outcome]"
                    )
        else:
            for member in results_config["party_names"]:
                session.character_actions.append(
                    f"{member}: [Action/outcome]"
                )

        create_session_results_file(results_config["campaign_dir"], session)

    def _generate_supporting_files(
        self,
        filepath: str,
        campaign_dir: str,
        workspace_path: str,
        ai_client=None,
    ) -> None:
        """Generate story_hooks and session_results files.

        Uses the canonical NPC detection and file creation functions to ensure
        consistency with the rest of the story management system. Optionally
        uses AI to generate story hooks and session results from story narrative.

        Args:
            filepath: Path to the story file
            campaign_dir: Path to the campaign directory
            workspace_path: Path to the workspace root
            ai_client: Optional AI client for AI-powered analysis
        """
        try:
            story_content = read_text_file(filepath)
            story_name = os.path.basename(filepath)[:-3]  # Remove .md
            party_names = self._load_party_members(campaign_dir)

            # Detect NPCs and generate files
            npc_suggestions = detect_npc_suggestions(
                story_content, party_names, workspace_path
            )

            # Generate story_hooks file
            hooks_config = {
                "campaign_dir": campaign_dir,
                "story_name": story_name,
                "story_content": story_content,
                "workspace_path": workspace_path,
                "party_names": party_names,
                "npc_suggestions": npc_suggestions,
                "ai_client": ai_client,
            }
            self._generate_story_hooks_file(hooks_config)

            # Generate session_results file
            results_config = {
                "campaign_dir": campaign_dir,
                "story_name": story_name,
                "story_content": story_content,
                "party_names": party_names,
                "ai_client": ai_client,
            }
            self._generate_session_results_file(results_config)

        except OSError as e:
            print(f"[WARNING] Could not generate supporting files: {e}")

    def _load_party_members(self, campaign_dir: str) -> List[str]:
        """Load party member names from campaign configuration.

        Args:
            campaign_dir: Path to the campaign directory

        Returns:
            List of party member names
        """

        party_names = []
        try:
            party_config_path = os.path.join(
                campaign_dir, "current_party.json"
            )
            if os.path.exists(party_config_path):
                with open(party_config_path, "r", encoding="utf-8") as f:
                    party_data = json.load(f)
                    party_names = party_data.get("party_members", [])
        except (OSError, json.JSONDecodeError):
            pass

        return party_names

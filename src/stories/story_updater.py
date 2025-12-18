"""
Story Updater Component.

Handles updating story files with analysis results, including consultant notes,
consistency sections, combat narratives, and AI-generated continuations.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.utils.markdown_utils import update_markdown_section
from src.utils.story_formatting_utils import (
    generate_consultant_notes,
    generate_consistency_section,
)
from src.utils.text_formatting_utils import wrap_narrative_text
from src.npcs.npc_auto_detection import detect_npc_suggestions
from src.stories.hooks_and_analysis import create_story_hooks_file
from src.stories.session_results_manager import (
    StorySession,
    create_session_results_file,
    populate_session_from_ai_results,
)
from src.stories.story_ai_generator import (
    generate_session_results_from_story,
    generate_story_hooks_from_content,
)
from src.cli.party_config_manager import load_party_with_profiles
from src.characters.character_consistency import create_character_development_file
from src.stories.character_action_analyzer import extract_character_actions


class ContinuationConfig:
    """Configuration builder for story continuation operations."""

    def __init__(self):
        """Initialize empty config."""
        self.filepath = None
        self.continuation = None
        self.campaign_dir = None
        self.workspace_path = None
        self.ai_client = None
        self.prompt = None

    def set_paths(
        self, filepath: str, campaign_dir: str, workspace_path: str
    ) -> "ContinuationConfig":
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

    def set_content(self, continuation: str) -> "ContinuationConfig":
        """Set continuation content.

        Args:
            continuation: AI-generated continuation text

        Returns:
            Self for method chaining
        """
        self.continuation = continuation
        return self

    def set_ai_client(self, ai_client) -> "ContinuationConfig":
        """Set optional AI client.

        Args:
            ai_client: Optional AI client for analysis

        Returns:
            Self for method chaining
        """
        self.ai_client = ai_client
        return self

    def set_prompt(self, prompt: str) -> "ContinuationConfig":
        """Set user prompt for spell extraction.

        Args:
            prompt: User prompt for narrative generation

        Returns:
            Self for method chaining
        """
        self.prompt = prompt
        return self

    def validate(self) -> bool:
        """Validate that all required fields are set.

        Returns:
            True if valid, False otherwise
        """
        return all(
            [
                self.filepath,
                self.continuation,
                self.campaign_dir,
                self.workspace_path,
            ]
        )


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
        if content is None:
            content = ""

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

    def _process_narrative(self, narrative: str, prompt: Optional[str] = None) -> str:
        """Process narrative by wrapping to 80 chars and highlighting spells.

        Args:
            narrative: Raw narrative text
            prompt: Optional user prompt to extract spells from

        Returns:
            Processed narrative with wrapping and spell highlighting
        """
        # Wrap to 80 characters and highlight spells from prompt
        narrative = wrap_narrative_text(narrative, prompt=prompt or "")

        return narrative

    def append_combat_narrative(
        self,
        filepath: str,
        narrative: str,
        title: Optional[str] = None,
        prompt: Optional[str] = None,
    ):
        """
        Append combat narrative to story file.

        Args:
            filepath: Path to the story file
            narrative: Combat narrative text to append
            title: Combat section title (optional, defaults to "Combat Scene")
            prompt: User prompt for spell extraction (optional)
        """
        if not file_exists(filepath):
            return

        content = read_text_file(filepath)
        if content is None:
            content = ""

        # Use provided title or default to "Combat Scene"
        section_title = title if title else "Combat Scene"

        # Process narrative: wrap and highlight spells from prompt
        processed_narrative = self._process_narrative(narrative, prompt)

        # Add combat section with level 3 header for indentation
        combat_section = f"\n\n### {section_title}\n\n{processed_narrative}\n"
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
        if not config.filepath or not file_exists(config.filepath):
            return False

        try:
            current_content = read_text_file(config.filepath)
            if current_content is None:
                current_content = ""
            cleaned_content = self.clean_story_content(current_content)
            continuation_title = self.extract_narrative_title(
                config.continuation or "", ai_client=config.ai_client
            )

            new_content = self._build_story_content_with_continuation(
                cleaned_content,
                continuation_title,
                config.continuation or "",
                config.prompt or "",
            )

            write_text_file(config.filepath, new_content)

            if config.campaign_dir is None or config.workspace_path is None:
                print("[ERROR] campaign_dir and workspace_path must not be None")
                return False

            self._generate_supporting_files(
                config.filepath,
                config.campaign_dir,
                config.workspace_path,
                ai_client=config.ai_client,
            )

            print(
                f"[SUCCESS] Appended AI continuation to story file: "
                f"{os.path.basename(config.filepath)}"
            )
            return True

        except OSError as e:
            print(f"[ERROR] Failed to update story: {e}")
            return False

    def clean_story_content(self, content: str) -> str:
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
            elif line.startswith("**Created:**") or line.startswith("**Description:**"):
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

    def extract_narrative_title(self, text: str, ai_client=None) -> str:
        """Extract an inventive narrative title from story content.

        Attempts to identify key entities (locations, actions, NPCs) and uses
        AI if available to generate descriptive titles. Falls back to pattern
        matching for location/action-based titles.

        Args:
            text: The continuation text
            ai_client: Optional AI client for title generation

        Returns:
            A narrative title for the section (e.g., "Quest at the Pony")
        """
        if not text or not text.strip():
            return "Story Continuation"

        # Try AI title generation first if available
        if ai_client:
            ai_title = self._generate_ai_narrative_title(text, ai_client)
            if ai_title and ai_title != "Story Continuation":
                return ai_title

        # Fallback: Use pattern-based extraction
        return self._extract_pattern_based_title(text)

    def _generate_ai_narrative_title(self, text: str, ai_client) -> str:
        """Generate a narrative title using AI.

        Args:
            text: The narrative content
            ai_client: AI client for title generation

        Returns:
            An AI-generated title or empty string if generation fails
        """
        if not ai_client:
            return ""

        try:
            # Use first 500 chars as context
            context = text[:500]
            prompt = (
                f"Based on this story narrative, generate a SHORT, "
                f"inventive title (3-5 words maximum) that captures "
                f"the main event or location.\n\n"
                f"Narrative: {context}\n\n"
                f"Generate ONLY the title, nothing else. "
                f"Make it vivid and specific.\n"
                f'Examples: "The Prancing Pony Quest", "Goblins of Breehill", '
                f'"The Vanishing Travelers", "Ambush in the Woods"\n\nTitle:'
            )

            title = ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}], temperature=0.7
            ).strip()

            # Clean up the title
            title = title.strip("\"'.")

            # Validate title length
            if len(title.split()) > 6:
                return ""

            return title if title else ""

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError):
            return ""

    def _extract_pattern_based_title(self, text: str) -> str:
        """Extract title using pattern matching on narrative content.

        Looks for locations, NPCs, and action keywords to build descriptive
        titles when AI is unavailable.

        Args:
            text: The continuation text

        Returns:
            A pattern-based narrative title
        """
        # Get first few lines for analysis
        first_lines = " ".join(text.split("\n")[:3]).lower()

        # Try named locations first (with articles or proper names)
        named_locs = {
            "prancing pony": "Prancing Pony",
            "breehill forest": "Breehill Forest",
            "castle": "Castle",
            "temple": "Temple",
            "tavern": "Tavern",
            "inn": "Inn",
            "village": "Village",
        }

        # Action keywords matching (paired with action titles)
        actions = [
            ("quest", "Quest"),
            ("ambush", "Ambush"),
            ("battle", "Battle"),
            ("meeting", "Meeting"),
            ("investigation", "Investigation"),
            ("discovery", "Discovery"),
            ("vanishing", "Vanishing Travelers"),
            ("goblins", "Goblin Attack"),
            ("ambushed", "Ambush"),
        ]

        # Check named locations
        for loc_key, loc_name in named_locs.items():
            if loc_key in first_lines:
                for keyword, action_title in actions:
                    if keyword in first_lines:
                        return f"{action_title} at {loc_name}"
                return f"The {loc_name}"

        # Generic locations list
        generic_locs = [
            "tavern",
            "inn",
            "castle",
            "village",
            "town",
            "city",
            "forest",
            "dungeon",
            "cave",
            "tower",
            "temple",
            "shrine",
            "market",
            "garden",
            "hall",
            "chamber",
            "room",
            "passage",
            "woods",
        ]

        # Generic action keywords
        generic_actions = [
            "quest",
            "ambush",
            "battle",
            "meeting",
            "investigation",
            "discovery",
            "escape",
            "ritual",
            "ceremony",
            "negotiation",
            "confrontation",
            "retreat",
            "advance",
            "attack",
            "defend",
        ]

        # Find first matching generic location
        for location in generic_locs:
            if location in first_lines:
                for action in generic_actions:
                    if action in first_lines:
                        return f"{action.title()} at the {location}"
                return f"The {location.title()}"

        # Last resort: capitalized words from first line
        first_line = text.split("\n")[0].strip()
        capitalized = [
            w.strip(".,!?;:")
            for w in first_line.split()
            if w and w[0].isupper() and w.lower() not in ["a", "an", "the"]
        ]

        return " ".join(capitalized[:3]) if capitalized else "Story Continuation"

    def _build_story_content_with_continuation(
        self, cleaned_content: str, title: str, continuation: str, prompt: str = ""
    ) -> str:
        """Build story content with template removal and new continuation.

        Combines the cleaned existing content with a new continuation section,
        preserving headers and removing leftover template text.

        Args:
            cleaned_content: Cleaned story content (from _clean_story_content)
            title: Narrative title for the continuation
            continuation: AI-generated continuation text
            prompt: Optional user prompt for spell extraction

        Returns:
            Final story content with continuation appended
        """
        # Process continuation: wrap and highlight spells from prompt
        processed_continuation = self._process_narrative(continuation, prompt)

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
                    f"## {title}\n\n{processed_continuation}\n"
                )
            else:
                new_content = (
                    f"{header_section}\n\n## {title}\n\n" f"{processed_continuation}\n"
                )
        else:
            if kept_content.strip():
                new_content = (
                    f"{kept_content}\n\n" f"## {title}\n\n{processed_continuation}\n"
                )
            else:
                new_content = f"## {title}\n\n{processed_continuation}\n"

        return new_content

    def _extract_story_based_hooks(self, story_content: str, party_names: list) -> list:
        """Extract story-aware hooks from narrative content.

        Analyzes story narrative to extract meaningful hooks when AI is unavailable.
        Looks for locations, actions, and character developments.

        Args:
            story_content: The story narrative text
            party_names: List of party member names

        Returns:
            List of extracted hook strings, or empty list if extraction fails
        """
        if not story_content or not story_content.strip():
            return []

        hooks = []
        locations = [
            "tavern",
            "inn",
            "castle",
            "village",
            "town",
            "city",
            "forest",
            "dungeon",
            "cave",
            "tower",
            "temple",
            "shrine",
            "market",
            "garden",
            "hall",
            "chamber",
            "room",
            "passage",
            "throne",
            "cemetery",
            "mansion",
            "ship",
            "boat",
            "river",
            "mountain",
        ]

        # Extract location from first line
        first_line = story_content.split("\n")[0].strip() if story_content else ""
        words = first_line.split()
        for i, word in enumerate(words):
            word_lower = word.lower().strip(".,!?;:")
            if word_lower in locations:
                location = (
                    f"{words[i - 1].strip('.,!?;:')} {word_lower}"
                    if i > 0 and words[i - 1][0].isupper()
                    else word_lower
                )
                hooks.append(f"Explore {location} further and uncover its secrets")
                break

        # Extract action-based hooks
        action_pairs = [
            ("quest", "Complete the quest that was presented"),
            ("mission", "Execute the mission objectives"),
            ("danger", "Face the danger that was introduced"),
            ("mystery", "Solve the mystery that was revealed"),
            ("threat", "Address the threat that emerged"),
        ]
        story_lower = story_content.lower()
        for keyword, hook_text in action_pairs:
            if keyword in story_lower:
                hooks.append(hook_text)
                break

        # Character development hook
        if party_names:
            hooks.append(f"Develop {party_names[0]}'s character through the events")

        # Ensure minimum hooks
        while len(hooks) < 3:
            hooks.append("[Character development opportunity]")

        return hooks

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
        # Build the actual filename that will be created
        # This must match the logic in create_story_hooks_file()
        session_date = datetime.now().strftime("%Y-%m-%d")
        story_name = hooks_config["story_name"]
        filename = (
            f"story_hooks_{session_date}_{story_name.lower().replace(' ', '_')}.md"
        )
        hooks_path = os.path.join(hooks_config["campaign_dir"], filename)

        # If file already exists, log info and continue to regenerate/update
        if os.path.exists(hooks_path):
            print(f"[INFO] Story hooks file already exists, regenerating: {filename}")

        hooks = None
        if hooks_config.get("ai_client"):
            party_characters = load_party_with_profiles(
                hooks_config["campaign_dir"], hooks_config["workspace_path"]
            )
            print(f"story content: {len(hooks_config['story_content'])} chars")
            ai_hooks = generate_story_hooks_from_content(
                hooks_config["ai_client"],
                hooks_config["story_content"],
                party_characters,
                hooks_config["party_names"],
            )
            if ai_hooks:
                # Pass structured dict directly to preserve all sections
                hooks = ai_hooks

        # Fallback 1: If AI didn't generate hooks, try story-aware extraction
        if hooks is None:
            extracted_hooks = self._extract_story_based_hooks(
                hooks_config["story_content"], hooks_config["party_names"]
            )
            if extracted_hooks and len(extracted_hooks) > 0:
                print("[INFO] Using story-aware extraction for hooks (AI unavailable)")
                hooks = extracted_hooks

        # Fallback 2: If extraction didn't work, use generic placeholders
        if hooks is None or (isinstance(hooks, list) and len(hooks) == 0):
            print("[WARNING] No hooks generated, using generic placeholders")
            hooks = [
                "[Primary plot thread to pursue]",
                "[Secondary subplot to explore]",
                "[Character development opportunity]",
            ]

        create_story_hooks_file(
            hooks_config["campaign_dir"],
            hooks_config["story_name"],
            hooks,
            npc_suggestions=hooks_config["npc_suggestions"],
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
                results_config["ai_client"],
                results_config["story_content"],
                results_config["party_names"],
            )
            if ai_results:
                populate_session_from_ai_results(session, ai_results)
            else:
                for member in results_config["party_names"]:
                    session.character_actions.append(f"{member}: [Action/outcome]")
        else:
            for member in results_config["party_names"]:
                session.character_actions.append(f"{member}: [Action/outcome]")

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
                story_content if story_content is not None else "",
                party_names,
                workspace_path,
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

            # Generate character_development file
            if party_names:
                character_profiles = self._load_character_profiles(
                    party_names, workspace_path
                )
                character_actions = extract_character_actions(
                    story_content if story_content is not None else "",
                    party_names,
                    self._truncate_at_sentence,
                    character_profiles,
                )
                if character_actions:
                    create_character_development_file(
                        campaign_dir, story_name, character_actions
                    )

        except OSError as e:
            print(f"[WARNING] Could not generate supporting files: {e}")

    def _truncate_at_sentence(self, text: str, max_length: int) -> str:
        """Truncate text at sentence boundary to avoid cutting off words.

        Args:
            text: Text to truncate
            max_length: Maximum length before truncation

        Returns:
            Truncated text ending at sentence boundary
        """
        if len(text) <= max_length:
            return text

        truncated = text[:max_length]
        sentence_endings = [".", "!", "?"]
        for ending in sentence_endings:
            last_ending = truncated.rfind(ending)
            if last_ending > max_length // 2:
                return truncated[: last_ending + 1]

        return truncated

    def _load_party_members(self, campaign_dir: str) -> List[str]:
        """Load party member names from campaign configuration.

        Args:
            campaign_dir: Path to the campaign directory

        Returns:
            List of party member names
        """

        party_names = []
        try:
            party_config_path = os.path.join(campaign_dir, "current_party.json")
            if os.path.exists(party_config_path):
                with open(party_config_path, "r", encoding="utf-8") as f:
                    party_data = json.load(f)
                    party_names = party_data.get("party_members", [])
        except (OSError, json.JSONDecodeError):
            pass

        return party_names

    def _load_character_profiles(
        self, party_names: List[str], workspace_path: str
    ) -> Dict[str, Dict[str, Any]]:
        """Load character profiles to access personality traits and background.

        Args:
            party_names: List of character names to load
            workspace_path: Path to the workspace root

        Returns:
            Dict mapping character names to their trait dictionaries
        """
        profiles = {}
        characters_dir = os.path.join(workspace_path, "game_data", "characters")

        for character_name in party_names:
            try:
                # Use first name (first word) as filename convention
                first_name = character_name.split()[0].lower()
                filename = f"{first_name}.json"
                filepath = os.path.join(characters_dir, filename)

                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        char_data = json.load(f)
                        profiles[character_name] = {
                            "name": character_name,
                            "dnd_class": char_data.get("dnd_class", ""),
                            "personality_summary": char_data.get(
                                "personality_summary", ""
                            ),
                            "background_story": char_data.get("background_story", ""),
                            "motivations": char_data.get("motivations", []),
                            "fears_weaknesses": char_data.get("fears_weaknesses", []),
                            "goals": char_data.get("goals", []),
                            "relationships": char_data.get("relationships", {}),
                            "secrets": char_data.get("secrets", []),
                            "class_abilities": char_data.get("class_abilities", []),
                            "specialized_abilities": char_data.get(
                                "specialized_abilities", []
                            ),
                            "known_spells": char_data.get("known_spells", []),
                            "feats": char_data.get("feats", []),
                        }
            except (OSError, json.JSONDecodeError, KeyError):
                pass

        return profiles

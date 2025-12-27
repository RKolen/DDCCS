"""
Story Workflow Orchestrator Module

Coordinates the creation of all auxiliary story files and post-processing tasks.
This module orchestrates calling existing functions from specialized modules to
ensure complete story workflows with NPC detection, hooks, sessions, and character
development tracking.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.npcs.npc_auto_detection import (
    detect_npc_suggestions,
    generate_npc_from_story,
    save_npc_profile,
)
from src.stories.hooks_and_analysis import (
    create_story_hooks_file,
)
from src.stories.session_results_manager import (
    StorySession,
    create_session_results_file,
    populate_session_from_ai_results,
)
from src.stories.story_ai_generator import (
    generate_story_hooks_from_content,
    generate_session_results_from_story,
)
from src.cli.party_config_manager import load_party_with_profiles
from src.characters.character_consistency import create_character_development_file
from src.stories.character_action_analyzer import extract_character_actions
from src.utils.string_utils import truncate_at_sentence


@dataclass
class WorkflowOptions:
    """Configuration and options for story workflow execution."""

    create_npc_profiles: bool = True
    create_hooks_file: bool = True
    create_character_dev_file: bool = True
    create_session_file: bool = True
    ai_client: Any = None
    skip_ai_character_analysis: bool = False  # Skip AI calls for character analysis
    max_characters_for_ai: int = 12  # Max characters to analyze with AI (performance)


@dataclass
class StoryWorkflowContext:
    """Context object for story workflow coordination."""

    story_name: str
    story_content: str
    series_path: str
    workspace_path: str
    party_names: List[str]
    ai_client: Any = None
    results: Dict[str, Any] = field(
        default_factory=lambda: {
            "npcs_created": [],
            "npcs_suggested": [],
            "hooks_file": None,
            "character_dev_file": None,
            "session_file": None,
            "errors": [],
        }
    )

    def add_error(self, message: str) -> None:
        """Add an error to the results."""
        self.results["errors"].append(message)


def coordinate_story_workflow(
    ctx: StoryWorkflowContext,
    *,
    options: Optional[WorkflowOptions] = None,
) -> Dict[str, Any]:
    """
    Orchestrate complete story workflow with all auxiliary file creation.

    Coordinates calling existing specialized functions to handle NPC detection
    and generation, story hooks file creation, character development tracking,
    and session results file creation.

    Args:
        ctx: StoryWorkflowContext with story data, paths, and party info
        options: WorkflowOptions with execution configuration and AI client

    Returns:
        Dictionary summarizing created files with keys:
        - npcs_created: List of NPC names with created profiles
        - npcs_suggested: List of NPCs detected in story
        - hooks_file: Path to created hooks file, or None
        - character_dev_file: Path to created character development file, or None
        - session_file: Path to created session results file, or None
        - errors: List of any errors encountered
    """
    if options is None:
        options = WorkflowOptions()

    # Execute workflow steps
    _process_npc_workflow(ctx, options)
    _process_hooks_workflow(ctx, options)
    _process_character_dev_workflow(ctx, options)
    _process_session_workflow(ctx, options)

    return ctx.results


def _process_npc_workflow(ctx: StoryWorkflowContext, opt: WorkflowOptions) -> None:
    """Process NPC detection and profile generation workflow step."""
    if not opt.create_npc_profiles and not opt.create_hooks_file:
        return

    try:
        npc_suggestions = detect_npc_suggestions(
            ctx.story_content, ctx.party_names, ctx.workspace_path
        )
        ctx.results["npcs_suggested"] = [npc["name"] for npc in npc_suggestions]

        # Generate and save NPC profiles if AI is available
        if opt.create_npc_profiles and opt.ai_client:
            for npc in npc_suggestions:
                try:
                    profile = generate_npc_from_story(
                        npc["name"],
                        npc["role"],
                        npc["context_excerpt"],
                        opt.ai_client,
                    )
                    if profile:
                        save_npc_profile(profile, ctx.workspace_path)
                        ctx.results["npcs_created"].append(npc["name"])
                except (ValueError, OSError, KeyError, AttributeError) as e:
                    ctx.results["errors"].append(
                        f"Failed to generate profile for {npc['name']}: {e}"
                    )
    except (ValueError, OSError, KeyError, AttributeError) as e:
        ctx.results["errors"].append(f"NPC detection failed: {e}")


def _process_hooks_workflow(ctx: StoryWorkflowContext, opt: WorkflowOptions) -> None:
    """Process story hooks file creation workflow step.

    Uses AI-powered hook generation if AI client available, falls back to
    keyword extraction for reliability.
    """
    if not opt.create_hooks_file:
        return

    try:
        hooks = None

        # Try AI-powered generation if available
        if opt.ai_client:
            party_characters = load_party_with_profiles(
                ctx.series_path, ctx.workspace_path
            )
            ai_hooks = generate_story_hooks_from_content(
                opt.ai_client, ctx.story_content, party_characters, ctx.party_names
            )
            if ai_hooks:
                hooks = ai_hooks  # Pass structured dict directly, don't convert

        # Fall back to keyword extraction if AI not available
        if hooks is None:
            hooks = _extract_story_hooks(ctx.story_content)

        npc_suggestions = detect_npc_suggestions(
            ctx.story_content, ctx.party_names, ctx.workspace_path
        )
        hooks_path = create_story_hooks_file(
            ctx.series_path,
            ctx.story_name,
            hooks,
            npc_suggestions=npc_suggestions,
        )
        ctx.results["hooks_file"] = hooks_path
    except (ValueError, OSError, KeyError, AttributeError) as e:
        ctx.results["errors"].append(f"Story hooks creation failed: {e}")


def _process_character_dev_workflow(
    ctx: StoryWorkflowContext, opt: WorkflowOptions
) -> None:
    """Process character development file creation workflow step."""
    if not opt.create_character_dev_file:
        print("[DEBUG] Character dev workflow skipped - option disabled")
        return

    print(f"Character development workflow starting - party: {ctx.party_names}")
    try:
        # Performance optimization for large parties
        party_size = len(ctx.party_names)
        if party_size > opt.max_characters_for_ai:
            print(
                f"[PERFORMANCE] Large party detected ({party_size} members). "
                f"AI analysis limited to first {opt.max_characters_for_ai} "
                "characters."
            )
            remaining = party_size - opt.max_characters_for_ai
            print(f"  Remaining {remaining} will use rule-based analysis.")

        # Load character profiles by searching all JSON files and matching by name field
        character_profiles = {}
        chars_dir = Path("game_data") / "characters"
        if chars_dir.exists():
            for json_file in chars_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        profile = json.load(f)
                        profile_name = profile.get("name", "")
                        # Match against party names
                        if profile_name in ctx.party_names:
                            # Disable AI for characters beyond max limit
                            char_index = ctx.party_names.index(profile_name)
                            if (
                                char_index >= opt.max_characters_for_ai
                                or opt.skip_ai_character_analysis
                            ):
                                if "ai_config" not in profile:
                                    profile["ai_config"] = {}
                                profile["ai_config"]["enabled"] = False
                            character_profiles[profile_name] = profile
                except (OSError, json.JSONDecodeError) as e:
                    print(f"[DEBUG] Could not load {json_file.name}: {e}")

        character_actions = extract_character_actions(
            ctx.story_content, ctx.party_names, truncate_at_sentence, character_profiles
        )

        # If no actions extracted but we have party names, create placeholder entries
        if not character_actions and ctx.party_names:
            print(
                f"[DEBUG] Creating placeholders for {len(ctx.party_names)} party members"
            )
            character_actions = [
                {
                    "character": name,
                    "action": "No actions detected yet - write your story and this will update",
                    "reasoning": "To be added after story is written",
                    "consistency": "Pending story content",
                    "notes": "System will auto-extract when character is mentioned in story",
                }
                for name in ctx.party_names
            ]

        # Only create file if we have party members
        if character_actions:
            print(
                f"[DEBUG] Creating character dev file with {len(character_actions)} entries"
            )
            char_dev_path = create_character_development_file(
                ctx.series_path,
                ctx.story_name,
                character_actions,
            )
            ctx.results["character_dev_file"] = char_dev_path
        else:
            print("[DEBUG] No character actions to save - skipping file creation")
    except (ValueError, OSError, KeyError, AttributeError) as e:
        error_msg = f"Character development file creation failed: {e}"
        print(f"[DEBUG] ERROR: {error_msg}")
        ctx.results["errors"].append(error_msg)


def _process_session_workflow(ctx: StoryWorkflowContext, opt: WorkflowOptions) -> None:
    """Process session results file creation workflow step."""
    if not opt.create_session_file:
        return

    try:
        session = StorySession(ctx.story_name, datetime.now().strftime("%Y-%m-%d"))

        # Use AI to analyze story and populate session if AI client available
        if opt.ai_client:
            party_characters = load_party_with_profiles(
                ctx.series_path, ctx.workspace_path
            )
            try:
                party_names = list(party_characters.keys())
                ai_results = generate_session_results_from_story(
                    opt.ai_client, ctx.story_content, party_names
                )
                if ai_results:
                    populate_session_from_ai_results(session, ai_results)
            except (AttributeError, ValueError, KeyError, TypeError) as e:
                print(f"[DEBUG] AI session analysis failed: {e}")

        session_path = create_session_results_file(ctx.series_path, session)
        ctx.results["session_file"] = session_path
    except (ValueError, OSError, KeyError, AttributeError) as e:
        ctx.results["errors"].append(f"Session results file creation failed: {e}")


def _extract_story_hooks(story_content: str) -> List[str]:
    """
    Extract potential story hooks from narrative content.

    Looks for sentences with keywords suggesting unresolved plot threads,
    mysteries, or follow-up opportunities.

    Args:
        story_content: The story narrative text

    Returns:
        List of potential story hook strings
    """
    hooks = []
    hook_keywords = [
        "mystery",
        "strange",
        "unusual",
        "rumors",
        "legend",
        "whispers",
        "disappeared",
        "quest",
        "treasure",
        "danger",
        "warning",
        "prophecy",
        "secret",
        "hidden",
        "forbidden",
        "curse",
    ]

    lines = story_content.split("\n")
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in hook_keywords):
            line_cleaned = line.strip()
            if line_cleaned and len(line_cleaned) > 10:
                hooks.append(line_cleaned)

    # Deduplicate and limit to 5 hooks
    unique_hooks = list(set(hooks))[:5]
    return unique_hooks if unique_hooks else ["Future adventure awaits..."]


def should_offer_ai_generation(ai_client, has_context: bool = True) -> bool:
    """
    Determine if AI story generation should be offered to user.

    Args:
        ai_client: The AI client instance (or None if unavailable)
        has_context: Whether party/campaign context is available

    Returns:
        True if AI generation should be offered, False otherwise
    """
    return ai_client is not None and has_context


def report_workflow_results(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable report of workflow results.

    Args:
        results: Dictionary returned by coordinate_story_workflow()

    Returns:
        Formatted report string
    """
    report_lines = ["[WORKFLOW] Story workflow completed"]
    report_lines.append("=" * 50)

    if results["npcs_created"]:
        report_lines.append(f"NPCs Created: {', '.join(results['npcs_created'])}")

    if results["npcs_suggested"]:
        report_lines.append(f"NPCs Detected: {', '.join(results['npcs_suggested'])}")

    if results["hooks_file"]:
        report_lines.append(f"Story Hooks: {results['hooks_file']}")

    if results["character_dev_file"]:
        report_lines.append(f"Character Dev: {results['character_dev_file']}")

    if results["session_file"]:
        report_lines.append(f"Session Results: {results['session_file']}")

    if results["errors"]:
        report_lines.append("\nWarnings/Errors:")
        for error in results["errors"]:
            report_lines.append(f"  - {error}")

    return "\n".join(report_lines)

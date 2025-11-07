"""
Story Workflow Orchestrator Module

Coordinates the creation of all auxiliary story files and post-processing tasks.
This module orchestrates calling existing functions from specialized modules to
ensure complete story workflows with NPC detection, hooks, sessions, and character
development tracking.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.npcs.npc_auto_detection import (
    detect_npc_suggestions,
    generate_npc_from_story,
    save_npc_profile,
)
from src.stories.hooks_and_analysis import (
    create_story_hooks_file,
    convert_ai_hooks_to_list
)
from src.stories.session_results_manager import (
    StorySession,
    create_session_results_file,
)
from src.stories.story_ai_generator import generate_story_hooks_from_content
from src.cli.party_config_manager import load_party_with_profiles
from src.characters.character_consistency import create_character_development_file


@dataclass
class WorkflowOptions:
    """Configuration and options for story workflow execution."""

    create_npc_profiles: bool = True
    create_hooks_file: bool = True
    create_character_dev_file: bool = True
    create_session_file: bool = True
    ai_client: Any = None


@dataclass
class StoryWorkflowContext:
    """Context object for story workflow coordination."""

    story_name: str
    story_content: str
    series_path: str
    workspace_path: str
    party_names: List[str]
    ai_client: Any = None
    results: Dict[str, Any] = field(default_factory=lambda: {
        "npcs_created": [],
        "npcs_suggested": [],
        "hooks_file": None,
        "character_dev_file": None,
        "session_file": None,
        "errors": [],
    })

    def add_error(self, message: str) -> None:
        """Add an error to the results."""
        self.results["errors"].append(message)


def coordinate_story_workflow(
    ctx: StoryWorkflowContext,
    *,
    options: WorkflowOptions = None,
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
                opt.ai_client, ctx.story_content,
                party_characters, ctx.party_names
            )
            if ai_hooks:
                hooks = convert_ai_hooks_to_list(ai_hooks)

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
        return

    try:
        character_actions = _extract_character_actions(
            ctx.story_content, ctx.party_names
        )
        char_dev_path = create_character_development_file(
            ctx.series_path,
            ctx.story_name,
            character_actions,
        )
        ctx.results["character_dev_file"] = char_dev_path
    except (ValueError, OSError, KeyError, AttributeError) as e:
        ctx.results["errors"].append(f"Character development file creation failed: {e}")


def _process_session_workflow(
    ctx: StoryWorkflowContext, opt: WorkflowOptions
) -> None:
    """Process session results file creation workflow step."""
    if not opt.create_session_file:
        return

    try:
        session = StorySession(ctx.story_name)
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


def _extract_character_actions(
    story_content: str, character_names: List[str]
) -> List[Dict[str, str]]:
    """
    Extract character actions from story narrative.

    Looks for mentions of character names followed by action descriptions.

    Args:
        story_content: The story narrative text
        character_names: List of character names to track

    Returns:
        List of character action dictionaries
    """
    actions = []

    for char_name in character_names:
        # Simple extraction: find paragraphs mentioning the character
        lines = story_content.split("\n")
        for i, line in enumerate(lines):
            if char_name in line:
                # Extract context around character mention
                context_start = max(0, i - 1)
                context_end = min(len(lines), i + 2)
                context = " ".join(lines[context_start:context_end])

                if context.strip():
                    actions.append(
                        {
                            "character": char_name,
                            "action": context.strip()[:200],
                            "reasoning": "To be analyzed",
                            "consistency": "Pending review",
                            "notes": "Extract from narrative",
                        }
                    )
                    break  # One action per character for initial extraction

    return actions


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
        report_lines.append(
            f"NPCs Created: {', '.join(results['npcs_created'])}"
        )

    if results["npcs_suggested"]:
        report_lines.append(
            f"NPCs Detected: {', '.join(results['npcs_suggested'])}"
        )

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

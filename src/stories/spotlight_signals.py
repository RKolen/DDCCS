"""Signal collectors for the Spotlighting System.

Each collector reads from existing data sources (story files, character profiles,
campaign hooks) and returns a mapping of entity name to SpotlightSignal.

Signal types and default weights:
    recency              - 20  (sessions since last appearance)
    unresolved_thread    - 25  (open plot threads or NPC follow-ups)
    dc_failure           - 20  (pending or failed DC checks)
    relationship_tension - 15  (conflicted relationships in character profile)
"""

import os
import re
from typing import Dict, List, Optional

from src.stories.spotlight_types import SpotlightSignal
from src.utils.character_profile_utils import load_character_profile
from src.utils.file_io import read_text_file
from src.utils.story_file_helpers import list_story_files


# Keywords that indicate relationship tension in a character profile
_TENSION_KEYWORDS: frozenset = frozenset([
    "conflict",
    "tension",
    "rivalry",
    "distrust",
    "fear",
    "hatred",
    "complicated",
    "uneasy",
    "antagonistic",
    "opposed",
    "hostile",
    "betrayed",
    "rival",
    "enemy",
])

_HOOKS_PATTERN = re.compile(r"story_hooks_.*\.md$")

_DC_PATTERN = re.compile(
    r"DC\s+\d+|failed.*check|check.*failed|needs?\s+to\s+roll",
    re.IGNORECASE,
)


def _read_story_content(campaign_path: str, filename: str) -> str:
    """Read a single story file and return its content.

    Args:
        campaign_path: Absolute path to the campaign directory.
        filename: Story filename to read.

    Returns:
        File content string, or empty string on read error.
    """
    filepath = os.path.join(campaign_path, filename)
    try:
        return read_text_file(filepath) or ""
    except (OSError, UnicodeDecodeError):
        return ""


def _extract_section(content: str, section_title: str) -> str:
    """Extract the body of a markdown section by heading title.

    Reads from the heading up to the next same-level heading or end of file.

    Args:
        content: Full markdown file content.
        section_title: Exact section heading text (without leading # symbols).

    Returns:
        Section body text stripped of surrounding whitespace, or empty string.
    """
    pattern = re.compile(
        rf"##\s+{re.escape(section_title)}\s*\n(.*?)(?=\n##|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def _find_evidence_sentence(text: str, name: str) -> str:
    """Find the first sentence containing name in text.

    Args:
        text: Text to search through.
        name: Name to look for.

    Returns:
        First matching sentence stripped of whitespace, or empty string.
    """
    pattern = re.compile(
        rf"[^.!?\n]*{re.escape(name)}[^.!?\n]*[.!?\n]?",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(0).strip() if match else ""


def _name_near_dc_pattern(content: str, name: str) -> bool:
    """Check whether a DC-related pattern appears within 200 chars of name.

    Args:
        content: Text content to search.
        name: Name to find.

    Returns:
        True if a DC pattern appears within 200 characters of name.
    """
    name_pos = content.find(name)
    if name_pos < 0:
        return False
    window_start = max(0, name_pos - 200)
    window_end = name_pos + 200 + len(name)
    window = content[window_start:window_end]
    return bool(_DC_PATTERN.search(window))


def collect_recency_signals(
    campaign_path: str,
    names: List[str],
    entity_type: str,
    recency_weight: float = 20.0,
) -> Dict[str, SpotlightSignal]:
    """Score entities by how many sessions have passed since last mention.

    Reads all numbered story files (e.g. 001_start.md) in the campaign
    directory and finds the last file index where each name appears.
    Entities absent from more recent sessions receive proportionally higher
    signal weights.

    Args:
        campaign_path: Absolute path to the campaign directory.
        names: Entity names to check for story mentions.
        entity_type: "character" or "npc" (used in description text only).
        recency_weight: Maximum weight contribution for this signal type.

    Returns:
        Mapping of entity name to SpotlightSignal for entities absent from
        at least one session at the end of the campaign.
    """
    story_files = list_story_files(campaign_path)
    total_sessions = len(story_files)
    if total_sessions == 0 or not names:
        return {}

    last_seen: Dict[str, int] = {}
    for index, filename in enumerate(story_files):
        content = _read_story_content(campaign_path, filename)
        for name in names:
            if name in content:
                last_seen[name] = index

    signals: Dict[str, SpotlightSignal] = {}
    for name in names:
        if name not in last_seen:
            sessions_absent = total_sessions
            last_file = "never"
        else:
            sessions_absent = total_sessions - last_seen[name] - 1
            last_file = story_files[last_seen[name]]

        if sessions_absent > 0:
            weight = recency_weight * (sessions_absent / total_sessions)
            signals[name] = SpotlightSignal(
                signal_type="recency",
                description=(
                    f"{entity_type.capitalize()} absent for "
                    f"{sessions_absent} session(s)"
                ),
                weight=round(weight, 2),
                evidence=f"Last seen in: {last_file}",
            )

    return signals


def collect_unresolved_thread_signals(
    campaign_path: str,
    names: List[str],
    thread_weight: float = 25.0,
) -> Dict[str, SpotlightSignal]:
    """Identify entities mentioned in open plot threads or NPC follow-ups.

    Reads the most recent story hooks file and searches the
    'Unresolved Plot Threads' and 'NPC Follow-ups' sections for entity names.

    Args:
        campaign_path: Absolute path to the campaign directory.
        names: Entity names to check for thread mentions.
        thread_weight: Weight contribution when a thread mention is found.

    Returns:
        Mapping of entity name to SpotlightSignal for entities referenced
        in open plot threads.
    """
    if not names:
        return {}

    try:
        all_files = os.listdir(campaign_path)
    except (FileNotFoundError, NotADirectoryError):
        return {}

    hook_files = sorted(f for f in all_files if _HOOKS_PATTERN.match(f))
    if not hook_files:
        return {}

    latest_hooks = hook_files[-1]
    raw_content = _read_story_content(campaign_path, latest_hooks)

    thread_section = _extract_section(raw_content, "Unresolved Plot Threads")
    npc_section = _extract_section(raw_content, "NPC Follow-ups")
    combined = f"{thread_section}\n{npc_section}"

    signals: Dict[str, SpotlightSignal] = {}
    for name in names:
        if name in combined:
            evidence = _find_evidence_sentence(combined, name)
            signals[name] = SpotlightSignal(
                signal_type="unresolved_thread",
                description="Mentioned in open plot threads or NPC follow-ups",
                weight=round(thread_weight, 2),
                evidence=evidence or f"Mentioned in {latest_hooks}",
            )

    return signals


def collect_dc_failure_signals(
    campaign_path: str,
    character_names: List[str],
    dc_weight: float = 20.0,
) -> Dict[str, SpotlightSignal]:
    """Find characters involved in pending or failed DC checks.

    Scans story files for 'DC Suggestions Needed' sections and for
    DC-related language (e.g. "failed check", "DC 18") near character names.
    Pending DCs receive full weight; proximity matches receive 60% weight.

    Args:
        campaign_path: Absolute path to the campaign directory.
        character_names: Character names to check for DC events.
        dc_weight: Maximum weight contribution for a pending DC signal.

    Returns:
        Mapping of character name to SpotlightSignal for characters with
        pending or failed DC checks.
    """
    if not character_names:
        return {}

    signals: Dict[str, SpotlightSignal] = {}

    for filename in list_story_files(campaign_path):
        content = _read_story_content(campaign_path, filename)

        # Check 'DC Suggestions Needed' section for character mentions
        dc_section = _extract_section(content, "DC Suggestions Needed")
        if dc_section:
            for name in character_names:
                if name in dc_section and name not in signals:
                    evidence = _find_evidence_sentence(dc_section, name)
                    signals[name] = SpotlightSignal(
                        signal_type="dc_failure",
                        description="Involved in a pending DC check",
                        weight=round(dc_weight, 2),
                        evidence=evidence or f"Pending DC in {filename}",
                    )

        # Check narrative content for DC failure patterns near character names
        if _DC_PATTERN.search(content):
            for name in character_names:
                if name not in signals and _name_near_dc_pattern(content, name):
                    signals[name] = SpotlightSignal(
                        signal_type="dc_failure",
                        description="Involved in a DC check event",
                        weight=round(dc_weight * 0.6, 2),
                        evidence=f"DC event near name in {filename}",
                    )

    return signals


def collect_relationship_tension_signals(
    character_names: List[str],
    workspace_path: Optional[str] = None,
    tension_weight: float = 15.0,
) -> Dict[str, SpotlightSignal]:
    """Score characters with conflicted or unresolved relationships.

    Reads each character profile and checks the 'relationships' dictionary for
    values that contain tension keywords (conflict, rivalry, distrust, etc.).
    Weight scales with number of tense relationships, capped at tension_weight.

    Args:
        character_names: Character names to check.
        workspace_path: Optional workspace root path for profile resolution.
        tension_weight: Maximum weight contribution per character.

    Returns:
        Mapping of character name to SpotlightSignal for characters with
        at least one relationship containing tension keywords.
    """
    if not character_names:
        return {}

    signals: Dict[str, SpotlightSignal] = {}

    for name in character_names:
        profile = load_character_profile(name, workspace_path)
        if not profile:
            continue

        relationships = profile.get("relationships", {})
        if not isinstance(relationships, dict):
            continue

        tense_entries = [
            f"{other}: {desc}"
            for other, desc in relationships.items()
            if isinstance(desc, str)
            and any(kw in desc.lower() for kw in _TENSION_KEYWORDS)
        ]

        if tense_entries:
            entry_count = len(tense_entries)
            weight = min(tension_weight, tension_weight * (entry_count / 3.0))
            signals[name] = SpotlightSignal(
                signal_type="relationship_tension",
                description=(
                    f"{entry_count} tense relationship(s) in character profile"
                ),
                weight=round(weight, 2),
                evidence=tense_entries[0],
            )

    return signals

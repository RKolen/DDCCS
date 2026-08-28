"""The prompt opening both recap-reading passes share.

Drafting an arc and reading its cast ask different questions of the same
material: a campaign's session recaps, in play order, under a campaign name.
That opening lives here so the two prompts cannot drift apart, and so the
budgets that keep them inside local inference are set once.
"""

from typing import List, Sequence

from src.story_arcs.arc_draft_types import SessionRecap
from src.utils.string_utils import clip_to_budget

# Budgets keep the prompt inside what local inference handles well. A campaign
# runs to dozens of sessions; the recaps are clipped rather than dropped so the
# whole span is represented.
MAX_RECAP_CHARS = 500
MAX_RECAPS = 40


def render_sessions(recaps: Sequence[SessionRecap]) -> str:
    """Render session recaps as one clipped line each.

    Args:
        recaps: Session recaps, in play order.

    Returns:
        Newline-separated session lines, empty when none carry text.
    """
    return "\n".join(
        f"Session {recap.story_number}: {clip_to_budget(recap.summary, MAX_RECAP_CHARS)}"
        for recap in recaps[:MAX_RECAPS]
        if recap.summary.strip()
    )


def session_preamble(
    task: str,
    campaign_name: str,
    recaps: Sequence[SessionRecap],
) -> List[str]:
    """Build the leading prompt blocks: the task, the campaign, the sessions.

    Args:
        task: The instruction that opens the prompt.
        campaign_name: The campaign the sessions belong to.
        recaps: Session recaps, in play order.

    Returns:
        The opening blocks, ready to extend with the task's own tail.
    """
    return [
        task,
        "",
        f"Campaign: {campaign_name}",
        "",
        "Sessions so far:",
        render_sessions(recaps),
    ]


def usable_recaps(recaps: Sequence[SessionRecap]) -> List[SessionRecap]:
    """Return the recaps that carry text, in play order.

    Args:
        recaps: Session recaps in any order.

    Returns:
        The non-blank recaps, sorted by session number.
    """
    usable = [recap for recap in recaps if recap.summary.strip()]
    return sorted(usable, key=lambda recap: recap.story_number)

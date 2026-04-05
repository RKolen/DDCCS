"""Core spotlight scoring engine for the Spotlighting System.

Generates SpotlightReport objects for a campaign by combining multiple signal
collectors into a single ranked priority list. Also provides a prompt injection
helper that formats the top entries as a short text block for AI system prompts.
"""

from typing import Dict, List, NamedTuple, Optional

from src.config.config_types import SpotlightConfig
from src.stories.spotlight_signals import (
    collect_dc_failure_signals,
    collect_recency_signals,
    collect_relationship_tension_signals,
    collect_unresolved_thread_signals,
)
from src.stories.spotlight_types import SpotlightEntry, SpotlightReport, SpotlightSignal
from src.utils.character_profile_utils import list_character_names
from src.utils.file_io import get_json_files_in_directory, load_json_file
from src.utils.path_utils import get_campaign_path, get_npcs_dir
from src.utils.terminal_display import display_panel
from src.utils.string_utils import get_timestamp

_MAX_SCORE = 100.0


class _CampaignCtx(NamedTuple):
    """Lightweight context bundle for campaign path and workspace path."""

    campaign_path: str
    workspace_path: Optional[str]


class SpotlightEngine:
    """Generates spotlight reports by scoring characters and NPCs in a campaign.

    Each call to generate_report() collects recency, unresolved thread,
    DC failure, and relationship tension signals, combines them per entity,
    and returns a SpotlightReport ranked by total score.
    """

    def generate_report(
        self,
        campaign_name: str,
        workspace_path: Optional[str] = None,
        config: Optional[SpotlightConfig] = None,
    ) -> SpotlightReport:
        """Generate a full spotlight report for the given campaign.

        Collects all narrative signals for characters and NPCs in the campaign,
        combines them into scored SpotlightEntry objects, and returns a ranked
        SpotlightReport.

        Args:
            campaign_name: Name of the campaign directory under game_data/campaigns/.
            workspace_path: Optional workspace root path.
            config: Optional SpotlightConfig controlling signal weights. Uses
                SpotlightConfig defaults when not provided.

        Returns:
            SpotlightReport with all entries sorted by score descending.
        """
        cfg = config or SpotlightConfig()
        ctx = _CampaignCtx(
            campaign_path=get_campaign_path(campaign_name, workspace_path),
            workspace_path=workspace_path,
        )
        character_names = list_character_names(workspace_path)
        npc_names = self._load_npc_names(workspace_path)
        thread_signals = collect_unresolved_thread_signals(
            ctx.campaign_path, character_names + npc_names, cfg.thread_weight
        )
        char_entries = self._build_character_entries(
            ctx, character_names, cfg, thread_signals
        )
        npc_entries = self._build_npc_entries(ctx, npc_names, cfg, thread_signals)
        return SpotlightReport(
            campaign_name=campaign_name,
            generated_at=get_timestamp(),
            entries=sorted(
                char_entries + npc_entries, key=lambda e: e.score, reverse=True
            ),
        )

    def _build_character_entries(
        self,
        ctx: _CampaignCtx,
        character_names: List[str],
        cfg: SpotlightConfig,
        thread_signals: Dict[str, SpotlightSignal],
    ) -> List[SpotlightEntry]:
        """Collect signals and build SpotlightEntry objects for characters.

        Args:
            ctx: Campaign path and workspace path bundle.
            character_names: List of character names to score.
            cfg: SpotlightConfig controlling signal weights.
            thread_signals: Pre-computed unresolved thread signals.

        Returns:
            List of SpotlightEntry objects for characters with at least one signal.
        """
        return self._build_entries(
            character_names,
            "character",
            [
                collect_recency_signals(
                    ctx.campaign_path, character_names, "character", cfg.recency_weight
                ),
                thread_signals,
                collect_dc_failure_signals(
                    ctx.campaign_path, character_names, cfg.dc_weight
                ),
                collect_relationship_tension_signals(
                    character_names, ctx.workspace_path, cfg.tension_weight
                ),
            ],
        )

    def _build_npc_entries(
        self,
        ctx: _CampaignCtx,
        npc_names: List[str],
        cfg: SpotlightConfig,
        thread_signals: Dict[str, SpotlightSignal],
    ) -> List[SpotlightEntry]:
        """Collect signals and build SpotlightEntry objects for NPCs.

        Args:
            ctx: Campaign path and workspace path bundle.
            npc_names: List of NPC names to score.
            cfg: SpotlightConfig controlling signal weights.
            thread_signals: Pre-computed unresolved thread signals.

        Returns:
            List of SpotlightEntry objects for NPCs with at least one signal.
        """
        return self._build_entries(
            npc_names,
            "npc",
            [
                collect_recency_signals(
                    ctx.campaign_path, npc_names, "npc", cfg.recency_weight
                ),
                thread_signals,
            ],
        )

    def get_prompt_injection(
        self,
        campaign_name: str,
        workspace_path: Optional[str] = None,
        config: Optional[SpotlightConfig] = None,
    ) -> str:
        """Return a brief spotlight context block for injection into AI prompts.

        Formats the top scoring characters and NPCs as a short natural-language
        paragraph suitable for prepending to a story generation system prompt.

        Args:
            campaign_name: Name of the campaign directory.
            workspace_path: Optional workspace root path.
            config: Optional SpotlightConfig. Uses defaults when not provided.

        Returns:
            Formatted spotlight context string, or empty string if nothing is
            noteworthy (all scores are zero).
        """
        cfg = config or SpotlightConfig()
        report = self.generate_report(campaign_name, workspace_path, cfg)
        top_chars = report.top_characters(cfg.max_characters_in_prompt)
        top_npcs = report.top_npcs(cfg.max_npcs_in_prompt)

        if not top_chars and not top_npcs:
            return ""

        lines = ["Narratively important at this moment:"]
        for entry in top_chars:
            signal_descs = "; ".join(s.description for s in entry.signals)
            lines.append(
                f"- {entry.name} (score {entry.score:.0f}): {signal_descs}."
            )
        for entry in top_npcs:
            signal_descs = "; ".join(s.description for s in entry.signals)
            lines.append(
                f"- {entry.name} (NPC, score {entry.score:.0f}): {signal_descs}."
            )

        return "\n".join(lines)

    def _load_npc_names(self, workspace_path: Optional[str] = None) -> List[str]:
        """Load NPC display names from the npcs directory.

        Reads each non-example JSON file and returns the value of the 'name'
        field. Files without a 'name' field are skipped silently.

        Args:
            workspace_path: Optional workspace root path.

        Returns:
            List of NPC name strings.
        """
        npcs_dir = get_npcs_dir(workspace_path)
        names: List[str] = []

        json_files = get_json_files_in_directory(
            npcs_dir, exclude_patterns=["example", "template"]
        )

        for filepath in json_files:
            try:
                data = load_json_file(str(filepath))
                if isinstance(data, dict):
                    npc_name = data.get("name", "")
                    if npc_name:
                        names.append(str(npc_name))
            except (OSError, ValueError):
                continue

        return names

    def _build_entries(
        self,
        names: List[str],
        entity_type: str,
        signal_maps: List[Dict[str, SpotlightSignal]],
    ) -> List[SpotlightEntry]:
        """Build SpotlightEntry objects by combining multiple signal maps.

        Entities with no signals (zero score) are excluded from the output.
        Total score is capped at _MAX_SCORE (100).

        Args:
            names: Entity names to build entries for.
            entity_type: "character" or "npc".
            signal_maps: List of signal dicts mapping name to SpotlightSignal.

        Returns:
            List of SpotlightEntry objects for entities with at least one signal.
        """
        entries: List[SpotlightEntry] = []

        for name in names:
            signals: List[SpotlightSignal] = []
            for signal_map in signal_maps:
                if name in signal_map:
                    signals.append(signal_map[name])

            if not signals:
                continue

            raw_score = sum(s.weight for s in signals)
            score = round(min(raw_score, _MAX_SCORE), 1)

            entries.append(
                SpotlightEntry(
                    name=name,
                    entity_type=entity_type,
                    score=score,
                    signals=signals,
                )
            )

        return entries


def display_spotlight_report(report: SpotlightReport) -> None:
    """Display a SpotlightReport as a formatted terminal panel.

    Uses rich display_panel if available, otherwise falls back to plain text.
    Shows top characters and NPCs with their scores and signal descriptions.

    Args:
        report: SpotlightReport to display.
    """
    if not report.entries:
        display_panel(
            "No significant narrative spotlight signals found.",
            title=f"Spotlight Report: {report.campaign_name}",
            style="yellow",
        )
        return

    lines: List[str] = [f"Generated: {report.generated_at}", ""]

    top_chars = report.top_characters(5)
    top_npcs = report.top_npcs(5)

    if top_chars:
        lines.append("Characters:")
        for entry in top_chars:
            signal_descs = "; ".join(s.description for s in entry.signals)
            lines.append(f"  {entry.name} [{entry.score:.0f}] - {signal_descs}")

    if top_npcs:
        if top_chars:
            lines.append("")
        lines.append("NPCs:")
        for entry in top_npcs:
            signal_descs = "; ".join(s.description for s in entry.signals)
            lines.append(f"  {entry.name} [{entry.score:.0f}] - {signal_descs}")

    display_panel(
        "\n".join(lines),
        title=f"Spotlight Report: {report.campaign_name}",
        style="cyan",
    )

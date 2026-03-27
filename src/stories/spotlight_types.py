"""Data types for the Spotlighting System.

Defines the core data structures used to represent narrative spotlight scores,
individual signals, and the full campaign spotlight report.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SpotlightSignal:
    """A single narrative signal contributing to a spotlight score.

    Attributes:
        signal_type: Category identifier (recency, unresolved_thread, etc.).
        description: Human-readable description of the signal.
        weight: Numeric contribution to the entity's total score.
        evidence: Source text or file reference that triggered this signal.
    """

    signal_type: str
    description: str
    weight: float
    evidence: str


@dataclass
class SpotlightEntry:
    """Spotlight score and signals for a single character or NPC.

    Attributes:
        name: Display name of the character or NPC.
        entity_type: Either "character" or "npc".
        score: Combined score (0-100) from all active signals.
        signals: Individual signals that contribute to the score.
        last_appearance: Filename of the story where the entity last appeared.
        sessions_absent: Number of story sessions since last appearance.
    """

    name: str
    entity_type: str
    score: float
    signals: List[SpotlightSignal] = field(default_factory=list)
    last_appearance: str = ""
    sessions_absent: int = 0


@dataclass
class SpotlightReport:
    """Full spotlight report for a campaign context.

    Attributes:
        campaign_name: Name of the campaign this report covers.
        generated_at: Timestamp string when the report was generated.
        entries: All scored SpotlightEntry objects, sorted by score descending.
    """

    campaign_name: str
    generated_at: str
    entries: List[SpotlightEntry] = field(default_factory=list)

    def top_characters(self, n: int = 3) -> List[SpotlightEntry]:
        """Return the top N spotlit characters sorted by score descending.

        Args:
            n: Maximum number of entries to return.

        Returns:
            Sorted list of SpotlightEntry instances for characters.
        """
        chars = [e for e in self.entries if e.entity_type == "character"]
        return sorted(chars, key=lambda x: x.score, reverse=True)[:n]

    def top_npcs(self, n: int = 3) -> List[SpotlightEntry]:
        """Return the top N spotlit NPCs sorted by score descending.

        Args:
            n: Maximum number of entries to return.

        Returns:
            Sorted list of SpotlightEntry instances for NPCs.
        """
        npcs = [e for e in self.entries if e.entity_type == "npc"]
        return sorted(npcs, key=lambda x: x.score, reverse=True)[:n]

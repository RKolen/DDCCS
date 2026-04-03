"""Cross-campaign event linking."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from src.timeline.event_schema import TimelineEvent
from src.timeline.timeline_store import TimelineStore


@dataclass
class CampaignLink:
    """Represents a link between two campaigns."""

    campaign_1: str
    campaign_2: str
    link_type: str
    description: str = ""
    shared_events: List[str] = field(default_factory=list)


class CrossCampaignLinker:
    """Manages links between campaigns and finds shared elements."""

    def __init__(self, store: Optional[TimelineStore] = None):
        """Initialize linker with a timeline store."""
        self.store = store or TimelineStore()
        self._campaign_links: Dict[str, List[CampaignLink]] = {}

    def link_campaigns(
        self,
        campaign_1: str,
        campaign_2: str,
        link_type: str,
        description: str = "",
    ) -> CampaignLink:
        """Create a link between two campaigns."""
        link = CampaignLink(
            campaign_1=campaign_1,
            campaign_2=campaign_2,
            link_type=link_type,
            description=description,
        )
        for campaign in (campaign_1, campaign_2):
            self._campaign_links.setdefault(campaign, [])
            self._campaign_links[campaign].append(link)
        return link

    def find_shared_characters(
        self, campaign_1: str, campaign_2: str
    ) -> Set[str]:
        """Find characters that appear in both campaigns."""
        chars_1 = self._collect_characters(campaign_1)
        chars_2 = self._collect_characters(campaign_2)
        return chars_1.intersection(chars_2)

    def _collect_characters(self, campaign: str) -> Set[str]:
        """Collect all character names from a campaign's events."""
        names: Set[str] = set()
        for event in self.store.get_campaign_timeline(campaign):
            names.update(c.lower() for c in event.context.characters_involved)
        return names

    def find_shared_locations(
        self, campaign_1: str, campaign_2: str
    ) -> Set[str]:
        """Find locations that appear in both campaigns."""
        locs_1 = self._collect_locations(campaign_1)
        locs_2 = self._collect_locations(campaign_2)
        return locs_1.intersection(locs_2)

    def _collect_locations(self, campaign: str) -> Set[str]:
        """Collect all location names from a campaign's events."""
        locs: Set[str] = set()
        for event in self.store.get_campaign_timeline(campaign):
            if event.context.location:
                locs.add(event.context.location.lower())
        return locs

    def suggest_links(self, campaign_name: str) -> List[Dict]:
        """Suggest potential links to other campaigns."""
        suggestions = []
        all_campaigns = set(self.store.get_campaign_names())
        all_campaigns.discard(campaign_name)

        for other in all_campaigns:
            shared_chars = self.find_shared_characters(campaign_name, other)
            shared_locs = self.find_shared_locations(campaign_name, other)

            if shared_chars or shared_locs:
                suggestions.append(
                    {
                        "campaign": other,
                        "shared_characters": list(shared_chars),
                        "shared_locations": list(shared_locs),
                        "link_type": self._suggest_link_type(
                            shared_chars, shared_locs
                        ),
                    }
                )

        return suggestions

    def _suggest_link_type(
        self, shared_chars: Set[str], shared_locs: Set[str]
    ) -> str:
        """Suggest link type based on shared elements."""
        if shared_chars:
            return "shared_world"
        if shared_locs:
            return "parallel"
        return "unknown"

    def get_linked_campaigns(self, campaign_name: str) -> List[CampaignLink]:
        """Get all campaigns linked to a given campaign."""
        return self._campaign_links.get(campaign_name, [])

    def get_unified_timeline(
        self, campaign_names: List[str]
    ) -> List[TimelineEvent]:
        """Get a unified event list across multiple campaigns."""
        all_events = []
        for campaign in campaign_names:
            all_events.extend(self.store.get_campaign_timeline(campaign))
        return sorted(all_events, key=lambda e: e.event_id)

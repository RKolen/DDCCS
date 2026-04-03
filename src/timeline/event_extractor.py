"""Extract timeline events from story files."""

import json
import re
from dataclasses import dataclass
from typing import Dict, List

from src.timeline.event_schema import (
    EventContext,
    EventMeta,
    EventPriority,
    EventSource,
    EventType,
    TimelineEvent,
)
from src.utils.file_io import read_text_file


@dataclass
class ExtractionPattern:
    """Pattern for extracting events from text."""

    event_type: EventType
    patterns: List[str]
    priority: EventPriority


EXTRACTION_PATTERNS = [
    ExtractionPattern(
        event_type=EventType.COMBAT,
        patterns=[
            r"(?:battle|fight|combat|ambush|skirmish|duel|clash)",
            r"(?:attacks?|strikes?|defeats?|slays?|kills?)",
            r"(?:encounter with)",
        ],
        priority=EventPriority.IMPORTANT,
    ),
    ExtractionPattern(
        event_type=EventType.CHARACTER_DEATH,
        patterns=[
            r"(?:dies?|death|falls? in battle|killed|slain)",
            r"(?:perishes?|passes? away)",
        ],
        priority=EventPriority.CRITICAL,
    ),
    ExtractionPattern(
        event_type=EventType.NPC_INTRO,
        patterns=[
            r"(?:meets?|encounters?|introduces?)\s+(?:a|an|the)?\s+\w+\s+(?:named|called)",
            r"(?:introduced to)",
        ],
        priority=EventPriority.NORMAL,
    ),
    ExtractionPattern(
        event_type=EventType.DISCOVERY,
        patterns=[
            r"(?:discovers?|finds?|uncovers?|reveals?)",
            r"(?:stumbles? upon)",
            r"(?:hidden|secret|ancient)",
        ],
        priority=EventPriority.IMPORTANT,
    ),
    ExtractionPattern(
        event_type=EventType.QUEST_START,
        patterns=[
            r"(?:quest|mission|task|journey)\s+(?:begins?|starts?)",
            r"(?:accepts?\s+(?:the|a)\s+(?:quest|mission))",
            r"(?:tasked with)",
        ],
        priority=EventPriority.IMPORTANT,
    ),
    ExtractionPattern(
        event_type=EventType.QUEST_COMPLETE,
        patterns=[
            r"(?:quest|mission)\s+(?:completes?|ends?|finished)",
            r"(?:successfully\s+)?(?:completes?|finishes?)\s+(?:the|a)?\s*(?:quest|mission)",
        ],
        priority=EventPriority.IMPORTANT,
    ),
    ExtractionPattern(
        event_type=EventType.ITEM_GAIN,
        patterns=[
            r"(?:acquires?|obtains?|gains?|receives?|finds?)\s+(?:a|an|the)",
            r"(?:rewarded with)",
        ],
        priority=EventPriority.NORMAL,
    ),
    ExtractionPattern(
        event_type=EventType.LOCATION_VISIT,
        patterns=[
            r"(?:arrives? at|reaches?|enters?|visits?)",
            r"(?:travels? to|journeys? to)",
        ],
        priority=EventPriority.MINOR,
    ),
    ExtractionPattern(
        event_type=EventType.PLOT_TWIST,
        patterns=[
            r"(?:reveals? that|turns? out)",
            r"(?:betrayal|traitor|secret)",
            r"(?:unexpectedly|suddenly)",
        ],
        priority=EventPriority.CRITICAL,
    ),
]

_COMMON_WORDS = {"The", "A", "An", "He", "She", "They", "It", "This", "That"}

_TYPE_TITLES = {
    EventType.COMBAT: "Combat Encounter",
    EventType.CHARACTER_DEATH: "Character Death",
    EventType.NPC_INTRO: "NPC Introduction",
    EventType.DISCOVERY: "Discovery",
    EventType.QUEST_START: "Quest Begins",
    EventType.QUEST_COMPLETE: "Quest Completed",
    EventType.ITEM_GAIN: "Item Acquired",
    EventType.LOCATION_VISIT: "Location Visited",
    EventType.PLOT_TWIST: "Plot Twist",
}


class EventExtractor:
    """Extracts events from story text using regex patterns."""

    def __init__(self):
        """Initialize the event extractor."""
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[EventType, List[re.Pattern]]:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for extraction in EXTRACTION_PATTERNS:
            compiled[extraction.event_type] = [
                re.compile(p, re.IGNORECASE) for p in extraction.patterns
            ]
        return compiled

    def extract_from_file(
        self,
        file_path: str,
        campaign_name: str = "",
        story_file: str = "",
    ) -> List[TimelineEvent]:
        """Extract events from a story file."""
        content = read_text_file(file_path)
        if not content:
            return []
        return self.extract_from_text(content, campaign_name, story_file)

    def extract_from_text(
        self,
        text: str,
        campaign_name: str = "",
        story_file: str = "",
    ) -> List[TimelineEvent]:
        """Extract events from story text."""
        events = []
        sections = self._split_sections(text)
        for section_title, section_content in sections:
            section_events = self._extract_from_section(
                section_content, section_title, campaign_name, story_file
            )
            events.extend(section_events)
        return events

    def _split_sections(self, text: str) -> List[tuple]:
        """Split text into sections by markdown headers."""
        sections = []
        current_title = "Introduction"
        current_content: List[str] = []

        for line in text.split("\n"):
            if line.startswith("#"):
                if current_content:
                    sections.append((current_title, "\n".join(current_content)))
                current_title = line.lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append((current_title, "\n".join(current_content)))

        return sections

    def _extract_from_section(
        self,
        content: str,
        section_title: str,
        campaign_name: str,
        story_file: str,
    ) -> List[TimelineEvent]:
        """Extract events from a single section."""
        events = []
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for paragraph in paragraphs:
            detected = self._detect_events_in_paragraph(
                paragraph, section_title, campaign_name, story_file
            )
            events.extend(detected)
        return events

    def _detect_events_in_paragraph(
        self,
        paragraph: str,
        section_title: str,
        campaign_name: str,
        story_file: str,
    ) -> List[TimelineEvent]:
        """Detect events within a paragraph."""
        events = []
        seen_ids = set()

        for event_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(paragraph):
                    start = max(0, match.start() - 50)
                    end = min(len(paragraph), match.end() + 100)
                    ctx_text = paragraph[start:end]

                    event = TimelineEvent(
                        event_id="",
                        title=self._generate_title(event_type, ctx_text),
                        event_type=event_type,
                        context=EventContext(
                            description=ctx_text.strip(),
                            location=self._extract_location(paragraph),
                            characters_involved=self._extract_character_names(
                                paragraph
                            ),
                        ),
                        source=EventSource(
                            campaign_name=campaign_name,
                            story_file=story_file,
                            story_section=section_title,
                        ),
                        meta=EventMeta(
                            priority=self._get_priority_for_type(event_type),
                            extraction_confidence=0.7,
                        ),
                    )
                    event.event_id = event.generate_id()

                    if event.event_id not in seen_ids:
                        seen_ids.add(event.event_id)
                        events.append(event)

        return events

    def _generate_title(self, event_type: EventType, context: str) -> str:
        """Generate a title for an event."""
        base_title = _TYPE_TITLES.get(event_type, "Event")
        first_sentence = context.split(".")[0] if "." in context else context
        if len(first_sentence) < 50:
            return f"{base_title}: {first_sentence.strip()}"
        return base_title

    def _get_priority_for_type(self, event_type: EventType) -> EventPriority:
        """Get default priority for an event type."""
        for extraction in EXTRACTION_PATTERNS:
            if extraction.event_type == event_type:
                return extraction.priority
        return EventPriority.NORMAL

    def _extract_character_names(self, text: str) -> List[str]:
        """Extract potential character names from text."""
        matches = re.findall(r"\b[A-Z][a-z]+\b", text)
        return [m for m in matches if m not in _COMMON_WORDS][:5]

    def _extract_location(self, text: str) -> str:
        """Extract potential location from text."""
        location_patterns = [
            r"(?:in|at|near|inside|outside)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:arrives? at|reaches?|enters?)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        for loc_pattern in location_patterns:
            match = re.search(loc_pattern, text)
            if match:
                return match.group(1)
        return ""


class AIEventExtractor:
    """Use AI to extract events with higher accuracy."""

    def __init__(self, ai_client):
        """Initialize with AI client."""
        self.ai_client = ai_client

    def extract_with_ai(
        self,
        text: str,
        campaign_name: str = "",
        story_file: str = "",
    ) -> List[TimelineEvent]:
        """Extract events using AI analysis."""
        system_msg = self.ai_client.create_system_message(
            "You are a story analyst. Extract key events from D&D story text."
        )
        user_prompt = (
            "Analyze the following story text and extract key events. "
            "For each event, provide: event_type (combat, social, exploration, "
            "discovery, quest_start, quest_complete, character_death, npc_intro, "
            "item_gain, location_visit, plot_twist, or custom), title, description, "
            "characters_involved (list), location, and priority "
            "(critical, important, normal, minor).\n\n"
            f"Story text:\n{text}\n\n"
            "Respond in JSON format as an array of events:\n"
            '[{"event_type":"type","title":"Brief title",'
            '"description":"Description","characters_involved":["name"],'
            '"location":"Location","priority":"important"}]'
        )
        user_msg = self.ai_client.create_user_message(user_prompt)

        try:
            response = self.ai_client.chat_completion(
                messages=[system_msg, user_msg]
            )
            events_data = self.parse_ai_response(response)
            return self._build_events(events_data, campaign_name, story_file)
        except (ValueError, KeyError, AttributeError):
            return []

    def parse_ai_response(self, response: str) -> List[Dict]:
        """Parse AI JSON response into a list of event data dicts."""
        start = response.find("[")
        end = response.rfind("]") + 1
        if 0 <= start < end:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass
        return []

    def _build_events(
        self,
        events_data: List[Dict],
        campaign_name: str,
        story_file: str,
    ) -> List[TimelineEvent]:
        """Build TimelineEvent objects from parsed AI data."""
        events = []
        for data in events_data:
            try:
                event = TimelineEvent(
                    event_id="",
                    title=data.get("title", "Unknown Event"),
                    event_type=EventType(data.get("event_type", "custom")),
                    context=EventContext(
                        description=data.get("description", ""),
                        location=data.get("location", ""),
                        characters_involved=data.get("characters_involved", []),
                    ),
                    source=EventSource(
                        campaign_name=campaign_name,
                        story_file=story_file,
                    ),
                    meta=EventMeta(
                        priority=EventPriority(
                            data.get("priority", "normal")
                        ),
                        extraction_confidence=0.9,
                    ),
                )
                event.event_id = event.generate_id()
                events.append(event)
            except (ValueError, KeyError):
                pass
        return events

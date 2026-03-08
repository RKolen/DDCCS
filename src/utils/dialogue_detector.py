"""
Dialogue Detection Module

Detects and segments dialogue from story text, identifying speakers
for each dialogue segment to enable multi-voice TTS narration.

Supported dialogue patterns:
- Pattern A: "Dialogue," speaker said
- Pattern B: Speaker: "Dialogue"
- Pattern C: Character (action): "Dialogue"
- Pattern D: Standalone dialogue (uses context)
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SpeechSegment:
    """A single speech segment with speaker attribution."""

    text: str
    speaker: str  # Character name or "narrator"
    voice_id: Optional[str] = None  # Piper voice ID
    speed: float = 1.0
    pitch_shift: int = 0
    is_action: bool = False  # True for action descriptions (not spoken)


# Regex patterns for dialogue detection
DIALOGUE_PATTERNS = {
    # Pattern A: "Dialogue," speaker said
    # Examples: "Evenin'," the barkeep said. "Ale," Gorak replied.
    "inline_after": re.compile(
        r'"([^"]+)"\s*,?\s*(?:the\s+)?(\w+)\s+(?:said|replied|asked|muttered|'
        r'whispered|called|answered|responded|added|stated|exclaimed|'
        r'continued|finished|chuckled|laughed|growled|snarled|grunted)',
        re.IGNORECASE,
    ),
    # Pattern B: Speaker: "Dialogue" or Speaker (action): "Dialogue"
    # Examples: Nymur: "I couldn't help but hear..."
    #           Kaelen: (with a raised eyebrow) "Friendship comes cheap..."
    "prefix_explicit": re.compile(
        r"^([A-Z][a-zA-Z]+)\s*:?\s*(?:\([^)]+\))?\s*:\s*\"([^\"]+)\"",
        re.MULTILINE,
    ),
    # Pattern C: Speaker: "Multi-line dialogue" (continuation)
    # Example: Gorak: "I've heard rumors..."
    "prefix_continuation": re.compile(
        r"^([A-Z][a-zA-Z]+)\s*:\s*\"([^\"]+)\"",
        re.MULTILINE,
    ),
    # Pattern D: Standalone quoted text
    "standalone": re.compile(r'"([^"]+)"'),
}

# Speaker action verbs that indicate speech
SPEAKER_VERBS = {
    "said", "replied", "asked", "muttered", "whispered", "called",
    "answered", "responded", "added", "stated", "exclaimed", "continued",
    "finished", "chuckled", "laughed", "growled", "snarled", "grunted",
    "barked", "hissed", "roared", "boomed", "croaked", "drawled",
}

# Character name patterns (capitalized words at start of lines)
CHARACTER_NAME_PATTERN = re.compile(r"^([A-Z][a-zA-Z]+)\s*:", re.MULTILINE)


class DialogueDetector:
    """Detects and segments dialogue from story text."""

    def __init__(
        self,
        known_characters: Optional[List[str]] = None,
        known_npcs: Optional[List[str]] = None,
    ):
        """Initialize dialogue detector.

        Args:
            known_characters: List of known player character names
            known_npcs: List of known NPC names
        """
        self.known_characters = set(known_characters or [])
        self.known_npcs = set(known_npcs or [])
        self.all_known_names = self.known_characters | self.known_npcs
        self._last_speaker: Optional[str] = None

    def update_known_names(
        self,
        characters: Optional[List[str]] = None,
        npcs: Optional[List[str]] = None,
    ) -> None:
        """Update known character and NPC names.

        Args:
            characters: New list of known player characters
            npcs: New list of known NPCs
        """
        if characters:
            self.known_characters = set(characters)
        if npcs:
            self.known_npcs = set(npcs)
        self.all_known_names = self.known_characters | self.known_npcs

    def detect_speech_segments(self, text: str) -> List[SpeechSegment]:
        """Detect speech segments in text.

        Args:
            text: Story text to analyze

        Returns:
            List of SpeechSegment objects in order
        """
        segments: List[SpeechSegment] = []
        self._last_speaker = None

        # Split into paragraphs
        paragraphs = text.split("\n\n")

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Try each pattern in order of specificity
            paragraph_segments = self._analyze_paragraph(paragraph)
            segments.extend(paragraph_segments)

            # Update last speaker for context
            if paragraph_segments:
                last = paragraph_segments[-1]
                if last.speaker and last.speaker != "narrator":
                    self._last_speaker = last.speaker

        return segments

    def _analyze_paragraph(self, paragraph: str) -> List[SpeechSegment]:
        """Analyze a single paragraph for dialogue.

        Args:
            paragraph: Paragraph text to analyze

        Returns:
            List of SpeechSegment objects
        """
        segments: List[SpeechSegment] = []

        # Try Pattern B first (explicit speaker prefix)
        prefix_matches = list(DIALOGUE_PATTERNS["prefix_explicit"].finditer(paragraph))
        if prefix_matches:
            for match in prefix_matches:
                speaker = match.group(1)
                dialogue = match.group(2)
                # Resolve speaker name
                resolved_speaker = self.resolve_speaker_name(speaker)
                segments.append(
                    SpeechSegment(text=dialogue, speaker=resolved_speaker)
                )
            return segments

        # Try Pattern A (inline after dialogue)
        inline_matches = list(DIALOGUE_PATTERNS["inline_after"].finditer(paragraph))
        if inline_matches:
            # Check if this is just narrative action with dialogue
            for match in inline_matches:
                dialogue = match.group(1)
                speaker = match.group(2)
                resolved_speaker = self.resolve_speaker_name(speaker)
                segments.append(
                    SpeechSegment(text=dialogue, speaker=resolved_speaker)
                )
            return segments

        # Try Pattern C (multi-line continuation)
        continuation_matches = list(
            DIALOGUE_PATTERNS["prefix_continuation"].finditer(paragraph)
        )
        if continuation_matches:
            for match in continuation_matches:
                speaker = match.group(1)
                dialogue = match.group(2)
                resolved_speaker = self.resolve_speaker_name(speaker)
                segments.append(
                    SpeechSegment(text=dialogue, speaker=resolved_speaker)
                )
            return segments

        # Try Pattern D (standalone quotes with context)
        standalone_matches = list(DIALOGUE_PATTERNS["standalone"].finditer(paragraph))
        if standalone_matches:
            # Check if there's a character name nearby
            speaker = self._find_speaker_context(paragraph)
            if speaker:
                for match in standalone_matches:
                    dialogue = match.group(1)
                    # Only use this if the quote appears to be spoken
                    if self._is_dialogue_context(paragraph, match.start()):
                        segments.append(
                            SpeechSegment(text=dialogue, speaker=speaker)
                        )

        # If no dialogue found, treat as narrator action/narration
        if not segments and paragraph.strip():
            segments.append(
                SpeechSegment(text=paragraph, speaker="narrator", is_action=True)
            )

        return segments

    def _find_speaker_context(self, text: str) -> Optional[str]:
        """Find speaker from context (previous speaker or nearby names).

        Args:
            text: Text to search for context

        Returns:
            Speaker name if found, None otherwise
        """
        # Check for previous speaker
        if self._last_speaker:
            return self._last_speaker

        # Look for character names in the text
        for name in self.all_known_names:
            if name in text:
                return name

        # Look for any capitalized words that might be names
        words = text.split()
        for word in words[:3]:  # Check first few words
            clean_word = word.strip(",:().\"")
            if clean_word and clean_word[0].isupper():
                if self.resolve_speaker_name(clean_word):
                    return clean_word

        return None

    def _is_dialogue_context(self, text: str, quote_start: int) -> bool:
        """Check if a quote position indicates actual dialogue.

        Args:
            text: Full text
            quote_start: Start position of quote

        Returns:
            True if this appears to be spoken dialogue
        """
        # Get text before the quote
        before = text[:quote_start].strip()

        # If there's no text before, it's likely dialogue
        if not before:
            return True

        # Check for common dialogue introduction patterns
        dialogue_indicators = [
            "said", "replied", "asked", "whispered", "answered",
            "stated", "exclaimed", "continued", "added",
        ]

        before_lower = before.lower()
        for indicator in dialogue_indicators:
            if indicator in before_lower:
                return True

        return False

    def resolve_speaker_name(self, text_name: str) -> str:
        """Resolve a text reference to a known character/NPC name.

        Args:
            text_name: Name as it appears in the text

        Returns:
            Resolved character name or "narrator" if not found
        """
        if not text_name:
            return "narrator"

        # Exact match
        if text_name in self.all_known_names:
            return text_name

        # Case-insensitive match
        for known in self.all_known_names:
            if known.lower() == text_name.lower():
                return known

        # Check for "the X" pattern - could extend to match against NPC roles
        return text_name  # Return as-is for potential matching later


def clean_text_for_dialogue_detection(text: str) -> str:
    """Preprocess text for dialogue detection.

    Args:
        text: Raw text

    Returns:
        Preprocessed text
    """
    # Remove BOM if present
    text = text.lstrip("\ufeff")

    # Normalize quotes (curly to straight)
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace(''', '"').replace(''', '"')

    # Remove markdown formatting that might interfere
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)

    return text


def segment_story_for_tts(
    text: str,
    known_characters: Optional[List[str]] = None,
    known_npcs: Optional[List[str]] = None,
) -> List[SpeechSegment]:
    """Segment story text into speech segments for TTS.

    This is the main entry point for preparing story text for
    multi-voice TTS narration.

    Args:
        text: Story text to segment
        known_characters: Optional list of known player characters
        known_npcs: Optional list of known NPCs

    Returns:
        List of SpeechSegment objects in reading order
    """
    # Preprocess text
    cleaned = clean_text_for_dialogue_detection(text)

    # Create detector and find segments
    detector = DialogueDetector(known_characters, known_npcs)
    segments = detector.detect_speech_segments(cleaned)

    return segments


def get_speaker_voice_map(
    segments: List[SpeechSegment],
    character_voices: dict,
    narrator_voice_id: str = "en_US-joe-medium",
) -> List[SpeechSegment]:
    """Assign voice IDs to speech segments based on speaker.

    Args:
        segments: List of speech segments
        character_voices: Dict mapping character names to voice IDs
        narrator_voice_id: Voice ID for narrator

    Returns:
        Segments with voice IDs assigned
    """
    result = []

    for segment in segments:
        if segment.is_action:
            # Action descriptions use narrator voice
            segment.voice_id = narrator_voice_id
        elif segment.speaker.lower() == "narrator":
            segment.voice_id = narrator_voice_id
        else:
            # Look up character's voice with fuzzy matching
            segment.voice_id = _resolve_character_voice(
                segment.speaker, character_voices, narrator_voice_id
            )

        result.append(segment)

    return result


def _resolve_character_voice(
    speaker: str,
    character_voices: dict,
    default_voice: str,
) -> str:
    """Resolve character name to voice with fuzzy matching.

    Args:
        speaker: The speaker name from dialogue detection
        character_voices: Dict mapping character names to voice IDs
        default_voice: Default voice if no match

    Returns:
        Voice ID for the speaker
    """
    # Pronouns that need resolution
    pronouns = frozenset({"he", "she", "they", "him", "her", "them"})

    # Try exact match first
    if speaker in character_voices:
        return character_voices[speaker]

    # Try case-insensitive match
    speaker_lower = speaker.lower()
    for name, voice_id in character_voices.items():
        if name.lower() == speaker_lower:
            return voice_id

    # Try partial match (e.g., "Frodo" matches "Frodo Baggins")
    for name, voice_id in character_voices.items():
        if speaker_lower in name.lower() or name.lower() in speaker_lower:
            return voice_id

    # Check for pronouns - use default if we can't resolve
    if speaker_lower in pronouns:
        return default_voice

    # Default to narrator voice
    return default_voice

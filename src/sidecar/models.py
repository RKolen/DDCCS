"""Pydantic request and response models for the query parser sidecar."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ParseQueryRequest(BaseModel):
    """Incoming query parse request from Drupal."""

    q: str

    @field_validator("q")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        """Strip surrounding whitespace and reject blank queries.

        Args:
            value: Raw query string.

        Returns:
            Stripped query string.

        Raises:
            ValueError: If the query is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("q must not be empty")
        return stripped


class ParseQueryResponse(BaseModel):
    """Parsed query result returned to the caller."""

    original: str
    query: str
    inferred_type: Optional[str] = None
    confidence: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    ai_configured: bool


class SpotlightRequest(BaseModel):
    """Spotlight score request from the Gatsby frontend."""

    campaign_name: str
    character_names: List[str]


class SpotlightCharacterScore(BaseModel):
    """Spotlight score for a single character."""

    name: str
    score: float


class SpotlightResponse(BaseModel):
    """Spotlight scores for all requested characters."""

    campaign_name: str
    entries: List[SpotlightCharacterScore]


class BuildCharacterRequest(BaseModel):
    """Request to derive a character sheet from a class template."""

    name: str
    class_name: str
    level: int = Field(default=1, ge=1, le=20)
    ability_scores: Optional[Dict[str, int]] = None
    subclass: Optional[str] = None
    background: str = ""
    race: str = "Human"
    subspecies: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    @field_validator("name", "class_name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        """Strip whitespace and reject blank required identifiers.

        Args:
            value: Raw field value.

        Returns:
            The stripped value.

        Raises:
            ValueError: If the value is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped


class BuildCharacterResponse(BaseModel):
    """Derived character sheet ready for persistence.

    The ``character`` payload follows the game_data character dictionary
    shape produced by the template engine (ability scores, derived hit
    points, proficiency bonus, class features, spell slots, equipment).
    """

    character: Dict[str, Any]


class ResolveBackgroundRequest(BaseModel):
    """Request to resolve a background's granted data from the rules wiki."""

    name: str

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Strip whitespace and reject a blank background name.

        Args:
            value: Raw background name.

        Returns:
            The stripped name.

        Raises:
            ValueError: If the name is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped


class ResolveBackgroundResponse(BaseModel):
    """Resolved background data, or null when it could not be resolved.

    The ``background`` payload (when present) holds ability_options, feat,
    skills, tools, gold, and equipment.
    """

    background: Optional[Dict[str, Any]] = None


class SkillPlanRequest(BaseModel):
    """Request for a character's class + species/subspecies skill plan."""

    class_name: str
    level: int = Field(default=1, ge=1, le=20)
    race: str = "Human"
    subspecies: Optional[str] = None


class SkillPlanResponse(BaseModel):
    """A skill plan: auto-granted skills/tools plus choice groups.

    ``granted``/``granted_tools`` are auto-proficient skill and tool names;
    ``choices`` is a list of {id, label, count, from, kind} where ``kind`` is
    one of skill/tool/skill_or_tool (an empty ``from`` means any of that kind).
    ``equipment_choices`` are the class starting-equipment groups (each {id,
    label, items:[{name, item_type}], gold} — take the items or the gold).
    ``subclass`` is {level, options:[names]} when the class chooses a subclass.
    ``source`` is "taxonomy" when the class plan came from the class taxonomy,
    else "template".
    """

    granted: List[str]
    granted_tools: List[str]
    granted_languages: List[str] = Field(default_factory=list)
    choices: List[Dict[str, Any]]
    equipment_choices: List[Dict[str, Any]] = Field(default_factory=list)
    subclass: Optional[Dict[str, Any]] = None
    source: str = "template"


class EquipmentDescribeRequest(BaseModel):
    """Request to resolve descriptions and types for a list of item names."""

    names: List[str] = Field(default_factory=list)


class EquipmentItemInfo(BaseModel):
    """Resolved catalogue data for one item: prose description and type."""

    description: str = ""
    item_type: str = "item"


class EquipmentDescribeResponse(BaseModel):
    """Resolved equipment, keyed by the requested name.

    Names with no catalogue match are omitted from ``items``.
    """

    items: Dict[str, EquipmentItemInfo] = Field(default_factory=dict)


class TtsRequest(BaseModel):
    """Request to synthesise speech from text with a Piper voice."""

    text: str
    voice_id: str = ""
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    # Pitch shift in semitones, applied as a post-process (Piper has no pitch).
    pitch: float = Field(default=0.0, ge=-12.0, le=12.0)


class ArcStoryInput(BaseModel):
    """One story's text for character arc analysis, in campaign order."""

    content: str
    title: str = ""
    story_number: Optional[int] = None


class ArcAnalysisRequest(BaseModel):
    """Request to analyze a character's arc across their campaign's stories."""

    character_name: str
    campaign_name: str = ""
    stories: List[ArcStoryInput] = Field(default_factory=list)


class ArcMetricModel(BaseModel):
    """A single development metric's progression across stories."""

    label: str
    series: List[float] = Field(default_factory=list)
    direction: str = "stasis"
    obs: str = ""


class ArcRelationshipModel(BaseModel):
    """A character relationship arc."""

    target: str
    type: str = "neutral"
    strength: int = 5
    trust: int = 5
    note: str = ""


class ArcGoalModel(BaseModel):
    """A character goal and its progress."""

    description: str
    status: str = "active"
    progress: int = 0


class ArcStoryRequest(BaseModel):
    """Request to analyze a single story into one arc data point."""

    character_name: str
    content: str
    title: str = ""
    story_number: Optional[int] = None
    pronouns: str = ""


class ArcDataPointModel(BaseModel):
    """One story's arc data point (matches ArcDataPoint.to_dict)."""

    story_file: str = ""
    session_id: str = ""
    timestamp: str = ""
    metric_values: Dict[str, Any] = Field(default_factory=dict)
    observations: List[str] = Field(default_factory=list)
    key_events: List[str] = Field(default_factory=list)
    ai_analysis: str = ""


class ArcAggregateRequest(BaseModel):
    """Request to aggregate stored per-story data points into a full arc."""

    character_name: str
    campaign_name: str = ""
    pronouns: str = ""
    data_points: List[ArcDataPointModel] = Field(default_factory=list)


class ArcSynthesisRequest(BaseModel):
    """Request to synthesize an arc from stored per-story analysis texts."""

    character_name: str
    pronouns: str = ""
    story_texts: List[str] = Field(default_factory=list)


class ArcSynthesisResponse(BaseModel):
    """Arc synthesis from stored analyses: summary + relationships + goals."""

    summary: str = ""
    relationships: List[ArcRelationshipModel] = Field(default_factory=list)
    goals: List[ArcGoalModel] = Field(default_factory=list)


class ArcAnalysisResponse(BaseModel):
    """Structured character arc analysis result."""

    direction: str
    stage: str
    summary: str
    stories_analyzed: int
    updated_at: str
    metrics: Dict[str, ArcMetricModel] = Field(default_factory=dict)
    relationships: List[ArcRelationshipModel] = Field(default_factory=list)
    goals: List[ArcGoalModel] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Shared error envelope returned by all sidecar endpoints on failure."""

    error: str
    detail: str

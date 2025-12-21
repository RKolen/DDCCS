"""
Character Profile Data Model

Refactored with nested dataclasses to organize the 36+ attributes
into logical groupings while maintaining JSON compatibility.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging

from src.characters.character_sheet import DnDClass
from src.utils.file_io import load_json_file, save_json_file
from src.ai.lazy_imports import AIImportManager


# Constants for behavior generation - disabled to avoid 18s delay during loading
try:
    from src.validation.character_validator import validate_character_json

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    validate_character_json = None

# Disable behavior generator to avoid 18+ second AI calls during character loading
# Behavior generation is only for in-memory use and not needed during loading
BEHAVIOUR_GENERATOR_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


@dataclass
class CharacterIdentity:
    """Basic character identity information."""

    name: str
    character_class: DnDClass
    nickname: Optional[str] = None
    level: int = 1
    species: str = "Human"
    lineage: Optional[str] = None
    subclass: Optional[str] = None


@dataclass
class CharacterPersonality:
    """Custom background and personality traits (written by user)."""

    background_story: str = ""
    personality_summary: str = ""
    motivations: List[str] = field(default_factory=list)
    fears_weaknesses: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)


@dataclass
class CharacterBehavior:
    """Class-specific behavior patterns."""

    preferred_strategies: List[str] = field(default_factory=list)
    typical_reactions: Dict[str, str] = field(default_factory=dict)
    speech_patterns: List[str] = field(default_factory=list)
    decision_making_style: str = ""


@dataclass
class CharacterStory:
    """Story integration elements."""

    story_hooks: List[str] = field(default_factory=list)
    character_arcs: List[str] = field(default_factory=list)
    major_plot_actions: List[Any] = field(default_factory=list)


@dataclass
class CharacterStats:
    """Core combat stats."""

    ability_scores: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, Any] = field(default_factory=dict)
    max_hit_points: int = 0
    armor_class: int = 10
    movement_speed: int = 30
    proficiency_bonus: int = 2
    background: str = ""


@dataclass
class CharacterAbilities:
    """Character abilities and powers."""

    feats: List[str] = field(default_factory=list)
    class_abilities: List[str] = field(default_factory=list)
    specialized_abilities: List[str] = field(default_factory=list)
    spell_slots: Dict[str, int] = field(default_factory=dict)
    known_spells: List[str] = field(default_factory=list)


@dataclass
class CharacterPossessions:
    """Character equipment and items."""

    equipment: Dict[str, List[str]] = field(default_factory=dict)
    magic_items: List[str] = field(default_factory=list)


@dataclass
class CharacterMechanics:
    """Game mechanics (stats and abilities)."""

    stats: CharacterStats = field(default_factory=CharacterStats)
    abilities: CharacterAbilities = field(default_factory=CharacterAbilities)


@dataclass
class CharacterProfile:
    """Extended character profile with custom background and consultant capabilities.

    Now organized into logical groupings:
    - identity: Basic character info (name, class, level, species)
    - personality: Background story and character traits
    - behavior: Class-specific behavior patterns
    - story: Story hooks and plot actions
    - mechanics: Game mechanics (stats + abilities)
    - possessions: Equipment and magic items
    """

    identity: CharacterIdentity
    personality: CharacterPersonality = field(default_factory=CharacterPersonality)
    behavior: CharacterBehavior = field(default_factory=CharacterBehavior)
    story: CharacterStory = field(default_factory=CharacterStory)
    mechanics: CharacterMechanics = field(default_factory=CharacterMechanics)
    possessions: CharacterPossessions = field(default_factory=CharacterPossessions)
    ai_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Populate an in-memory `behavior` from personality fields if empty.

        This will call `generate_behavior_from_personality` when available.
        It never writes back to disk; it only mutates the in-memory instance so
        downstream code (consultants, tests) get a sensible `CharacterBehavior`.
        """
        # Behavior generation disabled to avoid 18+ second AI calls during loading.
        # BEHAVIOUR_GENERATOR_AVAILABLE is set to False at module level.
        # This method is kept for API compatibility but performs no operation.
        return

    # Backward compatibility properties for accessing nested dataclass fields
    @property
    def name(self) -> str:
        """Character name."""
        return self.identity.name

    @property
    def character_class(self) -> DnDClass:
        """Character class."""
        return self.identity.character_class

    @property
    def level(self) -> int:
        """Character level."""
        return self.identity.level

    @property
    def species(self) -> str:
        """Character species."""
        return self.identity.species

    @property
    def lineage(self) -> Optional[str]:
        """Character lineage."""
        return self.identity.lineage

    @property
    def subclass(self) -> Optional[str]:
        """Character subclass."""
        return self.identity.subclass

    def get_all_abilities(self) -> List[str]:
        """Get a combined list of all character abilities, spells, and feats."""
        abilities = []
        abilities.extend(self.mechanics.abilities.class_abilities)
        abilities.extend(self.mechanics.abilities.specialized_abilities)
        abilities.extend(self.mechanics.abilities.known_spells)
        abilities.extend(self.mechanics.abilities.feats)
        return [str(a) for a in abilities]

    @property
    def background_story(self) -> str:
        """Character background story."""
        return self.personality.background_story

    @background_story.setter
    def background_story(self, value: str):
        """Set character background story."""
        self.personality.background_story = value

    @property
    def personality_summary(self) -> str:
        """Character personality summary."""
        return self.personality.personality_summary

    @personality_summary.setter
    def personality_summary(self, value: str):
        """Set character personality summary."""
        self.personality.personality_summary = value

    @property
    def motivations(self) -> List[str]:
        """Character motivations."""
        return self.personality.motivations

    @property
    def fears_weaknesses(self) -> List[str]:
        """Character fears and weaknesses."""
        return self.personality.fears_weaknesses

    @property
    def goals(self) -> List[str]:
        """Character goals."""
        return self.personality.goals

    @property
    def secrets(self) -> List[str]:
        """Character secrets."""
        return self.personality.secrets

    @property
    def relationships(self) -> Dict[str, str]:
        """Character relationships."""
        return self.personality.relationships

    @property
    def equipment(self) -> Dict[str, List[str]]:
        """Character equipment."""
        return self.possessions.equipment

    @property
    def magic_items(self) -> List[str]:
        """Character magic items."""
        return self.possessions.magic_items

    @property
    def ability_scores(self) -> Dict[str, int]:
        """Character ability scores."""
        return self.mechanics.stats.ability_scores

    # Note: Top-level accessors for behavior fields were intentionally removed.
    # Callers should use `profile.behavior.<field>` (e.g. profile.behavior.speech_patterns)
    # to access behavior-related properties. This keeps the data model explicit
    # and avoids API surface duplication.

    @staticmethod
    def _update_if_exists(data: Dict[str, Any], key: str, value: Any) -> None:
        """Update data dict key only if key exists in data and value is not empty."""
        if key in data and value:
            data[key] = value

    def save_to_file(self, filepath: str):
        """Save character profile to JSON file.

        Preserves original file structure and all existing fields.
        Only updates the fields managed by CharacterProfile.
        """
        # Load existing data to preserve unknown fields and original structure
        try:
            data = load_json_file(filepath)
        except (FileNotFoundError, ValueError):
            data = {}

        # Update all managed fields in data dict
        if data is None:
            data = {}
        self._update_all_fields(data)

        # Validate before saving
        if VALIDATOR_AVAILABLE and validate_character_json:
            is_valid, errors = validate_character_json(data, filepath)
            if not is_valid:
                print("[WARNING]  Character profile validation failed:")
                for error in errors:
                    print(f"  - {error}")
                print("  Saving anyway, but please fix these issues.")

        save_json_file(filepath, data)

    def _update_identity_fields(self, data: Dict[str, Any]) -> None:
        """Update identity fields in data dict."""
        data["name"] = self.identity.name
        data["nickname"] = self.identity.nickname
        data["dnd_class"] = self.identity.character_class.value
        data["level"] = self.identity.level
        data["species"] = self.identity.species
        data["lineage"] = self.identity.lineage
        data["subclass"] = self.identity.subclass

    def _update_personality_fields(self, data: Dict[str, Any]) -> None:
        """Update personality fields in data dict."""
        data["backstory"] = self.personality.background_story
        summary = self.personality.personality_summary
        data["personality_traits"] = summary.split("; ") if summary else []
        data["bonds"] = self.personality.motivations
        data["flaws"] = self.personality.fears_weaknesses
        data["ideals"] = self.personality.goals
        data["relationships"] = self.personality.relationships
        if "secrets" in data:
            data["secrets"] = self.personality.secrets

    def _update_mechanics_fields(self, data: Dict[str, Any]) -> None:
        """Update mechanics fields in data dict."""
        data["ability_scores"] = self.mechanics.stats.ability_scores
        data["skills"] = self.mechanics.stats.skills
        data["max_hit_points"] = self.mechanics.stats.max_hit_points
        data["armor_class"] = self.mechanics.stats.armor_class
        data["movement_speed"] = self.mechanics.stats.movement_speed
        data["proficiency_bonus"] = self.mechanics.stats.proficiency_bonus
        if "background" in data and self.mechanics.stats.background:
            data["background"] = self.mechanics.stats.background
        data["feats"] = self.mechanics.abilities.feats
        data["class_abilities"] = self.mechanics.abilities.class_abilities
        data["specialized_abilities"] = self.mechanics.abilities.specialized_abilities
        data["spell_slots"] = self.mechanics.abilities.spell_slots
        data["known_spells"] = self.mechanics.abilities.known_spells

    def _update_all_fields(self, data: Dict[str, Any]) -> None:
        """Update all fields in data dict from character profile."""
        self._update_identity_fields(data)
        self._update_personality_fields(data)

        # Behavior fields - only write if they exist in original data
        self._update_if_exists(
            data, "preferred_strategies", self.behavior.preferred_strategies
        )
        self._update_if_exists(
            data, "typical_reactions", self.behavior.typical_reactions
        )
        self._update_if_exists(data, "speech_patterns", self.behavior.speech_patterns)
        self._update_if_exists(
            data, "decision_making_style", self.behavior.decision_making_style
        )

        # Story fields - only write if they exist in original data
        self._update_if_exists(data, "story_hooks", self.story.story_hooks)
        self._update_if_exists(data, "character_arcs", self.story.character_arcs)
        self._update_if_exists(
            data, "major_plot_actions", self.story.major_plot_actions
        )

        self._update_mechanics_fields(data)

        # Possessions fields
        data["equipment"] = self.possessions.equipment
        data["magic_items"] = self.possessions.magic_items

        # AI config - only update if it exists in original data
        if "ai_config" in data and self.ai_config:
            AIImportManager.ensure_loaded()
            config_class = AIImportManager.get_character_ai_config()
            if AIImportManager.get_ai_available() and config_class is not None:
                # Preserve original structure, only update changed values
                original_ai_config = data["ai_config"]
                # Cast to Any to allow dynamic attribute access
                ai_config_obj: Any = self.ai_config
                if hasattr(ai_config_obj, "to_dict"):
                    updated = ai_config_obj.to_dict()
                    # Only update fields that existed in the original
                    for key in original_ai_config:
                        if key in updated:
                            original_ai_config[key] = updated[key]
                else:
                    data["ai_config"] = self.ai_config
            elif self.ai_config:
                data["ai_config"] = self.ai_config

    @classmethod
    def _load_mechanics_from_data(cls, data: Dict[str, Any]) -> CharacterMechanics:
        """Helper to load mechanics section from data dict."""
        stats = CharacterStats(
            ability_scores=data.get("ability_scores", {}),
            skills=data.get("skills", {}),
            max_hit_points=data.get("max_hit_points", 0),
            armor_class=data.get("armor_class", 10),
            movement_speed=data.get("movement_speed", 30),
            proficiency_bonus=data.get("proficiency_bonus", 2),
            background=data.get("background", ""),
        )
        abilities = CharacterAbilities(
            feats=data.get("feats", []),
            class_abilities=data.get("class_abilities", []),
            specialized_abilities=data.get("specialized_abilities", []),
            spell_slots=data.get("spell_slots", {}),
            known_spells=data.get("known_spells", []),
        )
        return CharacterMechanics(stats=stats, abilities=abilities)

    @classmethod
    def _load_ai_config_from_data(cls, data: Dict[str, Any]) -> Optional[Any]:
        """Helper to load AI config from data dict with lazy imports."""
        if not isinstance(data, dict) or "ai_config" not in data:
            return None

        AIImportManager.ensure_loaded()
        if AIImportManager.get_ai_available():
            config_class = AIImportManager.get_character_ai_config()
            if config_class is not None:
                ai_config_obj: Any = config_class.from_dict(data["ai_config"])
                if hasattr(ai_config_obj, "to_dict"):
                    return ai_config_obj.to_dict()
                return dict(data["ai_config"])
        return data.get("ai_config")

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load character profile from JSON file."""
        data = load_json_file(filepath)

        # Ensure data is a dict
        if not isinstance(data, dict):
            data = {}

        # Ensure nickname is present (can be None)
        if "nickname" not in data:
            data["nickname"] = None

        # Handle both 'character_class' and 'dnd_class' field names
        character_class_name = (
            data.get("dnd_class") or data.get("character_class") or "fighter"
        )

        try:
            character_class = DnDClass(character_class_name)
        except ValueError:
            character_class = DnDClass.FIGHTER

        # Create identity
        identity = CharacterIdentity(
            name=data.get("name", "Unknown"),
            character_class=character_class,
            nickname=data.get("nickname"),
            level=data.get("level", 1),
            species=data.get("species", "Human"),
            lineage=data.get("lineage"),
            subclass=data.get("subclass"),
        )

        # Create personality (map field names)
        personality = CharacterPersonality(
            background_story=data.get("backstory", data.get("background_story", "")),
            personality_summary="; ".join(data.get("personality_traits", [])),
            motivations=data.get("bonds", data.get("motivations", [])),
            fears_weaknesses=data.get("flaws", data.get("fears_weaknesses", [])),
            relationships=data.get("relationships", {}),
            goals=data.get("ideals", data.get("goals", [])),
            secrets=data.get("secrets", []),
        )

        # Create behavior
        behavior = CharacterBehavior(
            preferred_strategies=data.get("preferred_strategies", []),
            typical_reactions=data.get("typical_reactions", {}),
            speech_patterns=data.get("speech_patterns", []),
            decision_making_style=data.get("decision_making_style", ""),
        )

        # Create story
        story = CharacterStory(
            story_hooks=data.get("story_hooks", []),
            character_arcs=data.get("character_arcs", []),
            major_plot_actions=data.get("major_plot_actions", []),
        )

        # Load mechanics and possessions
        mechanics = cls._load_mechanics_from_data(data)
        possessions = CharacterPossessions(
            equipment=data.get("equipment", {}),
            magic_items=data.get("magic_items", []),
        )

        # Load AI configuration if present
        ai_config = cls._load_ai_config_from_data(data)

        return cls(
            identity=identity,
            personality=personality,
            behavior=behavior,
            story=story,
            mechanics=mechanics,
            possessions=possessions,
            ai_config=ai_config,
        )

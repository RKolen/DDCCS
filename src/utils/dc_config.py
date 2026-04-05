"""DC scaling configuration management."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.dnd_rules import DifficultyTier, ScalingMode, get_dc_for_difficulty

DEFAULT_DC_CONFIG_PATH = "game_data/dc_config.json"

# Default enabled-scaling flags used for serialization / deserialization
_DEFAULT_CONTEXT_SCALING: Dict[str, bool] = {
    "combat": True,
    "social": True,
    "exploration": True,
}


@dataclass
class DCConfig:
    """Configuration for DC scaling behaviour.

    Attributes:
        scaling_mode: Algorithm used to scale DCs with level.
        default_difficulty: Fallback difficulty tier when none is specified.
        custom_dc_overrides: Per-check-type DC overrides that bypass scaling.
        difficulty_modifiers: Per-check-type additive adjustments applied after scaling.
        party_level_override: Forces a fixed party level (None = use actual level).
        context_scaling: Enabled/disabled flags keyed by context name
            (``"combat"``, ``"social"``, ``"exploration"``).
    """

    scaling_mode: ScalingMode = ScalingMode.TIERED
    default_difficulty: DifficultyTier = DifficultyTier.MEDIUM
    custom_dc_overrides: Dict[str, int] = field(default_factory=dict)
    difficulty_modifiers: Dict[str, int] = field(default_factory=dict)
    party_level_override: Optional[int] = None
    context_scaling: Dict[str, bool] = field(
        default_factory=lambda: dict(_DEFAULT_CONTEXT_SCALING)
    )

    def get_dc(
        self,
        check_type: str,
        level: Optional[int] = None,
        difficulty: Optional[DifficultyTier] = None,
    ) -> int:
        """Get configured DC for a check.

        Args:
            check_type: Type of check being made.
            level: Character or party level.
            difficulty: Desired difficulty tier (defaults to configured default).

        Returns:
            Configured DC value (minimum 1).
        """
        if check_type in self.custom_dc_overrides:
            return self.custom_dc_overrides[check_type]

        effective_difficulty = difficulty or self.default_difficulty
        effective_level = self.party_level_override or level

        base_dc = get_dc_for_difficulty(
            effective_difficulty,
            effective_level,
            self.scaling_mode,
        )

        modifier = self.difficulty_modifiers.get(check_type, 0)
        return max(1, base_dc + modifier)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation of this configuration.
        """
        return {
            "scaling_mode": self.scaling_mode.value,
            "default_difficulty": self.default_difficulty.value,
            "custom_dc_overrides": self.custom_dc_overrides,
            "difficulty_modifiers": self.difficulty_modifiers,
            "party_level_override": self.party_level_override,
            "combat_scaling_enabled": self.context_scaling.get("combat", True),
            "social_scaling_enabled": self.context_scaling.get("social", True),
            "exploration_scaling_enabled": self.context_scaling.get("exploration", True),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DCConfig":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with configuration values.

        Returns:
            DCConfig instance populated from data.
        """
        return cls(
            scaling_mode=ScalingMode(data.get("scaling_mode", "tiered")),
            default_difficulty=DifficultyTier(data.get("default_difficulty", "medium")),
            custom_dc_overrides=data.get("custom_dc_overrides", {}),
            difficulty_modifiers=data.get("difficulty_modifiers", {}),
            party_level_override=data.get("party_level_override"),
            context_scaling={
                "combat": data.get("combat_scaling_enabled", True),
                "social": data.get("social_scaling_enabled", True),
                "exploration": data.get("exploration_scaling_enabled", True),
            },
        )

    def save(self, filepath: str) -> None:
        """Save configuration to a JSON file.

        Args:
            filepath: Path to the output file.
        """
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "DCConfig":
        """Load configuration from a JSON file, returning defaults if absent.

        Args:
            filepath: Path to the configuration file.

        Returns:
            DCConfig loaded from file, or default DCConfig if file not found.
        """
        path = Path(filepath)
        if not path.exists():
            return cls()
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)


def get_dc_config() -> DCConfig:
    """Load and return the current DC configuration.

    Returns:
        DCConfig loaded from the default config path.
    """
    return DCConfig.load(DEFAULT_DC_CONFIG_PATH)

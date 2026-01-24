"""
NPC Agent class and loader for recurring NPCs.
"""

from pathlib import Path
from src.characters.character_sheet import NPCProfile
from src.utils.file_io import load_json_file

# Import AI client if available
try:
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class NPCAgent:
    """Agent for managing and consulting on NPCs."""

    def __init__(self, profile: NPCProfile, ai_client=None):
        """
        Initialize an NPCAgent with a profile and optional AI client.

        Args:
            profile (NPCProfile): The NPC profile dataclass instance.
            ai_client: Optional AI client for advanced features.
        """
        self.profile = profile
        self.ai_client = ai_client
        self._npc_ai_client = None
        self.memory = []  # Optional: track NPC events/interactions

    def get_status(self):
        """
        Return a dictionary summary of the NPC's current status and attributes.

        Includes combat stats and class information for full profiles.
        """
        status = {
            "name": self.profile.name,
            "role": self.profile.role,
            "species": self.profile.species,
            "lineage": self.profile.lineage,
            "personality": self.profile.personality,
            "relationships": self.profile.relationships,
            "key_traits": self.profile.key_traits,
            "abilities": self.profile.abilities,
            "recurring": self.profile.recurring,
            "notes": self.profile.notes,
            "profile_type": self.profile.profile_type,
            "faction": self.profile.faction,
        }

        # Add full character profile information if available
        if self.profile.is_full_profile():
            stats = self.profile.combat_stats
            status.update(
                {
                    "class": stats.dnd_class,
                    "subclass": stats.subclass,
                    "level": stats.level,
                    "ability_scores": stats.combat.ability_scores,
                    "max_hit_points": stats.combat.max_hit_points,
                    "armor_class": stats.combat.armor_class,
                    "movement_speed": stats.combat.movement_speed,
                    "proficiency_bonus": stats.combat.proficiency_bonus,
                    "equipment": stats.abilities.equipment,
                    "known_spells": stats.abilities.spellcraft.known_spells,
                    "class_abilities": stats.abilities.class_abilities,
                }
            )

        return status

    def add_to_memory(self, event: str):
        """
        Add an event to the NPC's memory log, keeping only the last 50 events.

        Args:
            event (str): Description of the event to add.
        """
        self.memory.append(event)
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]


def load_npc_from_json(json_path: Path) -> NPCProfile:
    """Load an NPC from a JSON file.

    Supports both simplified and full character profiles.
    """
    data = load_json_file(str(json_path))

    # Get profile type (default to simplified for backward compatibility)
    profile_type = data.get("profile_type", "simplified")

    # Base NPC fields (common to both profile types)
    base_kwargs = {
        "name": data.get("name", ""),
        "nickname": data.get("nickname"),
        "role": data.get("role", "NPC"),
        "species": data.get("species", "Human"),
        "lineage": data.get("lineage", ""),
        "personality": data.get("personality", ""),
        "relationships": data.get("relationships", {}),
        "key_traits": data.get("key_traits", []),
        "abilities": data.get("abilities", []),
        "recurring": data.get("recurring", False),
        "notes": data.get("notes", ""),
        "profile_type": profile_type,
        "faction": data.get("faction", "neutral"),
    }

    # Add full character profile fields if present
    if profile_type == "full":
        base_kwargs.update(
            {
                "dnd_class": data.get("dnd_class"),
                "subclass": data.get("subclass"),
                "level": data.get("level"),
                "ability_scores": data.get("ability_scores"),
                "skills": data.get("skills"),
                "max_hit_points": data.get("max_hit_points"),
                "armor_class": data.get("armor_class"),
                "movement_speed": data.get("movement_speed"),
                "proficiency_bonus": data.get("proficiency_bonus"),
                "equipment": data.get("equipment"),
                "spell_slots": data.get("spell_slots"),
                "known_spells": data.get("known_spells"),
                "background": data.get("background"),
                "personality_traits": data.get("personality_traits"),
                "ideals": data.get("ideals"),
                "bonds": data.get("bonds"),
                "flaws": data.get("flaws"),
                "backstory": data.get("backstory"),
                "feats": data.get("feats"),
                "magic_items": data.get("magic_items"),
                "class_abilities": data.get("class_abilities"),
                "specialized_abilities": data.get("specialized_abilities"),
                "major_plot_actions": data.get("major_plot_actions"),
            }
        )

    profile = NPCProfile.create(**base_kwargs)

    # Load AI configuration if present
    if data is not None and "ai_config" in data:
        profile.ai_config = data["ai_config"]

    return profile


def create_npc_agents(npcs_dir: Path, ai_client=None) -> list:
    """Create NPCAgent objects for all NPC JSON files in the directory."""
    agents = []
    for npc_file in npcs_dir.glob("*.json"):
        # Skip example files
        if npc_file.name.startswith("npc.example"):
            continue
        profile = load_npc_from_json(npc_file)
        agents.append(NPCAgent(profile, ai_client=ai_client))
    return agents

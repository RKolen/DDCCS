"""
NPC Agent class and loader for recurring NPCs.
"""

from pathlib import Path

from src.characters.character_sheet import NPCProfile
from src.utils.file_io import load_json_file

# Import AI client if available
try:
    from src.ai.ai_client import CharacterAIConfig
    AI_AVAILABLE = True
except ImportError:
    CharacterAIConfig = None
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
        """
        return {
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
        }

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
    """Load an NPC from a JSON file."""
    data = load_json_file(str(json_path))

    profile = NPCProfile(
        name=data.get("name", ""),
        nickname=data.get("nickname", None),
        role=data.get("role", "NPC"),
        species=data.get("species", "Human"),
        lineage=data.get("lineage", ""),
        personality=data.get("personality", ""),
        relationships=data.get("relationships", {}),
        key_traits=data.get("key_traits", []),
        abilities=data.get("abilities", []),
        recurring=data.get("recurring", False),
        notes=data.get("notes", ""),
    )

    # Load AI configuration if present
    if "ai_config" in data and AI_AVAILABLE:
        profile.ai_config = CharacterAIConfig.from_dict(data["ai_config"])
    elif "ai_config" in data:
        # Store as dict if AI not available
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

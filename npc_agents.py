"""
NPC Agent class and loader for recurring NPCs.
"""

import json
from pathlib import Path
from character_sheet import NPCProfile

# Import AI client if available
try:
    from ai_client import AIClient, CharacterAIConfig
    AI_AVAILABLE = True
except ImportError:
    AIClient = None
    CharacterAIConfig = None
    AI_AVAILABLE = False

class NPCAgent:
    """Agent for managing and consulting on NPCs."""
    def __init__(self, profile: NPCProfile, ai_client=None):
        self.profile = profile
        self.ai_client = ai_client
        self._npc_ai_client = None
        self.memory = []  # Optional: track NPC events/interactions

    def get_status(self):
        return {
            "name": self.profile.name,
            "role": self.profile.role,
            "personality": self.profile.personality,
            "relationships": self.profile.relationships,
            "key_traits": self.profile.key_traits,
            "abilities": self.profile.abilities,
            "recurring": self.profile.recurring,
            "notes": self.profile.notes
        }

    def add_to_memory(self, event: str):
        self.memory.append(event)
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]


def load_npc_from_json(json_path: Path) -> NPCProfile:
    """Load an NPC from a JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    profile = NPCProfile(
        name=data.get("name", ""),
        role=data.get("role", "NPC"),
        personality=data.get("personality", ""),
        relationships=data.get("relationships", {}),
        key_traits=data.get("key_traits", []),
        abilities=data.get("abilities", []),
        recurring=data.get("recurring", False),
        notes=data.get("notes", "")
    )
    
    # Load AI configuration if present
    if 'ai_config' in data and AI_AVAILABLE:
        profile.ai_config = CharacterAIConfig.from_dict(data['ai_config'])
    elif 'ai_config' in data:
        # Store as dict if AI not available
        profile.ai_config = data['ai_config']
    
    return profile


def create_npc_agents(npcs_dir: Path, ai_client=None) -> list:
    """Create NPCAgent objects for all NPC JSON files in the directory."""
    agents = []
    for npc_file in npcs_dir.glob("*.json"):
        # Skip example files
        if npc_file.name.startswith('npc.example'):
            continue
        profile = load_npc_from_json(npc_file)
        agents.append(NPCAgent(profile, ai_client=ai_client))
    return agents

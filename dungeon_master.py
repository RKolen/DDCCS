"""
Dungeon Master Consultant - Provides narrative suggestions based on user prompts.
Integrates with character and NPC agents for coherent storytelling.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from character_consultants import CharacterConsultant
from npc_agents import NPCAgent, create_npc_agents


class DMConsultant:
    """AI consultant that provides DM narrative suggestions based on user prompts."""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.character_consultants = self._load_character_consultants()
        self.npc_agents = self._load_npc_agents()
        self.narrative_style = "immersive"  # immersive, cinematic, descriptive
        
    def _load_character_consultants(self) -> Dict[str, CharacterConsultant]:
        """Load all character consultants from the characters folder."""
        consultants = {}
        characters_dir = self.workspace_path / "characters"
        if characters_dir.exists():
            for char_file in characters_dir.glob("*.json"):
                consultant = CharacterConsultant.load_from_file(char_file)
                consultants[consultant.profile.name] = consultant
        return consultants
        
    def _load_npc_agents(self) -> Dict[str, NPCAgent]:
        """Load all NPC agents from the npcs folder."""
        agents = {}
        npcs_dir = self.workspace_path / "npcs"
        if npcs_dir.exists():
            npc_agent_list = create_npc_agents(npcs_dir)
            for agent in npc_agent_list:
                agents[agent.profile.name] = agent
        return agents
    
    def suggest_narrative(self, user_prompt: str, characters_present: List[str] = None, npcs_present: List[str] = None) -> Dict[str, Any]:
        """Generate narrative suggestions based on user prompt and present characters/NPCs."""
        characters_present = characters_present or []
        npcs_present = npcs_present or []
        
        # Get character insights for present characters
        character_insights = {}
        for char_name in characters_present:
            if char_name in self.character_consultants:
                consultant = self.character_consultants[char_name]
                reaction = consultant.suggest_reaction(user_prompt, {})
                character_insights[char_name] = {
                    "likely_reaction": reaction["suggested_reaction"],
                    "reasoning": reaction["reasoning"],
                    "class_expertise": reaction.get("class_expertise", "")
                }
        
        # Get NPC insights for present NPCs
        npc_insights = {}
        for npc_name in npcs_present:
            if npc_name in self.npc_agents:
                agent = self.npc_agents[npc_name]
                npc_insights[npc_name] = {
                    "personality": agent.profile.personality,
                    "role": agent.profile.role,
                    "relationships": agent.profile.relationships,
                    "likely_behavior": self._suggest_npc_behavior(agent.profile, user_prompt)
                }
        
        # Generate narrative suggestions
        narrative_suggestions = self._generate_narrative_suggestions(
            user_prompt, character_insights, npc_insights
        )
        
        return {
            "user_prompt": user_prompt,
            "character_insights": character_insights,
            "npc_insights": npc_insights,
            "narrative_suggestions": narrative_suggestions,
            "consistency_notes": self._check_consistency(characters_present, npcs_present, user_prompt)
        }
    
    def _suggest_npc_behavior(self, npc_profile, situation: str) -> str:
        """Suggest how an NPC would behave in the given situation."""
        personality = npc_profile.personality.lower()
        
        if "friendly" in personality:
            return "Would likely be helpful and accommodating"
        elif "hostile" in personality or "aggressive" in personality:
            return "Would likely be confrontational or suspicious"
        elif "mysterious" in personality:
            return "Would speak in riddles or reveal information cryptically"
        elif "merchant" in npc_profile.role.lower():
            return "Would try to turn the situation into a business opportunity"
        else:
            return "Would react cautiously but politely"
    
    def _generate_narrative_suggestions(self, prompt: str, char_insights: Dict, npc_insights: Dict) -> List[str]:
        """Generate multiple narrative direction suggestions."""
        suggestions = []
        
        # Base narrative suggestion
        suggestions.append(f"Setting the scene: {self._create_scene_description(prompt)}")
        
        # Character-driven suggestions
        if char_insights:
            char_names = list(char_insights.keys())
            suggestions.append(f"Character focus: Highlight {char_names[0]}'s expertise in this situation")
            
        # NPC-driven suggestions  
        if npc_insights:
            npc_names = list(npc_insights.keys())
            suggestions.append(f"NPC interaction: {npc_names[0]} could provide crucial information or complications")
            
        # Tension/conflict suggestions
        suggestions.append("Add tension: Introduce a time constraint or moral dilemma")
        suggestions.append("Character development: Create an opportunity for character growth")
        
        return suggestions
    
    def _create_scene_description(self, prompt: str) -> str:
        """Create a brief scene description based on the prompt."""
        if "tavern" in prompt.lower():
            return "The warm glow of the hearth casts dancing shadows across weathered faces"
        elif "dungeon" in prompt.lower():
            return "Ancient stone walls echo with the party's footsteps and distant dripping"
        elif "forest" in prompt.lower():
            return "Dappled sunlight filters through the canopy as leaves rustle overhead"
        elif "town" in prompt.lower():
            return "Bustling streets filled with merchants, guards, and curious onlookers"
        else:
            return "The party finds themselves in a situation requiring careful consideration"
    
    def _check_consistency(self, characters: List[str], npcs: List[str], situation: str) -> List[str]:
        """Check for potential consistency issues with character/NPC behavior."""
        notes = []
        
        # Check character consistency
        for char_name in characters:
            if char_name in self.character_consultants:
                consultant = self.character_consultants[char_name]
                # Add consistency check based on established personality
                if hasattr(consultant.profile, 'personality_summary'):
                    notes.append(f"{char_name}: Remember their {consultant.profile.personality_summary}")
        
        # Check NPC relationships
        for npc_name in npcs:
            if npc_name in self.npc_agents:
                agent = self.npc_agents[npc_name]
                for char_name in characters:
                    if char_name in agent.profile.relationships:
                        relationship = agent.profile.relationships[char_name]
                        notes.append(f"{npc_name} and {char_name}: {relationship}")
        
        return notes
    
    def get_available_npcs(self) -> List[str]:
        """Get list of available NPC names."""
        return list(self.npc_agents.keys())
    
    def get_available_characters(self) -> List[str]:
        """Get list of available character names."""
        return list(self.character_consultants.keys())
    
    def suggest_npc_interaction(self, npc_name: str, situation: str) -> Dict[str, Any]:
        """Get specific suggestions for how an NPC would react in a situation."""
        if npc_name not in self.npc_agents:
            return {"error": f"NPC '{npc_name}' not found"}
        
        agent = self.npc_agents[npc_name]
        suggested_behavior = self._suggest_npc_behavior(agent.profile, situation)
        
        return {
            "npc_name": npc_name,
            "personality": agent.profile.personality,
            "role": agent.profile.role,
            "suggested_behavior": suggested_behavior,
            "relationships": agent.profile.relationships,
            "situation": situation
        }
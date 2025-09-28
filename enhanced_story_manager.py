"""
Enhanced Story Management System with User Choice and Character Agent Integration
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from character_consultants import CharacterConsultant, CharacterProfile
from character_sheet import DnDClass


def load_current_party(config_path: str = "current_party.json") -> List[str]:
    """Load current party members from configuration file."""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('party_members', [])
        except Exception as e:
            print(f"Warning: Could not load party configuration: {e}")
    
    # Return default party if no config found
    return ["Zilvra Baenre", "Kaelen Moonshadow", "Brogan 'Saltshadow' Ironfist", "Alina Gristvale"]


def save_current_party(party_members: List[str], config_path: str = "current_party.json"):
    """Save current party members to configuration file."""
    data = {
        'party_members': party_members,
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[SUCCESS] Saved party configuration to {config_path}")
    except Exception as e:
        print(f"Error saving party configuration: {e}")


class StorySession:
    """Represents a single story session with results separate from narrative."""
    
    def __init__(self, story_name: str, session_date: str = None):
        self.story_name = story_name
        self.session_date = session_date or datetime.now().strftime("%Y-%m-%d")
        self.roll_results = []
        self.character_actions = []
        self.narrative_events = []
        self.recruiting_pool = []
    
    def add_roll_result(self, character: str, action: str, roll_type: str, roll_value: int, dc: int, outcome: str):
        """Add a roll result to this session."""
        self.roll_results.append({
            "character": character,
            "action": action,
            "roll_type": roll_type,
            "roll_value": roll_value,
            "dc": dc,
            "success": roll_value >= dc,
            "outcome": outcome
        })
    
    def suggest_recruits_from_agents(self, story_manager, exclude_names: List[str]) -> List[str]:
        """Suggest recruit characters from existing character agents."""
        available_agents = []
        for name, consultant in story_manager.consultants.items():
            if name not in exclude_names:
                available_agents.append({
                    "name": name,
                    "class": consultant.profile.character_class.value,
                    "personality": consultant.profile.personality_summary,
                    "level": consultant.profile.level
                })
        return available_agents


class EnhancedStoryManager:
    """Enhanced story manager with user choice and better organization."""
    
    def __init__(self, workspace_path: str, party_config_path: str = None):
        self.workspace_path = workspace_path
        self.stories_path = workspace_path
        self.characters_path = os.path.join(workspace_path, "characters")
        self.party_config_path = party_config_path or os.path.join(workspace_path, "current_party.json")
        self.consultants = {}
        
        # Ensure directories exist
        os.makedirs(self.characters_path, exist_ok=True)
        
        # Load existing characters
        self._load_characters()
    
    def get_current_party(self) -> List[str]:
        """Get current party members from configuration."""
        return load_current_party(self.party_config_path)
    
    def set_current_party(self, party_members: List[str]):
        """Set current party members and save to configuration."""
        save_current_party(party_members, self.party_config_path)
    
    def add_party_member(self, character_name: str):
        """Add a character to the current party."""
        current_party = self.get_current_party()
        if character_name not in current_party:
            current_party.append(character_name)
            self.set_current_party(current_party)
            print(f"[SUCCESS] Added {character_name} to the party")
        else:
            print(f"[WARNING] {character_name} is already in the party")
    
    def remove_party_member(self, character_name: str):
        """Remove a character from the current party."""
        current_party = self.get_current_party()
        if character_name in current_party:
            current_party.remove(character_name)
            self.set_current_party(current_party)
            print(f"[SUCCESS] Removed {character_name} from the party")
        else:
            print(f"[WARNING] {character_name} is not in the party")
    
    def _load_characters(self):
        """Load all character profiles and create consultants."""
        if not os.path.exists(self.characters_path):
            return
        
        for filename in os.listdir(self.characters_path):
            # Skip template and example files
            if (filename.endswith('.json') and 
                not filename.startswith('class.example') and 
                not filename.endswith('.example.json') and
                not filename.startswith('template')):
                
                filepath = os.path.join(self.characters_path, filename)
                try:
                    profile = CharacterProfile.load_from_file(filepath)
                    self.consultants[profile.name] = CharacterConsultant(profile)
                except Exception as e:
                    print(f"Warning: Could not load character {filename}: {e}")
    
    def should_create_new_story_file(self, series_name: str, session_results: StorySession) -> bool:
        """Ask user if they want to create a new story file or continue existing one."""
        print(f"\\nSession results for '{session_results.story_name}':")
        print(f"- {len(session_results.roll_results)} dice rolls recorded")
        print(f"- {len(session_results.character_actions)} character actions")
        print(f"- {len(session_results.narrative_events)} story events")
        
        while True:
            choice = input("\\nCreate new story file? (y/n/continue): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            elif choice in ['c', 'continue']:
                return self._continue_existing_story(series_name)
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'continue' to update existing file")
    
    def _continue_existing_story(self, series_name: str) -> bool:
        """Handle continuing an existing story file."""
        existing_stories = self.get_story_files_in_series(series_name)
        if not existing_stories:
            print("No existing stories found. Creating new file.")
            return True
        
        print("\\nExisting stories:")
        for i, story in enumerate(existing_stories, 1):
            print(f"{i}. {story}")
        
        try:
            choice = int(input("\\nSelect story to update (number): "))
            if 1 <= choice <= len(existing_stories):
                return False  # Don't create new, update existing
            else:
                print("Invalid choice. Creating new story.")
                return True
        except ValueError:
            print("Invalid input. Creating new story.")
            return True
    
    def get_available_recruits(self, exclude_characters: List[str] = None) -> List[Dict[str, Any]]:
        """Get available character agents for recruitment, excluding current party."""
        if exclude_characters is None:
            exclude_characters = self.get_current_party()
        
        recruits = []
        for name, consultant in self.consultants.items():
            if name not in exclude_characters:
                recruits.append({
                    "name": name,
                    "class": consultant.profile.character_class.value,
                    "level": consultant.profile.level,
                    "personality": consultant.profile.personality_summary,
                    "background": consultant.profile.background_story
                })
        return recruits
    
    def create_pure_story_file(self, series_path: str, story_name: str, narrative_content: str) -> str:
        """Create a story file with pure narrative content only."""
        # Determine story number
        existing_stories = [f for f in os.listdir(series_path) if re.match(r'\\d{3}.*\\.md$', f)]
        if existing_stories:
            last_number = max([int(f[:3]) for f in existing_stories])
            next_number = last_number + 1
        else:
            next_number = 1
        
        # Create filename
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(series_path, filename)
        
        # Write pure narrative
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {story_name}\\n\\n")
            f.write(narrative_content)
        
        print(f"[SUCCESS] Created pure story file: {filename}")
        return filepath
    
    def create_session_results_file(self, series_path: str, session: StorySession) -> str:
        """Create a separate file for session results (rolls, mechanics, etc.)."""
        filename = f"session_results_{session.session_date}_{session.story_name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(series_path, filename)
        
        content = f"""# Session Results: {session.story_name}
**Date:** {session.session_date}

## Roll Results
"""
        for roll in session.roll_results:
            content += f"""
### {roll['character']} - {roll['action']}
- **Roll Type:** {roll['roll_type']}
- **Roll Value:** {roll['roll_value']} vs DC {roll['dc']}
- **Result:** {"SUCCESS" if roll['success'] else "FAILURE"}
- **Outcome:** {roll['outcome']}
"""
        
        if session.recruiting_pool:
            content += "\\n## Available Recruits\\n"
            for recruit in session.recruiting_pool:
                content += f"- **{recruit['name']}** ({recruit['class']}) - {recruit['personality']}\\n"
        
        content += f"""
## Character Actions
"""
        for action in session.character_actions:
            content += f"- {action}\\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SUCCESS] Created session results file: {filename}")
        return filepath


def create_improved_recruitment_system(current_party: List[str] = None):
    """Demonstration of improved recruitment using existing character agents."""
    print("\\n=== IMPROVED RECRUITMENT SYSTEM ===")
    
    story_manager = EnhancedStoryManager(".")
    
    # Use provided party or load from configuration
    if current_party is None:
        current_party = story_manager.get_current_party()
    
    available_recruits = story_manager.get_available_recruits()
    
    print(f"\\nCurrent party: {', '.join(current_party)}")
    print(f"Party size: {len(current_party)}")
    print(f"Available recruits from character agents: {len(available_recruits)}")
    
    if available_recruits:
        print("\\nSuggested recruits based on party needs:")
        for recruit in available_recruits[:3]:  # Show top 3 suggestions
            print(f"- {recruit['name']} ({recruit['class']}) Level {recruit['level']}")
            print(f"  Personality: {recruit['personality']}")
            print(f"  Background: {recruit['background'][:100]}...")
            print()
    else:
        print("\\n[WARNING] No available recruits - all characters are already in the party!")
    
    return available_recruits


if __name__ == "__main__":
    # Demo the improved system
    print("=== PARTY MANAGEMENT DEMO ===")
    
    story_manager = EnhancedStoryManager(".")
    
    # Show current party
    current_party = story_manager.get_current_party()
    print(f"Current party loaded from config: {current_party}")
    
    # Demo recruitment system
    create_improved_recruitment_system()
    
    # Demo party management
    print("\\n=== PARTY MANAGEMENT ===")
    print("Available commands:")
    print("- story_manager.add_party_member('Character Name')")
    print("- story_manager.remove_party_member('Character Name')")
    print("- story_manager.get_current_party()")
    print("- story_manager.set_current_party(['Name1', 'Name2', ...])")
    print("\\nParty configuration is saved to 'current_party.json'")
"""
Enhanced Story Management System with User Choice and Character Agent Integration
"""

import os
import re
import json
import textwrap
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from character_consultants import CharacterConsultant, CharacterProfile
from character_sheet import DnDClass


def wrap_narrative_text(text: str, width: int = 80) -> str:
    """
    Wrap narrative text to specified width while preserving paragraphs.
    
    Args:
        text: The text to wrap
        width: Maximum line width (default 80 characters)
    
    Returns:
        Text wrapped to specified width
    """
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []
    
    for para in paragraphs:
        # Skip if it's a heading or special line
        if para.strip().startswith('#') or para.strip().startswith('**'):
            wrapped_paragraphs.append(para)
        else:
            # Wrap the paragraph
            wrapped = textwrap.fill(para.strip(), width=width)
            wrapped_paragraphs.append(wrapped)
    
    return '\n\n'.join(wrapped_paragraphs)


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
    
    def __init__(self, workspace_path: str, party_config_path: str = None, ai_client=None):
        self.workspace_path = workspace_path
        self.stories_path = workspace_path
        self.characters_path = os.path.join(workspace_path, "characters")
        self.party_config_path = party_config_path or os.path.join(workspace_path, "current_party.json")
        self.ai_client = ai_client  # AI client for enhanced features
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
                    self.consultants[profile.name] = CharacterConsultant(profile, ai_client=self.ai_client)
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
    
    def get_existing_stories(self) -> List[str]:
        """Get existing story files in the root directory (legacy stories)."""
        story_files = []
        for filename in os.listdir(self.stories_path):
            if re.match(r'\d{3}.*\.md$', filename):
                story_files.append(filename)
        
        return sorted(story_files)
    
    def get_story_series(self) -> List[str]:
        """Get available story series (folders with numbered stories)."""
        series_folders = []
        for item in os.listdir(self.stories_path):
            item_path = os.path.join(self.stories_path, item)
            if os.path.isdir(item_path) and not item.startswith('.') and item != 'characters' and item != 'npcs' and item != '__pycache__':
                # Check if folder contains numbered story files
                if any(re.match(r'\d{3}.*\.md$', f) for f in os.listdir(item_path) if f.endswith('.md')):
                    series_folders.append(item)
        
        return sorted(series_folders)
    
    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """Get story files within a specific series folder."""
        series_path = os.path.join(self.stories_path, series_name)
        if not os.path.exists(series_path):
            return []
        
        story_files = []
        for filename in os.listdir(series_path):
            if re.match(r'\d{3}.*\.md$', filename):
                story_files.append(filename)
        
        return sorted(story_files)
    
    def get_story_files(self) -> List[str]:
        """Get all story files in sequence order (legacy method for backward compatibility)."""
        return self.get_existing_stories()
    
    def _validate_series_name(self, series_name: str) -> str:
        """Validate and ensure series name has proper suffix."""
        valid_suffixes = ['_Campaign', '_Quest', '_Story', '_Adventure']
        
        # Check if already has a valid suffix
        for suffix in valid_suffixes:
            if series_name.endswith(suffix):
                return series_name
        
        # Add _Campaign as default suffix
        return f"{series_name}_Campaign"
    
    def create_new_story_series(self, series_name: str, first_story_name: str, description: str = "") -> str:
        """
        Create a new story series in its own folder.
        
        Series name MUST end with: _Campaign, _Quest, _Story, or _Adventure
        """
        # Validate series name has proper suffix
        validated_name = self._validate_series_name(series_name)
        
        # Create series folder
        clean_series_name = re.sub(r'[^a-zA-Z0-9_-]', '_', validated_name)
        series_path = os.path.join(self.stories_path, clean_series_name)
        os.makedirs(series_path, exist_ok=True)
        
        # Create first story in series
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', first_story_name)
        filename = f"001_{clean_name}.md"
        filepath = os.path.join(series_path, filename)
        
        # Create story template
        template = self._create_story_template(first_story_name, description)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"OK Created new story series: {clean_series_name}")
        print(f"OK Created first story: {filename}")
        return filepath
    
    def create_story_in_series(self, series_name: str, story_name: str, description: str = "") -> str:
        """Create a new story in an existing series."""
        series_path = os.path.join(self.stories_path, series_name)
        if not os.path.exists(series_path):
            raise ValueError(f"Story series '{series_name}' does not exist")
        
        # Get existing stories in series to determine next number
        existing_stories = self.get_story_files_in_series(series_name)
        
        if existing_stories:
            last_number = max([int(f[:3]) for f in existing_stories])
            next_number = last_number + 1
        else:
            next_number = 1
        
        # Create filename
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(series_path, filename)
        
        # Create story template
        template = self._create_story_template(story_name, description)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"OK Created new story in {series_name}: {filename}")
        return filepath
    
    def create_new_story(self, story_name: str, description: str = "") -> str:
        """Create a new story file with the next sequence number (for existing/legacy stories in root)."""
        existing_stories = self.get_existing_stories()
        
        # Determine next sequence number
        if existing_stories:
            last_number = max([int(f[:3]) for f in existing_stories])
            next_number = last_number + 1
        else:
            next_number = 1
        
        # Create filename
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(self.stories_path, filename)
        
        # Create story template
        template = self._create_story_template(story_name, description)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"OK Created new story: {filename}")
        return filepath
    
    def _create_story_template(self, story_name: str, description: str, use_template: bool = False) -> str:
        """Create a markdown template for a new story."""
        if use_template:
            # Use full template with guidance
            template_path = os.path.join(self.workspace_path, "story_template.md")
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
                header = f"# {story_name}\n\n**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n**Description:** {description}\n\n---\n"
                return header + template
        
        # Pure narrative template (default)
        return f"# {story_name}\n\n**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n**Description:** {description}\n\n"
    
    def create_pure_narrative_story(self, series_name: str, story_name: str, description: str = "") -> str:
        """Create a story file with pure narrative template (no guidance sections)."""
        # Validate series name has proper suffix
        validated_series_name = self._validate_series_name(series_name)
        
        series_path = os.path.join(self.stories_path, validated_series_name)
        if not os.path.exists(series_path):
            os.makedirs(series_path, exist_ok=True)
        
        # Get existing stories to determine number
        existing_stories = [f for f in os.listdir(series_path) if re.match(r'\d{3}.*\.md$', f)]
        if existing_stories:
            last_number = max([int(f[:3]) for f in existing_stories])
            next_number = last_number + 1
        else:
            next_number = 1
        
        # Create filename
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(series_path, filename)
        
        # Create pure narrative template
        template = self._create_story_template(story_name, description, use_template=False)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"OK Created pure narrative story: {filename}")
        return filepath
    
    def get_character_list(self) -> List[str]:
        """Get list of all character names."""
        return list(self.consultants.keys())
    
    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """Get a specific character's profile."""
        consultant = self.consultants.get(character_name)
        return consultant.profile if consultant else None
    
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
    
    def create_character_development_file(self, series_path: str, story_name: str, character_actions: List[Dict[str, str]], session_date: str = None) -> str:
        """Create a separate file for character development suggestions."""
        if session_date is None:
            session_date = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"character_development_{session_date}_{story_name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(series_path, filename)
        
        content = f"""# Character Development: {story_name}
**Date:** {session_date}

## Character Actions & Reasoning

"""
        for action in character_actions:
            content += f"""### CHARACTER: {action.get('character', 'Unknown')}
**ACTION:** {action.get('action', 'No action recorded')}
**REASONING:** {action.get('reasoning', 'No reasoning provided')}

**Consistency Check:** {action.get('consistency', 'To be analyzed')}
**Development Notes:** {action.get('notes', 'No notes')}

---

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SUCCESS] Created character development file: {filename}")
        return filepath
    
    def detect_npc_suggestions(self, story_content: str) -> List[Dict[str, str]]:
        """
        Detect potential NPCs in story content that might need profiles created.
        
        Args:
            story_content: The story text to analyze
            
        Returns:
            List of dictionaries with NPC suggestions (name, role, context_excerpt)
        """
        import re
        
        suggestions = []
        
        # Get current party names to exclude them
        party_names = self.get_current_party()
        
        # Patterns to find NPCs with roles
        npc_patterns = [
            # "innkeeper named X" or "innkeeper called X" - must have "named" or "called"
            (r'(?:innkeeper|bartender|barkeep)[^.]*?(?:named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Innkeeper'),
            # "X, the innkeeper" - name must come before title
            (r'(?<![.!?]\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:the\s+)?(?:innkeeper|bartender|barkeep)', 'Innkeeper'),
            # "merchant named X"
            (r'(?:merchant|trader|shopkeeper)[^.]*?(?:named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Merchant'),
            # "guard captain X" or "Captain X"
            (r'(?:guard\s+captain|captain)[^.]*?(?:named|called)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Guard Captain'),
            # "blacksmith X" or "X the blacksmith"
            (r'(?:blacksmith|smith)[^.]*?(?:named|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Blacksmith'),
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:the\s+)?(?:blacksmith|smith)', 'Blacksmith'),
        ]
        
        seen_npcs = set()
        
        for pattern, default_role in npc_patterns:
            for match in re.finditer(pattern, story_content):
                npc_name = match.group(1)
                
                # Filter out false positives
                # Exclude common sentence starters and adverbs that might be capitalized
                false_positives = ['the', 'a', 'an', 'suddenly', 'meanwhile', 'however', 'therefore', 'thus', 'then']
                if (npc_name.lower() not in false_positives and 
                    not npc_name.startswith('The ') and
                    npc_name not in party_names and
                    npc_name not in seen_npcs):
                    
                    # Check if NPC profile already exists
                    npc_filename = npc_name.lower().replace(' ', '_').replace("'", '') + '.json'
                    npc_path = os.path.join(self.workspace_path, 'npcs', npc_filename)
                    
                    if not os.path.exists(npc_path):
                        # Get context around the NPC mention
                        start = max(0, match.start() - 100)
                        end = min(len(story_content), match.end() + 100)
                        context = story_content[start:end].strip()
                        
                        suggestions.append({
                            'name': npc_name,
                            'role': default_role,
                            'context_excerpt': context,
                            'filename': npc_filename
                        })
                        seen_npcs.add(npc_name)
        
        return suggestions
    
    def create_story_hooks_file(self, series_path: str, story_name: str, hooks: List[str], session_date: str = None, story_content: str = None) -> str:
        """
        Create a separate file for future story hooks and session suggestions.
        
        Args:
            series_path: Path to campaign folder
            story_name: Name of the story
            hooks: List of story hook strings
            session_date: Date of session (defaults to today)
            story_content: Optional story content to scan for NPC suggestions
        """
        if session_date is None:
            session_date = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"story_hooks_{session_date}_{story_name.lower().replace(' ', '_')}.md"
        filepath = os.path.join(series_path, filename)
        
        content = f"""# Story Hooks & Future Sessions: {story_name}
**Date:** {session_date}

## Unresolved Plot Threads

"""
        for i, hook in enumerate(hooks, 1):
            content += f"{i}. {hook}\n"
        
        # Add NPC suggestions if story content provided
        if story_content:
            npc_suggestions = self.detect_npc_suggestions(story_content)
            
            if npc_suggestions:
                content += "\n## NPC Profile Suggestions\n\n"
                content += "The following NPCs appeared in this session and may warrant profile creation:\n\n"
                
                for npc in npc_suggestions:
                    content += f"### {npc['name']} ({npc['role']})\n\n"
                    content += "**Context:** " + npc['context_excerpt'][:150] + "...\n\n"
                    content += "**To create profile:**\n```python\n"
                    content += f"# Generate profile for {npc['name']}\n"
                    content += f"npc_profile = story_manager.generate_npc_from_story(\n"
                    content += f"    npc_name=\"{npc['name']}\",\n"
                    content += f"    context=story_text,\n"
                    content += f"    role=\"{npc['role']}\"\n"
                    content += f")\n"
                    content += f"story_manager.save_npc_profile(npc_profile)\n"
                    content += f"# This will create: npcs/{npc['filename']}\n"
                    content += "```\n\n"
                    content += f"This NPC could be developed as a recurring character with personality traits, relationships, and story hooks.\n\n"
        
        content += """
## Potential Next Sessions

### Session Ideas
- [Future session idea based on current events]

### NPC Follow-ups
- [NPCs that need attention]

### Location Hooks
- [Places hinted at but not yet explored]

### Faction Developments
- [Faction activities and consequences]

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SUCCESS] Created story hooks file: {filename}")
        if story_content and npc_suggestions:
            print(f"   Added {len(npc_suggestions)} NPC profile suggestion(s)")
        return filepath
    
    def generate_npc_from_story(self, npc_name: str, context: str, role: str = "") -> Dict[str, Any]:
        """
        Generate an NPC profile based on story context using AI.
        
        Args:
            npc_name: Name of the NPC
            context: Story context where NPC appears
            role: Optional role hint (e.g., "innkeeper", "merchant")
            
        Returns:
            NPC profile dictionary ready to save as JSON
        """
        if not self.ai_client:
            # Fallback without AI
            return {
                "name": npc_name,
                "role": role or "NPC",
                "personality": "To be determined",
                "relationships": {},
                "key_traits": [],
                "abilities": [],
                "recurring": False,
                "notes": "Generated placeholder - needs manual customization",
                "ai_config": {
                    "enabled": False,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "system_prompt": ""
                }
            }
        
        try:
            prompt = f"""Based on this story context, generate a detailed D&D NPC profile for {npc_name}.

Story Context:
{context[:1000]}

NPC Name: {npc_name}
{f"Role: {role}" if role else ""}

Generate a JSON profile with:
1. personality: 2-3 sentence personality description
2. key_traits: Array of 3-5 distinctive traits
3. abilities: Array of 2-4 notable skills or abilities
4. recurring: boolean - should this NPC appear again?
5. notes: Any secrets, motivations, or hidden agendas
6. relationships: Object with any mentioned character names as keys

Be specific and D&D-appropriate. Make them memorable and useful for the story.

Return ONLY valid JSON in this format:
{{
  "personality": "description",
  "key_traits": ["trait1", "trait2"],
  "abilities": ["ability1", "ability2"],
  "recurring": true/false,
  "notes": "secrets or notes",
  "relationships": {{}}
}}"""

            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # Try to parse the AI response as JSON
            import json
            # Extract JSON from response (might have markdown code blocks)
            json_text = response.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            npc_data = json.loads(json_text)
            
            # Build complete NPC profile
            npc_profile = {
                "name": npc_name,
                "role": role or npc_data.get("role", "NPC"),
                "personality": npc_data.get("personality", "To be determined"),
                "relationships": npc_data.get("relationships", {}),
                "key_traits": npc_data.get("key_traits", []),
                "abilities": npc_data.get("abilities", []),
                "recurring": npc_data.get("recurring", False),
                "notes": npc_data.get("notes", ""),
                "ai_config": {
                    "_comment": "AI uses centralized .env settings. Set enabled=true for AI-driven dialogue.",
                    "enabled": False,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "system_prompt": f"You are {npc_name}, {npc_data.get('personality', 'an NPC in the story')}."
                }
            }
            
            return npc_profile
            
        except Exception as e:
            print(f"⚠️  AI NPC generation failed: {e}")
            # Return fallback
            return {
                "name": npc_name,
                "role": role or "NPC",
                "personality": "To be determined",
                "relationships": {},
                "key_traits": [],
                "abilities": [],
                "recurring": False,
                "notes": f"AI generation failed: {e}",
                "ai_config": {
                    "enabled": False,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "system_prompt": ""
                }
            }
    
    def save_npc_profile(self, npc_profile: Dict[str, Any]) -> str:
        """
        Save an NPC profile to the npcs/ directory.
        
        Args:
            npc_profile: NPC profile dictionary
            
        Returns:
            Path to saved NPC file
        """
        npcs_path = os.path.join(self.workspace_path, "npcs")
        os.makedirs(npcs_path, exist_ok=True)
        
        # Create filename from name
        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', npc_profile['name'].lower())
        filename = f"{clean_name}.json"
        filepath = os.path.join(npcs_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(npc_profile, f, indent=2)
        
        print(f"[SUCCESS] Saved NPC profile: {filename}")
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
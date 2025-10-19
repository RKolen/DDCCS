# D&D Character Consultant System

A Python-based system for managing D&D##  Documentation

- **[AI Integration Guide](docs/AI_INTEGRATION.md)** - Complete AI setup (Ollama, OpenAI, Anthropic)
- **[RAG Integration Guide](docs/RAG_INTEGRATION.md)** - Deep dive into RAG system and wiki integration
- **[RAG Quick Start](docs/RAG_QUICKSTART.md)** - Fast track to using RAG features
- **[Usage Examples](docs/Test_Example.md)** - See the system in action

> **Note:** Personal documentation and development notes are kept in `docs_personal/` (git-ignored) character consultants with 
VSCode integration for story management and character consistency analysis.

##  What This System Does

- **Unlimited Character Support** - Add as many character JSON files as you need
- **Class Expertise** - Each character can be customized for any D&D class, 
  background, or personality
- **Story Sequence Management** - Write narrative stories in `001*.md` files 
  with 80-character line limits for readability
- **Character Development Tracking** - Separate analytical file 
  (`character_development_suggestions.md`) for CHARACTER/ACTION/REASONING 
  analysis
- **DC Suggestion Engine** - Calculates appropriate challenge difficulties 
  based on character stats and abilities
- **Fantasy Grounds Unity Integration** - Converts combat logs to narrative with auto-generated titles
- **NPC Management** - Track recurring NPCs with relationships and traits
- ** Automatic NPC Detection** - System automatically detects NPCs in stories and suggests profile creation
- **VSCode Integration** - Tasks, settings, and markdown workflow support
- ** AI Integration** - Optional AI/LLM enhancement with OpenAI, Ollama, or any OpenAI-compatible API
- ** RAG System** - Dual wiki integration: campaign lore + D&D 5e rules (items, spells)
- ** Custom Items Registry** - Track homebrew items separately, blocks wiki lookups for custom content

> ** [AI Integration Guide](docs/AI_INTEGRATION.md)** - Complete guide for adding AI capabilities to your characters
> 
> ** [RAG Integration Guide](docs/RAG_INTEGRATION.md)** - Wiki integration for accurate campaign lore in stories

##  What This System Does NOT Do

- Does NOT automate gameplay, dice rolling, or run sessions
- Does NOT generate random encounters or locations
- Does NOT replace your creativity, but it can suggest future plot hooks, NPCs, and story ideas to inspire you

##  Current Project Structure

```
D&D New Beginnings/
├── game_data/              #  ALL YOUR CAMPAIGN DATA (git-ignored except examples)
│   ├── characters/         # Character profile JSON files (unlimited)
│   │   └── class.example.json   # Template for new characters
│   ├── npcs/              # NPC management
│   │   └── npc.example.json    # NPC template
│   ├── items/             # Custom/homebrew item tracking
│   │   ├── custom_items_registry.json         # Your homebrew items
│   │   └── custom_items_registry.example.json # Example homebrew items
│   ├── current_party/     # Party configuration
│   │   ├── current_party.json         # Your active party
│   │   └── current_party.example.json # Example party config
│   └── campaigns/         # All your campaign content
│       ├── Your_Campaign/ # Campaign folders (_Campaign, _Quest, _Story, _Adventure)
│       │   ├── 001_First_Story.md
│       │   ├── 002_Next_Story.md
│       │   ├── session_results_*.md
│       │   ├── character_development_*.md
│       │   └── story_hooks_*.md
│       └── Another_Quest/ # Multiple campaigns supported
├── docs/                  #  Public documentation
│   ├── AI_INTEGRATION.md  # Complete AI setup guide
│   ├── RAG_INTEGRATION.md # RAG system deep dive
│   ├── RAG_QUICKSTART.md  # Quick start for RAG
│   └── Test_Example.md    # Usage examples
├── src/                   # All source code (modular architecture)
│   ├── characters/        # Character management system
│   │   ├── consultants/   # Character consultant system (12 D&D classes)
│   │   ├── character_sheet.py       # D&D character data structures
│   │   └── character_consistency.py # Character consistency checking
│   ├── npcs/              # NPC management system
│   │   ├── npc_agents.py           # NPC AI agents
│   │   └── npc_auto_detection.py   # Automatic NPC detection
│   ├── stories/           # Story management system
│   │   ├── story_manager.py            # Core story management
│   │   ├── enhanced_story_manager.py   # Advanced story features
│   │   ├── story_analyzer.py           # Story analysis
│   │   └── session_results_manager.py  # Session results tracking
│   ├── combat/            # Combat system
│   │   ├── combat_narrator.py          # Combat narration
│   │   ├── narrator_ai.py              # AI-enhanced narration
│   │   ├── narrator_descriptions.py    # Combat descriptions
│   │   └── narrator_consistency.py     # Character consistency
│   ├── items/             # Items and inventory system
│   │   └── item_registry.py        # Custom items registry
│   ├── dm/                # Dungeon Master tools
│   │   ├── dungeon_master.py       # DM consultant
│   │   └── history_check_helper.py # History check helper
│   ├── validation/        # Data validation system
│   │   ├── character_validator.py  # Character JSON validation
│   │   ├── npc_validator.py        # NPC JSON validation
│   │   ├── items_validator.py      # Items JSON validation
│   │   ├── party_validator.py      # Party config validation
│   │   └── validate_all.py         # Unified validator
│   ├── ai/                # AI integration
│   │   ├── ai_client.py           # AI client interface
│   │   └── rag_system.py          # RAG system
│   ├── utils/             # Shared utilities
│   │   ├── dnd_rules.py            # D&D 5e game rules
│   │   ├── file_io.py              # File operations
│   │   ├── spell_highlighter.py    # Spell detection
│   │   └── text_formatting_utils.py # Text formatting
│   └── cli/               # Command-line interface
│       ├── dnd_consultant.py       # Main interactive CLI
│       ├── setup.py                # Workspace initialization
│       ├── cli_character_manager.py # Character operations
│       ├── cli_story_manager.py     # Story management
│       ├── cli_consultations.py     # Character consultations
│       └── cli_story_analysis.py    # Story analysis
├── tests/                 #  Test suite (6/6 passing, 10.00/10 pylint)
│   ├── validation/        # JSON validation tests
│   ├── ai/                # AI integration tests
│   ├── test_helpers.py    # Shared test utilities
│   ├── run_all_tests.py   # Unified test runner
│   └── README.md          # Test suite documentation
├── docs/                  #  Public documentation
│   ├── AI_INTEGRATION.md  # Complete AI setup guide
│   ├── RAG_INTEGRATION.md # RAG system deep dive
│   ├── RAG_QUICKSTART.md  # Quick start for RAG
│   └── Test_Example.md    # Usage examples
├── templates/             #  Story templates
│   └── story_template.md  # Story template with 80-char line rule
├── .vscode/              # VSCode integration
├── .rag_cache/           # Wiki content cache (git-ignored)
├── .env                  # AI & RAG configuration (create from .env.example)
├── .env.example          # Configuration template
├── dnd_consultant.py     # Launcher shortcut for interactive CLI
├── setup.py              # Launcher shortcut for workspace setup
└── README.md            # This file
```

##  Documentation

- **[AI Integration Guide](docs/AI_INTEGRATION.md)** - Complete AI setup (Ollama, OpenAI, Anthropic)
- **[RAG Integration Guide](docs/RAG_INTEGRATION.md)** - Deep dive into RAG system and wiki integration
- **[RAG Quick Start](docs/RAG_QUICKSTART.md)** - Fast track to using RAG features
- **[Party Configuration Guide](docs/PARTY_CONFIG_DOCUMENTATION.md)** - Managing your party setup
- **[Usage Examples](docs/Test_Example.md)** - See the system in action
- **[JSON Validation](docs/JSON_Validation.md)** - Data validation schemas and usage
- **[Test Suite](tests/README.md)** - Comprehensive test suite

##  Quick Start

1. **Setup the system:**
   ```powershell
   # Full module path
   python -m src.cli.setup
   
   # Or use the shortcut launcher
   python setup.py
   ```

2. **Set up AI (optional but recommended):**
   ```powershell
   # Copy environment template
   copy .env.example .env
   
   # Download Ollama model (free local AI)
   ollama pull llama3.1:8b
   ```
   See **[docs/AI_INTEGRATION.md](docs/AI_INTEGRATION.md)** for complete setup guide.

3. **Start the interactive consultant:**
   ```powershell
   # Full module path
   python -m src.cli.dnd_consultant
   
   # Or use the shortcut launcher
   python dnd_consultant.py
   ```

4. **Or use VSCode tasks:**
   - Press `Ctrl+Shift+P` → "Tasks: Run Task" → "D&D: Interactive Consultant"

## Party Configuration Management

The system uses `current_party.json` to track your active adventuring party. This is crucial for:
- **NPC Detection** - System excludes party members when suggesting NPC profiles
- **Story Analysis** - Focuses on your active characters
- **Character Development** - Tracks progression of current party members
- **Session Management** - Links stories to the correct characters

### Setting Up Your Party

**Option 1: Use the Interactive CLI (Recommended)**
```powershell
# Full module path
python -m src.cli.dnd_consultant

# Or use the shortcut launcher
python dnd_consultant.py

# Then choose: 1. Manage Characters → Create Default Party Configuration
```

**Option 2: Manual Configuration**
```powershell
# Copy the example file
copy game_data\current_party\current_party.example.json game_data\current_party\current_party.json

# Edit game_data/current_party/current_party.json with your character names
```

**Example `current_party.json`:**
```json
{
  "party_members": [
    "Theron Brightblade",
    "Mira Shadowstep",
    "Garrick Stonefist"
  ],
  "last_updated": "2025-10-05T10:30:00.000000"
}
```

### Important Notes

 **Character Names Must Match Exactly**
- Names in `current_party.json` must match character JSON filenames
- Example: `"Theron Brightblade"` → `game_data/characters/theron_brightblade.json`
- Case-insensitive matching, but exact spelling required

 **Git Ignored by Default**
- `game_data/current_party/current_party.json` is in `.gitignore` (your personal party configuration)
- `game_data/current_party/current_party.example.json` is tracked (template for others)
- This allows multiple people to work on the same repo with different parties

### Managing Your Party

**Adding/Removing Members:**
1. **Via CLI**: Use the interactive menu to modify party
2. **Via File**: Edit `current_party.json` directly
3. **Validation**: System validates character names exist on load

**When to Update:**
- Party composition changes (members join/leave)
- Starting a new campaign with different characters
- Testing with a specific character subset

**System Behavior:**
- **Missing Party File**: Falls back to default party (first 4 characters found)
- **Invalid Character Names**: System warns but continues with valid names
- **Empty Party**: System prompts to create party configuration

### Party in Action

**NPC Detection:**
```markdown
Story: "The innkeeper, Marcus, greets Theron, Mira, and Garrick..."

System detects:
[COMPLETE] Marcus (Innkeeper) - NEW NPC, suggests profile
 Theron, Mira, Garrick - Party members, excluded from NPC suggestions
```

**Story Analysis:**
```python
# System automatically focuses on your party
story_manager.analyze_story_development()
# Only analyzes: Theron, Mira, Garrick (from current_party.json)
```

##  Workflow Summary

### NEW: Story Organization System
**Campaign Story Management:**

All user-generated campaigns are stored in `game_data/campaigns/` and automatically git-ignored.

**Organized Story Series** (RECOMMENDED):
   - Each campaign gets its own folder (MUST end with: _Campaign, _Quest, _Story, or _Adventure)
   - Created in `game_data/campaigns/` by default
   - Separate analysis files per campaign
   - Better organization for multiple campaigns
   - Examples: `game_data/campaigns/Dragon_Heist_Campaign/`, `game_data/campaigns/Rescue_Mission_Quest/`

### Story Creation Workflow
1. **Create new story series** via CLI menu system (automatically goes to `game_data/campaigns/`)
2. **Write narrative** in `001_story_name.md` (pure story, 80-char lines)
3. **NPCs automatically detected** - System scans story and suggests profile creation in hooks file
4. **Analyze characters** in campaign's `character_development_*.md`
5. **Calculate DCs** in campaign's `story_dc_suggestions.md`
6. **Session results** saved in campaign's `session_results_*.md`
7. **Story hooks** tracked in campaign's `story_hooks_*.md`
4. **Use CHARACTER/ACTION/REASONING** blocks in suggestions files only
5. **Reference story scenarios** from suggestions back to narrative

### Character Consultation  
1. **Load character data** from any number of JSON files
2. **Get class expertise** for abilities, spells, tactics
3. **Check consistency** against established personality/motivations
4. **Generate DCs** based on character strengths and context in separate file

### Combat Integration
1. **Paste Fantasy Grounds Unity** combat log or simple combat description
2. **AI auto-generates** contextual combat title from story (e.g., "Goblin Ambush at Darkwood")
3. **Convert to narrative** with character-appropriate descriptions using RAG for spell/ability details
4. **Maintain story flow** while preserving mechanical accuracy

##  AI Features (Optional)

### What AI Adds
- **AI-Enhanced Character Reactions** - Characters respond with personality-driven dialogue and actions
- **Intelligent DC Suggestions** - Context-aware difficulty calculations
- **Per-Character Customization** - Each character can have unique AI settings
- **Story Analysis** - Automatic suggestions for character development and relationships

### Supported AI Providers
- **Ollama (Recommended)** - Free, local LLMs running on your PC (llama3.1:8b, mistral, etc.)
- **OpenAI** - GPT-3.5-Turbo, GPT-4, etc. (requires API key)
- **OpenRouter** - Access to many models with one API key
- **Any OpenAI-Compatible API** - Works with custom endpoints

##  Automatic NPC Detection

### What It Does
- **Automatic Scanning** - System scans story files for NPCs (innkeepers, merchants, guards, blacksmiths, etc.)
- **Smart Filtering** - Excludes party members and NPCs that already have profiles
- **Profile Suggestions** - Adds NPC creation suggestions to story hooks file with ready-to-run code
- **No Manual Tracking** - Never forget to create profiles for recurring NPCs

### How It Works
```markdown
Story: "The innkeeper, Marcus Ironforge, greets the party..."

Story Hooks File Auto-Generated:
## NPC Profile Suggestions
### Marcus Ironforge (Innkeeper)
**To create profile:**
```python
npc_profile = story_manager.generate_npc_from_story(
    npc_name="Marcus Ironforge",
    context=story_text,
    role="Innkeeper"
)
story_manager.save_npc_profile(npc_profile)
```
```

** Full Documentation:** [docs/NPC_DETECTION.md](docs/NPC_DETECTION.md)

##  RAG Features (Optional)

### What RAG Adds
- **Wiki Integration** - Automatically fetch accurate campaign lore from any wiki (Fandom.com, MediaWiki, custom)
- **Lore-Accurate Stories** - AI-generated narratives enriched with official campaign setting information
- **History Check Enhancement** - Characters recall wiki-sourced information on successful History checks
- **Smart Caching** - Downloaded wiki content cached locally (7-day TTL) to reduce API calls

### Quick RAG Setup
```powershell
# 1. Install dependencies
pip install requests beautifulsoup4

# 2. Configure in .env
RAG_ENABLED=true
RAG_WIKI_BASE_URL=https://your-campaign-wiki.com/wiki
```

** Full Guide:** [RAG_INTEGRATION.md](RAG_INTEGRATION.md)

### Quick AI Setup
```powershell
# 1. Install Ollama from https://ollama.ai
# 2. Download a model
ollama pull llama3.1:8b

# 3. Configure the system
copy .env.example .env
# Edit .env and set OPENAI_MODEL=llama3.1:8b

# 4. Enable AI for specific characters
# Edit character JSON and set ai_config.enabled = true
```

** Full Guide:** [docs/AI_INTEGRATION.md](docs/AI_INTEGRATION.md)

##  Technical Verification

[COMPLETE] **All systems operational:**
- Unlimited character JSON files supported
- Movement speeds, specialized abilities, and stats are customizable
- Story/analysis/DC separation implemented (3 separate files)
- Template files for git-friendly development
- 80-character line limit for improved readability

##  Prerequisites

- **Python 3.8+**
- **Dependencies for AI features:** `pip install -r requirements.txt` (optional, for AI integration)
- **VSCode** with Markdown extensions (recommended)

##  Philosophy

This system **enhances your creativity** while maintaining your control:

- **You create** the stories, personalities, and campaign direction
- **System provides** class expertise, consistency checking, and DC suggestions  
- **Characters act** as knowledgeable consultants, not autonomous agents
- **Perfect for** complex campaigns with rich character development

---

**Ready to enhance your D&D storytelling? Run `python -m src.cli.setup` to begin!** 
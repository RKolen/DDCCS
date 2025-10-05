# D&D Character Consultant System

A Python-based system for managing D&D## 📚 Documentation

- **[AI Integration Guide](docs/AI_INTEGRATION.md)** - Complete AI setup (Ollama, OpenAI, Anthropic)
- **[RAG Integration Guide](docs/RAG_INTEGRATION.md)** - Deep dive into RAG system and wiki integration
- **[RAG Quick Start](docs/RAG_QUICKSTART.md)** - Fast track to using RAG features
- **[Usage Examples](docs/Test_Example.md)** - See the system in action

> **Note:** Personal documentation and development notes are kept in `docs_personal/` (git-ignored)4) character consultants with 
VSCode integration for story management and character consistency analysis.

## 📋 What This System Does

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
- **🆕 Automatic NPC Detection** - System automatically detects NPCs in stories and suggests profile creation
- **VSCode Integration** - Tasks, settings, and markdown workflow support
- **🆕 AI Integration** - Optional AI/LLM enhancement with OpenAI, Ollama, or any OpenAI-compatible API
- **🆕 RAG System** - Wiki integration for campaign lore (Exandria, Forgotten Realms, custom wikis)

> **📖 [AI Integration Guide](docs/AI_INTEGRATION.md)** - Complete guide for adding AI capabilities to your characters
> 
> **🌐 [RAG Integration Guide](docs/RAG_INTEGRATION.md)** - Wiki integration for accurate campaign lore in stories

## 🚫 What This System Does NOT Do

- Does NOT automate gameplay, dice rolling, or run sessions
- Does NOT generate random encounters or locations
- Does NOT replace your creativity - it's a consultant tool

## 📁 Current Project Structure

```
D&D New Beginnings/
├── characters/              # Character profile JSON files (unlimited)
│   ├── class.example.json   # Template for new characters
├── npcs/                   # NPC management
│   └── npc.example.json    # NPC template
├── docs/                   # 📚 Public documentation
│   ├── AI_INTEGRATION.md   # Complete AI setup guide
│   ├── RAG_INTEGRATION.md  # RAG system deep dive
│   ├── RAG_QUICKSTART.md   # Quick start for RAG
│   └── Test_Example.md     # Usage examples
├── docs_personal/          # 🔒 Personal documentation (git-ignored)
│   ├── PARTY_CONFIG_DOCUMENTATION.md
│   ├── CHARACTER_NAME_ANONYMIZATION.md
│   └── FOLDER_RESTRUCTURE_SUMMARY.md
├── templates/              # 📝 Templates
│   └── story_template.md   # Story template with 80-char line rule
├── 001_*.md               # Legacy story sequence files (narrative only)
├── character_development_suggestions.md  # Legacy character analysis
├── story_dc_suggestions.md # Legacy DC calculations
├── Story_Series_Folders/   # NEW: Organized campaign management
│   ├── Test_Campaign/      # Example organized story series
│   │   ├── 001_The_Tavern_Meeting.md
│   │   ├── 002_Journey_to_the_Woods.md
│   │   ├── 003_The_Ancient_Seal.md
│   │   ├── character_development_suggestions.md
│   │   └── story_dc_suggestions.md
│   └── Your_Next_Campaign/ # Your new organized campaigns go here
├── .vscode/               # VSCode integration
├── .env                   # AI configuration (create from .env.example)
├── .env.example           # AI configuration template
├── ai_client.py           # AI/LLM integration module
├── character_consultants.py  # Character consultant system with AI
├── character_sheet.py     # D&D character data structures
├── dnd_consultant.py      # Main interactive interface
├── story_manager.py       # Story organization system
├── story_analyzer.py      # Story content analysis and suggestions
├── setup.py              # Project initialization
└── README.md             # This file
```

## � Documentation

- **[AI Integration Guide](docs/AI_INTEGRATION.md)** - Complete AI setup (Ollama, OpenAI, Anthropic)
- **[RAG Integration Guide](docs/RAG_INTEGRATION.md)** - Deep dive into RAG system and wiki integration
- **[RAG Quick Start](docs/RAG_QUICKSTART.md)** - Fast track to using RAG features
- **[Party Configuration Guide](docs/PARTY_CONFIG_DOCUMENTATION.md)** - Managing your party setup
- **[Usage Examples](docs/Test_Example.md)** - See the system in action
- **[Development Notes](docs/CHARACTER_NAME_ANONYMIZATION.md)** - Recent changes and updates

## �🚀 Quick Start

1. **Setup the system:**
   ```powershell
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
   python dnd_consultant.py
   ```

4. **Or use VSCode tasks:**
   - Press `Ctrl+Shift+P` → "Tasks: Run Task" → "D&D: Interactive Consultant"

## 👥 Party Configuration Management

The system uses `current_party.json` to track your active adventuring party. This is crucial for:
- **NPC Detection** - System excludes party members when suggesting NPC profiles
- **Story Analysis** - Focuses on your active characters
- **Character Development** - Tracks progression of current party members
- **Session Management** - Links stories to the correct characters

### Setting Up Your Party

**Option 1: Use the Interactive CLI (Recommended)**
```powershell
python dnd_consultant.py
# Choose: 1. Manage Characters → Create Default Party Configuration
```

**Option 2: Manual Configuration**
```powershell
# Copy the example file
copy current_party.example.json current_party.json

# Edit current_party.json with your character names
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

⚠️ **Character Names Must Match Exactly**
- Names in `current_party.json` must match character JSON filenames
- Example: `"Theron Brightblade"` → `characters/theron_brightblade.json`
- Case-insensitive matching, but exact spelling required

⚠️ **Git Ignored by Default**
- `current_party.json` is in `.gitignore` (your personal party configuration)
- `current_party.example.json` is tracked (template for others)
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
✅ Marcus (Innkeeper) - NEW NPC, suggests profile
❌ Theron, Mira, Garrick - Party members, excluded from NPC suggestions
```

**Story Analysis:**
```python
# System automatically focuses on your party
story_manager.analyze_story_development()
# Only analyzes: Theron, Mira, Garrick (from current_party.json)
```

## 🎯 Workflow Summary

### NEW: Story Organization System
**Two ways to manage your stories:**

1. **Legacy Stories** (existing `001_*.md` files)
   - Direct in root directory
   - Shared analysis files for all stories
   - Good for simple, single-campaign use

2. **Organized Story Series** (RECOMMENDED for new campaigns)
   - Each campaign gets its own folder (MUST end with: _Campaign, _Quest, _Story, or _Adventure)
   - Separate analysis files per campaign
   - Prevents numbering conflicts
   - Better organization for multiple campaigns
   - Examples: `Dragon_Heist_Campaign/`, `Rescue_Mission_Quest/`, `Lost_Mine_Adventure/`

### Story Creation (Organized Series - Recommended)
1. **Create new story series** via CLI menu system
2. **Write narrative** in `001_story_name.md` (pure story, 80-char lines)
3. **NPCs automatically detected** - System scans story and suggests profile creation in hooks file
4. **Analyze characters** in campaign's `character_development_suggestions.md`
5. **Calculate DCs** in campaign's `story_dc_suggestions.md`
6. **Use CHARACTER/ACTION/REASONING** blocks in suggestions files only

### Story Creation (Legacy - Single Campaign)
1. **Write narrative** in `001_story_name.md` (pure story, 80-char lines)
2. **Analyze characters** in `character_development_suggestions.md`
3. **Calculate DCs** in `story_dc_suggestions.md`
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

## 🤖 AI Features (Optional)

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

## 🧙 Automatic NPC Detection

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

**📖 Full Documentation:** [docs/NPC_DETECTION.md](docs/NPC_DETECTION.md)

## 🌐 RAG Features (Optional)

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

**📖 Full Guide:** [RAG_INTEGRATION.md](RAG_INTEGRATION.md)

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

**📖 Full Guide:** [docs/AI_INTEGRATION.md](docs/AI_INTEGRATION.md)

## 📋 Technical Verification

✅ **All systems operational:**
- Unlimited character JSON files supported
- Movement speeds, specialized abilities, and stats are customizable
- Story/analysis/DC separation implemented (3 separate files)
- Template files for git-friendly development
- 80-character line limit for improved readability

## 🔧 Prerequisites

- **Python 3.8+**
- **Dependencies for AI features:** `pip install -r requirements.txt` (optional, for AI integration)
- **VSCode** with Markdown extensions (recommended)

## 🎮 Philosophy

This system **enhances your creativity** while maintaining your control:

- **You create** the stories, personalities, and campaign direction
- **System provides** class expertise, consistency checking, and DC suggestions  
- **Characters act** as knowledgeable consultants, not autonomous agents
- **Perfect for** complex campaigns with rich character development

---

**Ready to enhance your D&D storytelling? Run `python setup.py` to begin!** 🎲
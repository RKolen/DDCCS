# D&D Character Consultant System

A Python-based system for managing D&D 5e (2024) character consultants with 
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
- **Fantasy Grounds Unity Integration** - Converts combat logs to narrative
- **NPC Management** - Track recurring NPCs with relationships and traits
- **VSCode Integration** - Tasks, settings, and markdown workflow support

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
├── story_template.md      # Template with 80-char line rule
├── .vscode/               # VSCode integration
├── character_agents.py    # Character consultant system
├── character_sheet.py     # D&D character data structures
├── dnd_consultant.py      # Main interactive interface
├── story_manager.py       # NEW: Story organization system
├── setup.py              # Project initialization
└── README.md             # This file
```

## 🚀 Quick Start

1. **Setup the system:**
   ```powershell
   python setup.py
   ```

2. **Start the interactive consultant:**
   ```powershell
   python dnd_consultant.py
   ```

3. **Or use VSCode tasks:**
   - Press `Ctrl+Shift+P` → "Tasks: Run Task" → "D&D: Interactive Consultant"

## 🎯 Workflow Summary

### NEW: Story Organization System
**Two ways to manage your stories:**

1. **Legacy Stories** (existing `001_*.md` files)
   - Direct in root directory
   - Shared analysis files for all stories
   - Good for simple, single-campaign use

2. **Organized Story Series** (RECOMMENDED for new campaigns)
   - Each campaign gets its own folder
   - Separate analysis files per campaign
   - Prevents numbering conflicts
   - Better organization for multiple campaigns

### Story Creation (Organized Series - Recommended)
1. **Create new story series** via CLI menu system
2. **Write narrative** in `001_story_name.md` (pure story, 80-char lines)
3. **Analyze characters** in campaign's `character_development_suggestions.md`
4. **Calculate DCs** in campaign's `story_dc_suggestions.md`
5. **Use CHARACTER/ACTION/REASONING** blocks in suggestions files only

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
1. **Paste Fantasy Grounds Unity** combat log
2. **Convert to narrative** with character-appropriate descriptions
3. **Maintain story flow** while preserving mechanical accuracy

## 📋 Technical Verification

✅ **All systems operational:**
- Unlimited character JSON files supported
- Movement speeds, specialized abilities, and stats are customizable
- Story/analysis/DC separation implemented (3 separate files)
- Template files for git-friendly development
- 80-character line limit for improved readability

## 🔧 Prerequisites

- **Python 3.8+** (no external dependencies)
- **VSCode** with Markdown extensions (recommended)

## 🎮 Philosophy

This system **enhances your creativity** while maintaining your control:

- **You create** the stories, personalities, and campaign direction
- **System provides** class expertise, consistency checking, and DC suggestions  
- **Characters act** as knowledgeable consultants, not autonomous agents
- **Perfect for** complex campaigns with rich character development

---

**Ready to enhance your D&D storytelling? Run `python setup.py` to begin!** 🎲
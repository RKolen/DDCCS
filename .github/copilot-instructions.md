# D&D Character Consultant System - Copilot Instructions

This workspace contains a Python-based D&D character consultant system designed to help with campaign management and story development.

## Project Overview

This is a **D&D 5e (2024) Character Consultant System** that provides:
- 12 AI character consultants (one per D&D class)
- Story sequence management with markdown files
- Character background customization
- DC suggestion engine
- Fantasy Grounds Unity combat conversion
- Character consistency analysis
- VSCode workspace integration

## Key Files & Structure

```
D&D Campaign Workspace/
├── character_consultants.py  # Core character consultant system
├── story_manager.py         # Handles 001<name>.md story files
├── combat_narrator.py       # Converts FGU combat to narrative
├── dnd_consultant.py        # Main interactive CLI
├── setup.py                 # Workspace initialization
├── characters/              # Character profile JSON files
│   ├── barbarian.json       # Customizable character backgrounds
│   ├── bard.json           # User writes custom personalities
│   └── ...                 # All 12 D&D classes
├── 001_*.md                # Story sequence files
└── .vscode/
    ├── tasks.json          # Quick access to consultants
    └── settings.json       # Markdown preferences
```

## User Workflow

The user creates story files in format `001<storyname>.md` and:
1. Writes character actions and reasoning
2. Requests DC suggestions for challenges
3. Pastes Fantasy Grounds Unity combat results
4. Gets character consistency analysis
5. Converts combat to narrative text

## Character Consultant System

Each of the 12 character consultants provides:
- **Class expertise** (spell lists, abilities, tactics)
- **DC suggestions** based on character strengths
- **Personality guidance** from custom backgrounds
- **Consistency checking** against established character traits
- **Alternative approaches** that fit the character class

## Coding Guidelines

When working with this codebase:

1. **Character Profiles**: All stored as JSON in `characters/` directory with user-customizable backgrounds
2. **Story Analysis**: Parse markdown files for CHARACTER/ACTION/REASONING blocks
3. **DC Calculations**: Base difficulty + character modifiers + context
4. **Narrative Style**: Character-appropriate descriptions for combat
5. **VSCode Integration**: Use tasks.json for quick access to consultant features

## Example Character Profile Structure

```json
{
  "name": "Character Name",
  "dnd_class": "fighter",
  "background_story": "User's custom background...",
  "personality_summary": "User's personality description...",
  "motivations": ["list", "of", "motivations"],
  "fears_weaknesses": ["character", "vulnerabilities"],
  "relationships": {
    "Character2": "relationship description"
  }
}
```

## Story File Format

```markdown
# Story Title

CHARACTER: [Character Name]
ACTION: [What they attempted]
REASONING: [Why they did it - for consistency]

## DC Suggestions Needed
- Character attempts specific action
- Another character tries challenge

## Combat Summary (from FGU)
[Fantasy Grounds Unity combat log]

## Story Narrative
[Final narrative text]
```

## Main Commands

- `python dnd_consultant.py` - Interactive consultant interface
- `python setup.py` - Initialize workspace with default characters
- VS Code tasks for quick access via Ctrl+Shift+P

## Technical Notes

- **No external dependencies** - uses only Python standard library
- **Type hints throughout** for better code clarity
- **JSON-based storage** for easy character customization
- **Markdown integration** with VSCode workflow
- **Modular design** for easy extension

## User Customization Areas

Users should customize:
1. **Character backgrounds** in JSON files
2. **Personality traits** and motivations
3. **Character relationships** with each other
4. **Story hooks** and character arcs

## Common Tasks

When assisting with this project:
- Help customize character profiles with rich backgrounds
- Assist with story analysis and consistency checking
- Support VSCode task configuration
- Help integrate Fantasy Grounds Unity workflows
- Guide DC balancing for character abilities

This system enhances user creativity rather than replacing it - the user maintains full control while getting expert character consultation.
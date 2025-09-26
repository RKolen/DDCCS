"""
Setup script for the D&D Character Consultant System.
Initializes workspace with default character JSON files and VSCode configuration.
"""

import os
import json
from pathlib import Path


def create_vscode_configuration():
    """Create VSCode tasks and settings for the workspace."""
    vscode_dir = Path('.vscode')
    vscode_dir.mkdir(exist_ok=True)
    
    # Create tasks.json for easy access to consultant commands
    tasks_config = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "D&D: Interactive Consultant",
                "type": "shell", 
                "command": "python",
                "args": ["dnd_consultant.py"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": True,
                    "panel": "shared"
                },
                "problemMatcher": []
            },
            {
                "label": "D&D: Analyze Current Story",
                "type": "shell",
                "command": "python", 
                "args": ["dnd_consultant.py", "--analyze", "${fileBasename}"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always", 
                    "focus": False,
                    "panel": "shared"
                },
                "problemMatcher": []
            }
        ]
    }
    
    tasks_path = vscode_dir / 'tasks.json'
    with open(tasks_path, 'w', encoding='utf-8') as f:
        json.dump(tasks_config, f, indent=2)
    
    # Create settings.json for markdown preferences
    settings_config = {
        "markdown.preview.scrollPreviewWithEditor": True,
        "markdown.preview.scrollEditorWithPreview": True,
        "files.associations": {
            "*.md": "markdown"
        },
        "markdown.extension.toc.levels": "2..6"
    }
    
    settings_path = vscode_dir / 'settings.json'
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings_config, f, indent=2)
    
    return True


def create_example_story():
    """Create an example story file using the current template format."""
    example_content = """# The Tavern Meeting

## First Encounters

### Opening Scene

---

## Character Actions for major_plot_actions

Use this format when logging character actions:

CHARACTER: [Character Name]
ACTION: [What they attempted]
REASONING: [Why they did it - for consistency]

Example:
CHARACTER: Sir Gareth
ACTION: Introduced himself to the group with confidence
REASONING: As a paladin, he naturally takes leadership and wants to inspire trust

---

## Character Relationships for relationships field

Update character JSON files with relationships like:
```json
"relationships": {
  "Elara": "Respects her knowledge but finds her overly cautious",
  "Finn": "Amused by his wit, but wary of his light fingers"
}
```

---

## DC Suggestions Needed
- Character attempts to rally the group with inspiring speech
- Another character tries to gather information discreetly

---

## Combat Summary (from FGU)
[No combat in this scene]

---

## Story Narrative

The Prancing Pony tavern bustled with evening activity as diverse adventurers found themselves drawn to respond to a mysterious job posting. The posting promised "adventure and fair compensation for those brave enough to seek ancient secrets."

Each character brings their own motivations and past experiences to this first meeting, setting the stage for the adventures to come.
"""
    
    example_path = Path('001_The_Tavern_Meeting.md')
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_content)
    
    return example_path


def setup_workspace():
    """Set up the workspace for the D&D Character Consultant System."""
    
    print("🐉 Setting up D&D Character Consultant System...")
    print("=" * 50)
    
    # Verify character files exist
    characters_dir = Path('characters')
    if not characters_dir.exists():
        print("❌ Error: 'characters' directory not found!")
        print("   The character JSON files should already exist in this workspace.")
        return False
    
    # Count existing character files
    character_files = list(characters_dir.glob('*.json'))
    print(f"✅ Found {len(character_files)} character JSON files")
    
    # Create VSCode configuration
    print("\n📝 Creating VSCode configuration...")
    if create_vscode_configuration():
        print("✅ Created VSCode tasks and settings")
    
    # Create example story
    print("\n📚 Creating example story...")
    example_path = create_example_story()
    print(f"✅ Created example story: {example_path}")
    
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Customize character backgrounds in the 'characters/*.json' files")
    print("2. Add relationships between characters in the JSON files")
    print("3. Run 'python dnd_consultant.py' to access the interactive consultant")
    print("4. Create story files using the 001<name>.md format")
    print("5. Use Ctrl+Shift+P > 'Tasks: Run Task' > 'D&D: Interactive Consultant'")
    
    print(f"\n📖 Example story created: {example_path}")
    print(f"\n🎭 Character files ready for customization:")
    
    # List the character files
    for char_file in sorted(character_files):
        # Read the class from the JSON file
        try:
            with open(char_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                class_name = data.get('dnd_class', 'Unknown')
                print(f"   • {char_file.stem}.json ({class_name})")
        except Exception:
            print(f"   • {char_file.name}")
    
    print("\n🎲 Ready to enhance your D&D storytelling!")
    return True


if __name__ == "__main__":
    setup_workspace()
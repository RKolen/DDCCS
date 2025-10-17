"""
Setup script for the D&D Character Consultant System.
Initializes workspace with default character JSON files and VSCode configuration.
"""

import json
from pathlib import Path


def create_vscode_configuration():
    """Create VSCode tasks and settings for the workspace."""
    vscode_dir = Path(".vscode")
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
                    "panel": "shared",
                },
                "problemMatcher": [],
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
                    "panel": "shared",
                },
                "problemMatcher": [],
            },
        ],
    }

    tasks_path = vscode_dir / "tasks.json"
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(tasks_config, f, indent=2)

    # Create settings.json for markdown preferences
    settings_config = {
        "markdown.preview.scrollPreviewWithEditor": True,
        "markdown.preview.scrollEditorWithPreview": True,
        "files.associations": {"*.md": "markdown"},
        "markdown.extension.toc.levels": "2..6",
    }

    settings_path = vscode_dir / "settings.json"
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings_config, f, indent=2)

    return True


def setup_workspace():
    """Set up the workspace for the D&D Character Consultant System."""

    print("🐉 Setting up D&D Character Consultant System...")
    print("=" * 50)

    # Verify character files exist
    characters_dir = Path("game_data/characters")
    if not characters_dir.exists():
        print("❌ Error: 'game_data/characters' directory not found!")
        print("   The character JSON files should already exist in this workspace.")
        return False

    # Count existing character files (exclude example/template files)
    all_files = list(characters_dir.glob("*.json"))
    character_files = [
        f
        for f in all_files
        if "example" not in f.stem.lower() and "template" not in f.stem.lower()
    ]
    print(f"✅ Found {len(character_files)} character JSON files")

    # Create VSCode configuration
    print("\n📝 Creating VSCode configuration...")
    if create_vscode_configuration():
        print("✅ Created VSCode tasks and settings")

    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Customize character backgrounds in 'game_data/characters/*.json'")
    print("2. Run 'python dnd_consultant.py' to start the interactive consultant")
    print("3. Use the consultant to:")
    print("   - Create campaigns and story files")
    print("   - Manage party configuration")
    print("   - Get character consultations and DC suggestions")
    print(
        "4. Or use VSCode: Ctrl+Shift+P > 'Tasks: Run Task' > 'D&D: Interactive Consultant'"
    )

    print("\n🎭 Character files ready for customization:")

    # List the character files (exclude example/template files)
    for char_file in sorted(character_files):
        # Skip example/template files
        if "example" in char_file.stem.lower() or "template" in char_file.stem.lower():
            continue

        # Read the class from the JSON file
        try:
            with open(char_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                class_name = data.get("dnd_class", "Unknown")
                print(f"   • {char_file.stem}.json ({class_name.title()})")
        except (OSError, json.JSONDecodeError):
            print(f"   • {char_file.name}")

    print("\n🎲 Ready to enhance your D&D storytelling!")
    return True


if __name__ == "__main__":
    setup_workspace()

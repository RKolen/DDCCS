# D&D Character Consultant System - Copilot Instructions

**For detailed project context, see `docs/docs_personal/COPILOT_CONTEXT.md`**

## Critical Rules (Non-Negotiable)

### NO Emojis in Any Code
**NEVER use emojis in .py or .md files**
- Causes Windows cp1252 codec failures
- Breaks execution even with UTF-8 configuration
- Use ASCII alternatives instead

### 10.00/10 Pylint Score Required
**NEVER use `# pylint: disable=...`, `# noqa`, or `# pragma` comments**
- Fix code properly: refactor functions, extract helpers, use decision tables
- This includes tests
- Document architectural solutions in `docs/docs_personal/future_rework.md`
- Upon big code changes also pyltin the folder src and the tests folder and fix every issue

### Full Pylint Output (No Pipes)
Always use: `python pylint <file-or-folder>`
- Never use pipes, grep, Select-String, or any output filtering
- Full visibility ensures all issues are addressed

## Key Instructions

### Before Starting Any Task
1. Read the full project structure in `docs/docs_personal/COPILOT_CONTEXT.md`
2. Verify code matches documentation
3. Check imports and file relationships
4. If uncertain about ANY detail, read the entire source folder

### When Making Plans
- Plans must reflect ACTUAL code structure, not assumptions
- Base decisions on current implementation, not previous versions
- Base it on the entire source folder
- Test examples on real party members: Aragorn, Frodo Baggins, Gandalf the Grey

### Code Quality Standards
- **Pylint 10.00/10** - Fix issues by refactoring, not disabling
- **Decision tables** for multiple conditions (eliminates nested ifs)
- **Data-driven design** for pattern matching (motivation/goal extraction)
- **Helper functions** to reduce local variables and complexity
- **Type hints** throughout all code

### When Verifying the Project
If asked to "verify everything" or "check all files":
- Read EVERY file mentioned in the project structure
- NO shortcuts, NO assumptions
- Verify actual code matches documentation
- Test workflows end-to-end

## Project Quick Reference

**Key Directories:**
- `game_data/characters/` - Character profiles (JSON)
- `game_data/campaigns/` - User story campaigns
- `src/` - All source code
- `src/stories/` - Story management (personality-aware analysis here)
- `src/cli/dnd_consultant.py` - Main interactive tool
- `tests/` - Test suite (git-ignored)

**Core Commands:**
```bash
python dnd_consultant.py                    # Main interactive CLI
python tests/run_all_tests.py               # Run all tests
python tests/run_all_tests.py validation    # Run 1 test suite
python tests/run_all_tests.py ai characters # Run multiple test suites
```

## Testing Practices

- **Standard:** 10.00/10 pylint score, public APIs only
- **Helpers:** Reusable patterns in `tests/test_helpers.py`
- **Examples:** Use real characters (Aragorn, Frodo, Gandalf) not placeholders
- **Running tests:**  When running tests always use the test suite read tests\README.md
                      on how to run this.
- **New tests:** Add the test to the test_all_<suitename>.py before checking if ther test works

## Documentation

- `docs/docs_personal/COPILOT_CONTEXT.md` - Detailed architecture & implementation
- `docs/docs_personal/future_rework.md` - Technical improvements needed

## Commit Guidelines

**Format:** Brief summary (50 chars max), optional detail below

**Examples:**
- "Refactor character_action_analyzer with decision tables for 10.00/10 pylint"
- "Add personality-aware reasoning to character development analysis"
- "Fix gitignore pattern for campaign files"

**Rules:**
- Use imperative mood: "Add" not "Added"
- No emojis or decorative characters
- Professional tone
- Group related changes

## Common Patterns

### Fixing Too-Many-Return-Statements
Use decision tables instead of nested ifs:
```python
patterns = [
    (trigger_words, trait_key, with_trait_msg, fallback_msg),
]
for words, key, with_msg, fallback in patterns:
    if any(word in text for word in words):
        if traits.get(key):
            return f"{with_msg}: {traits[key]}"
        return fallback
return default_msg
```

### Personality-Aware Analysis
Extract traits from character JSON profiles:
```python
traits = profiles.get(character_name, {})
# traits contains: personality_summary, background_story, motivations, 
# fears_weaknesses, goals, relationships, secrets
```

### Character Profile Structure
```json
{
  "name": "Aragorn",
  "dnd_class": "ranger",
  "level": 5,
  "personality_summary": "Determined ranger seeking to reclaim his throne",
  "motivations": ["Reclaim his throne", "Protect the realm"],
  "fears_weaknesses": ["Failure to save those he cares for"],
  "goals": ["Unite the kingdom", "Defeat the darkness"],
  "relationships": {"Frodo Baggins": "Loyal protector"},
  "background_story": "Ranger of the North..."
}
```

**This file is intentionally lean. For detailed information, see `docs/docs_personal/COPILOT_CONTEXT.md`**
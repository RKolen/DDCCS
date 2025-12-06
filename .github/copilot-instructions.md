# D&D Character Consultant System - Copilot Instructions

- Before every action read this entire document
**For detailed project context, see `docs/docs_personal/COPILOT_CONTEXT.md`**

## Critical Rules (Non-Negotiable)

### NO Emojis in Any Code
**NEVER use emojis in .py or .md files**
- Causes Windows cp1252 codec failures
- Breaks execution even with UTF-8 configuration
- Use ASCII alternatives instead

### 10.00/10 Pylint Score Required
**NEVER use `# pylint: disable=...`, `# noqa`, or `# pragma` comments**
- Fix code properly: refactor functions, extract helpers, use decision tables (duplicate-code must be fixed)
- This includes tests
- Document architectural solutions in `docs/docs_personal/future_rework.md`
- Upon big code changes also pyltin the folder src/ and the tests/ folder and fix every issue,
  so the commands to use are pylint src/ and pylint tests/ the entire sturcture must be correct
  this way duplicate code can be filtered out and fixed


### Full Pylint Output (No Pipes)
Always use: `python -m pylint <file-or-folder>`
- Never use pipes, grep, Select-String, or any output filtering
- Full visibility ensures all issues are addressed
- **FOR BIG CODE CHANGES:** Pylint BOTH `src/` AND `tests/` folders completely
  - Correct: `python -m pylint src/` then `python -m pylint tests/`
  - Incorrect: `python -m pylint src/cli/` (too narrow, misses duplicate code)
  - Always check the ENTIRE structure, not just changed module

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

### Testing Practices
- **Standard:** 10.00/10 pylint score, public APIs only,
- **Helpers:** Reusable patterns in `tests/test_helpers.py`
- **Examples:** Use real characters (Aragorn, Frodo, Gandalf) and campaigns (Example_Campaign)
- **Data:** NEVER create mock data in tests. Use existing profiles in `game_data/characters` and `game_data/campaigns`.
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

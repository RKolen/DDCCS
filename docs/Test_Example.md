# D&D Character Consultant - Simple Testing Guide

This guide shows you exactly what to press and what to expect when testing the system.

---

## Quick Test - 5 Minutes

### 1. Start the Program
```powershell
python dnd_consultant.py
```

### 2. You'll See This Menu:
```
=== D&D Character Consultant ===
1. Character Consultation
2. DM Consultation
3. Story Management
4. Combat Conversion
5. Exit
Choose an option (1-5):
```

### 3. Test Character Consultation
- **Press:** `1` and Enter
- **You'll see:** List of available characters (if you have any in `characters/` folder)
- **What to expect:** If no characters exist, you'll get a message to create some first

### 4. Test DM Consultation
- **Press:** `2` and Enter
- **You'll see:** Options for DC suggestions, character development, etc.
- **Try typing:** "A bard tries to persuade a merchant"
- **What to expect:** The system suggests a DC (difficulty) like "DC 15 for medium difficulty"

### 5. Test Story Management
- **Press:** `3` and Enter
- **You'll see:** Options to create campaigns, write stories, or manage sessions
- **What to expect:** Access to the enhanced story management system

---

## Full Test - Creating a Campaign

### Step 1: Run Setup
```powershell
python setup.py
```

**What happens:** Creates default character templates and VSCode configuration

### Step 2: Create Your First Campaign
1. Run: `python dnd_consultant.py`
2. Press `3` for Story Management
3. Choose "Create New Story Series"
4. **Name it:** Something ending in `_Quest`, `_Campaign`, `_Story`, or `_Adventure`
   - [COMPLETE] Good: `Thornhaven_Campaign`
   -  Bad: `MyStory` (missing required suffix)

**What you'll get:**
- A new folder with your campaign name
- Empty and ready for your first story

### Step 3: Write Your First Story
1. Still in Story Management, choose "Create New Story"
2. Select your campaign folder
3. **Name it:** A descriptive story title (e.g., "The Rusty Tankard")
4. **What happens:** Creates `001_The_Rusty_Tankard.md`
5. Open the file and write your narrative with your party (e.g., Aragorn, Frodo, Gandalf)

**IMPORTANT:** Set up party configuration first (see Step 2 note about party selection during series creation)

**The system automatically generates (after story is created):**
- `story_hooks_YYYY-MM-DD_story_name.md` - NPCs detected, plot hooks, unresolved threads
- `character_development_YYYY-MM-DD_story_name.md` - Created when party is configured AND story mentions party members
- `session_results_YYYY-MM-DD_story_name.md` - AI-analyzed character actions and events (if AI enabled)

### Step 4: Add Combat Narrative (Optional - Requires AI)

**If you have Ollama installed and configured:**

1. Return to main menu, press `4` for Combat Conversion
2. **Describe the combat in natural language** (end with `###`)
3. **Choose narrative style:** Cinematic, Gritty, Heroic, or Tactical
4. Select your campaign → Select your story file

**What happens:**
- AI automatically generates a situational title based on your combat and story
- Converts your tactical description into narrative prose
- Removes game mechanics (dice rolls, DCs, saves)
- Appends to your story as a new section

### Step 5: Test Character Consultation with Real Characters

The system includes example characters: Aragorn, Frodo, and Gandalf

1. Run: `python dnd_consultant.py`
2. Press `1` for Character Consultation
3. Select **Aragorn**, **Frodo**, or **Gandalf**
4. **Ask a question:** "What would you do if guards approached?"
5. **Expect:** Class-appropriate advice based on their ranger/hobbit/wizard abilities

**Character Development Workflow (Optional):**
1. Make sure you set up party members when creating the campaign series
2. Write a story featuring party member names (e.g., "Aragorn entered cautiously")
3. After story creation, the system auto-generates `character_development_YYYY-MM-DD_story_name.md`
4. Open the file and review how each character acted
5. Edit CHARACTER/ACTION/REASONING fields to analyze consistency against character traits

---

## Expected File Structure After Test

```
game_data/
├── characters/
│   ├── aragorn.json          # Example ranger character
│   ├── frodo.json            # Example hobbit character
│   ├── gandalf.json          # Example wizard character
│   └── ... (other classes)
└── campaigns/
    └── Thornhaven_Campaign/
        ├── current_party.json                              # Party configuration
        ├── 001_The_Rusty_Tankard.md                        # Your story file
        ├── story_hooks_2025-11-14_the_rusty_tankard.md     # Auto-generated (always)
        ├── character_development_2025-11-14_the_rusty_tankard.md    # Auto-generated (if party configured)
        └── session_results_2025-11-14_the_rusty_tankard.md          # Auto-generated (if party configured)
```

**Note:** File naming uses actual creation date (YYYY-MM-DD) instead of story number prefix

**Example character_development file content:**

*(Created automatically by extracting character mentions from your story)*

```markdown
# Character Development: The Rusty Tankard
**Date:** 2025-11-14

## Character Actions & Reasoning

### CHARACTER: Aragorn
**ACTION:** Aragorn entered the tavern cautiously, scanning the common room for threats. The ranger moved to a corner table where he could watch both entrances.
**REASONING:** To be analyzed
**Consistency Check:** Pending review
**Development Notes:** Extract from narrative

---

### CHARACTER: Frodo
**ACTION:** Frodo asked the innkeeper about previous visitors and listened carefully to gossip. He seemed concerned about being recognized.
**REASONING:** To be analyzed
**Consistency Check:** Pending review
**Development Notes:** Extract from narrative

---

### CHARACTER: Gandalf
**ACTION:** Gandalf ordered ale and settled by the fireplace, apparently listening to tavern gossip while seemingly lost in thought.
**REASONING:** To be analyzed
**Consistency Check:** Pending review
**Development Notes:** Extract from narrative

---
```

**How to use this file:**
1. The system automatically extracts character mentions and context from your story
2. You fill in the REASONING field with why each character acted that way
3. Update CONSISTENCY CHECK to verify it matches their established traits
4. Add DEVELOPMENT NOTES to track character growth and changes

**Example session_results file content:**
```markdown
# Session Results: The Rusty Tankard

## Character Actions Performed
- Aragorn: Established base of operations in tavern
- Frodo: Gathered information about local merchants
- Gandalf: Eavesdropped on merchant guild discussions

## Notable Events
- Met hooded stranger interested in party's journey
- Learned of bandit activity on northern road
- Accepted supply merchant's offer for equipment discount

## Session Summary
Party established presence in Thornhaven and gathered intelligence on local situation.
```

---

## Common Issues

### "No characters found"
**Fix:** Run `python setup.py` first to create templates

### "Invalid series name"
**Fix:** Campaign name must end with: `_Campaign`, `_Quest`, `_Story`, or `_Adventure`

### "AI not responding"
**Fix:** 
1. Check if Ollama is running: `ollama list`
2. Check if `.env` file exists and has correct settings
3. Make sure character has `"enabled": true` in `ai_config`

---

## Success Checklist

You've successfully tested the system if:

- [ ] Program starts without errors
- [ ] You can navigate the menu
- [ ] You can create a new story series (campaign)
- [ ] Files are created in the correct folder
- [ ] Character consultation works (if you have characters)
- [ ] AI responds (if you enabled it)

---

## Next Steps

1. **Customize characters:** Edit JSON files in `characters/` folder
2. **Write your story:** Fill in the `001_*.md` file with your narrative
3. **Use during sessions:** Run the consultant while playing D&D
4. **Add NPCs:** Create JSON files in `npcs/` folder

**That's it! Simple testing to verify everything works.** 

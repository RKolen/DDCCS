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
   - ✅ Good: `Thornhaven_Campaign`
   - ❌ Bad: `MyStory` (missing required suffix)

**What you'll get:**
- A new folder with your campaign name
- Empty and ready for your first story

### Step 3: Write Your First Story
1. Still in Story Management, choose "Create New Story"
2. Select your campaign folder
3. **Name it:** A descriptive story title (e.g., "The Rusty Tankard")
4. **What happens:** Creates `001_The_Rusty_Tankard.md`
5. Open the file and write your narrative

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

### Step 5: Test AI Features (Optional)

If you have Ollama installed:

1. Create `.env` file (copy from `.env.example`)
2. Make sure Ollama is running
3. Configure the AI model in `.env`:
   ```properties
   OPENAI_MODEL=qwen2.5:14b       # Your chosen model
   OPENAI_BASE_URL=http://localhost:11434/v1
   OPENAI_API_KEY=ollama
   ```
4. Edit a character JSON file's `ai_config` section:
   ```json
   "ai_config": {
     "enabled": true,
     "temperature": 0.7,
     "system_prompt": "You are [Character Name], a [class] who..."
   }
   ```
   **Note:** Model, base_url, and api_key are now centralized in `.env`. Characters only need `enabled`, `temperature`, and `system_prompt`.

5. Run `python dnd_consultant.py` again
6. Press `1` for Character Consultation
7. Select your character
8. **Ask:** "What would you do if a dragon appeared?"
9. **Expect:** AI-generated response in that character's voice

---

## Expected File Structure After Test

```
Thornhaven_Campaign/
├── 001_The_Rusty_Tankard.md          (Your story)
├── 002_Next_Adventure.md
└── ...
```

**Optional session files** (created through Story Management):
```
Thornhaven_Campaign/
├── session_results_2025-10-04_the_rusty_tankard.md
├── character_development_2025-10-04_the_rusty_tankard.md
└── story_hooks_2025-10-04_the_rusty_tankard.md
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

**That's it! Simple testing to verify everything works.** 🎲

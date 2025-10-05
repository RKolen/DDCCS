# RAG System Quick Start

## Install Dependencies

```bash
pip install requests beautifulsoup4
```

## Configure .env

Create or edit `.env` file:

```properties
# Enable RAG
RAG_ENABLED=true

# Choose your campaign wiki (for lore: locations, NPCs)
# Critical Role (Exandria)
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki

# Forgotten Realms
# RAG_WIKI_BASE_URL=https://forgottenrealms.fandom.com/wiki

# D&D 5e rules wiki (for items, spells, game mechanics)
RAG_RULES_BASE_URL=https://dnd5e.wikidot.com

# Cache settings (optional)
RAG_CACHE_TTL=604800  # 7 days
```

## Test It

```bash
python test_rag_system.py
```

## Use It

### In Story Generation

Stories automatically include wiki lore when you mention locations:

```bash
python dnd_consultant.py
# Choose: 2. DM Consultation
# Enter prompt: "The party arrives in Whitestone"
# → AI includes accurate Whitestone lore!
```

### For History Checks

```python
from history_check_helper import handle_history_check

result = handle_history_check("Tal'Dorei", check_result=18, character_name="Elara")
print(result['information'])  # Shows wiki lore!
```

## That's It!

See `RAG_INTEGRATION.md` for full documentation.

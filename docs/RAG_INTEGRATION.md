# RAG (Retrieval-Augmented Generation) Integration Guide

## Overview

The D&D Character Consultant System now includes **RAG (Retrieval-Augmented Generation)** support, allowing AI to fetch and integrate accurate campaign setting lore from wiki sources when generating stories and handling character History checks.

## 🌟 Features

### 1. **Wiki Integration for Story Generation**
- AI automatically searches campaign wikis for relevant lore
- Enriches narratives with accurate location descriptions, history, and context
- Maintains consistency with official campaign settings

### 2. **History Check Enhancement**
- Characters who make successful History checks receive wiki-sourced information
- Detail level scales with check result (10-14: basic, 15-19: detailed, 20+: comprehensive)
- DMs can look up lore instantly

### 3. **Smart Caching**
- Wiki pages are cached locally in `.rag_cache/` directory (git-ignored)
- Configurable TTL (time-to-live) prevents stale data
- Reduces API calls and improves performance

### 4. **Multiple Campaign Setting Support**
- **Critical Role (Exandria)**: `https://criticalrole.fandom.com/wiki`
- **Forgotten Realms**: `https://forgottenrealms.fandom.com/wiki`
- **Custom wikis**: Any MediaWiki or Fandom.com wiki
- **Homebrew**: Point to your own wiki

## 📋 Requirements

### Required Python Packages

```bash
pip install requests beautifulsoup4
```

These packages enable web scraping and HTML parsing for wiki content.

### Optional but Recommended

```bash
pip install python-dotenv  # Already included in base requirements
```

## ⚙️ Configuration

### 1. Enable RAG in `.env`

Copy from `.env.example` and configure:

```properties
# Enable RAG system
RAG_ENABLED=true

# Wiki base URL for your campaign setting
# Critical Role (Exandria)
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki

# Cache settings
RAG_CACHE_TTL=604800  # 7 days in seconds
RAG_MAX_CACHE_SIZE=100  # Maximum cached pages

# Search settings
RAG_SEARCH_DEPTH=3  # How many wiki links to follow
RAG_MIN_RELEVANCE=0.5  # Minimum relevance score (0.0-1.0)
```

### 2. Choose Your Campaign Setting

#### Critical Role (Exandria)
```properties
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki
```

Popular pages:
- `Tal'Dorei` - The continent
- `Whitestone` - The de Rolo family's city
- `Emon` - Capital of Tal'Dorei
- `Vasselheim` - Ancient city of the gods
- `Wildemount` - Second continent
- `Exandria` - The world itself

#### Forgotten Realms
```properties
RAG_WIKI_BASE_URL=https://forgottenrealms.fandom.com/wiki
```

Popular pages:
- `Waterdeep` - City of Splendors
- `Baldur's Gate` - Gateway to the West
- `Neverwinter` - Jewel of the North
- `Sword Coast` - Western region
- `Faerun` - The main continent

#### Custom/Homebrew Wiki
```properties
RAG_WIKI_BASE_URL=https://your-wiki.com/wiki
```

## 🚀 Usage

### In Story Generation

RAG works automatically when generating stories:

```python
from dungeon_master import DMConsultant
from ai_client import AIClient

# Initialize DM with AI
ai_client = AIClient()
dm = DMConsultant(workspace_path=".", ai_client=ai_client)

# Generate narrative - RAG automatically searches for locations
narrative = dm.generate_narrative_content(
    story_prompt="The party arrives in Whitestone, seeking the de Rolo family.",
    characters_present=["Theron", "Mira", "Garrick"],
    style="immersive"
)
```

**What happens behind the scenes:**
1. RAG extracts location names ("Whitestone", "de Rolo")
2. Fetches wiki pages for these locations
3. Includes relevant lore context in AI prompt
4. AI generates narrative using accurate campaign lore

### For Character History Checks

```python
from history_check_helper import handle_history_check

# Character makes a History check about Tal'Dorei
result = handle_history_check(
    topic="Tal'Dorei",
    check_result=18,  # d20 roll + Intelligence modifier
    character_name="Elara"
)

if result['success']:
    print(f"✅ {result['information']}")
    print(f"Source: {result['source']}")  # 'wiki' or 'fallback'
else:
    print(f"❌ Check failed (needed DC {result['dc']})")
```

**Output Example:**
```
✅ Elara recalls: 

=== LORE CONTEXT: Tal'Dorei ===

Introduction:
Tal'Dorei is a continent on the world of Exandria. It is home to the city 
of Emon, capital of the Tal'Dorei Republic, and is the primary setting of 
the first campaign of Critical Role...

Geography:
The continent is bordered by the Ozmit Sea to the west and the Lucidian 
Ocean to the east...

=== END LORE CONTEXT ===

Source: wiki
```

### Direct Lore Lookup (for DMs)

```python
from history_check_helper import search_lore

# Search for information about Whitestone
lore = search_lore("Whitestone", pages_to_search=["Whitestone", "Tal'Dorei"])
print(lore)
```

### In CLI (Interactive Mode)

```bash
python dnd_consultant.py
```

1. Choose **"2. DM Consultation"**
2. Select **"Generate Story Narrative"**
3. Enter your prompt mentioning locations
4. RAG automatically enriches the narrative

For History checks:
1. Choose **"1. Character Consultation"**
2. Select a character
3. When prompted, mention making a History check
4. System will fetch relevant lore

## 📁 File Structure

```
D&D Campaign Workspace/
├── .env                          # RAG configuration
├── .rag_cache/                   # Wiki content cache (git-ignored)
│   ├── index.json               # Cache index
│   ├── abc123def456.json        # Cached page 1
│   └── 789ghi012jkl.json        # Cached page 2
├── rag_system.py                 # Core RAG functionality
├── history_check_helper.py       # History check integration
├── dungeon_master.py             # Story generation with RAG
└── dnd_consultant.py             # CLI interface
```

## 🔧 Advanced Configuration

### Cache Management

View cache statistics:
```python
from rag_system import WikiCache

cache = WikiCache()
stats = cache.get_stats()
print(f"Cached pages: {stats['entries']}")
print(f"Cache size: {stats['size_mb']:.2f} MB")
```

Clear expired cache entries:
```python
cache.clear_expired()
```

Force refresh a specific page:
```python
from rag_system import WikiClient

client = WikiClient("https://criticalrole.fandom.com/wiki")
page_data = client.fetch_page("Whitestone", force_refresh=True)
```

### Custom Search Relevance

Adjust relevance scoring in `rag_system.py`:

```python
# In WikiClient.search_sections()
# Modify scoring weights:
if query_lower in title:
    score += 2.0  # Title match weight (default: 2.0)

title_matches = len(query_words & title_words)
score += title_matches * 0.5  # Title word weight (default: 0.5)

content_matches = len(query_words & content_words)
score += content_matches * 0.1  # Content word weight (default: 0.1)
```

### Error Handling

RAG fails gracefully:
- If `requests` or `beautifulsoup4` not installed → Warning message, continues without RAG
- If wiki unreachable → Uses cached data or continues without lore
- If page not found → Generates narrative without specific lore context

## 🐛 Troubleshooting

### "RAG System: requests or beautifulsoup4 not installed"

**Solution:**
```bash
pip install requests beautifulsoup4
```

### "RAG enabled but RAG_WIKI_BASE_URL not set in .env"

**Solution:**
Add to `.env`:
```properties
RAG_ENABLED=true
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki
```

### Wiki pages not being found

**Common issues:**
1. **Page name spelling** - Wiki page titles are case-sensitive
   - ✅ Correct: `Tal'Dorei`
   - ❌ Wrong: `taldorei` or `Tal Dorei`

2. **URL encoding** - Spaces become underscores
   - Search for: "Tal'Dorei Council"
   - Actual page: `Tal'Dorei_Council`

3. **Network issues** - Check internet connection
   ```python
   import requests
   response = requests.get("https://criticalrole.fandom.com/wiki/Exandria")
   print(response.status_code)  # Should be 200
   ```

### Cache not working

**Check cache directory:**
```bash
# Windows
dir .rag_cache

# Linux/Mac
ls -la .rag_cache
```

**Verify .gitignore:**
```bash
# .rag_cache/ should be in .gitignore
grep rag_cache .gitignore
```

### Slow performance

**Solutions:**
1. **Reduce search depth** in `.env`:
   ```properties
   RAG_SEARCH_DEPTH=2  # Lower is faster
   ```

2. **Increase cache TTL** (cache pages longer):
   ```properties
   RAG_CACHE_TTL=1209600  # 14 days
   ```

3. **Pre-cache important pages:**
   ```python
   from rag_system import WikiClient
   
   client = WikiClient("https://criticalrole.fandom.com/wiki")
   important_pages = ["Tal'Dorei", "Emon", "Whitestone", "Vasselheim"]
   
   for page in important_pages:
       print(f"Caching {page}...")
       client.fetch_page(page)
   ```

## 📊 Performance Considerations

### Caching Strategy

- **First fetch**: ~2-5 seconds (network request)
- **Cached fetch**: <0.1 seconds (local read)
- **Cache size**: ~10-50 KB per page

### Rate Limiting

Be respectful to wiki servers:
- Don't fetch more than 5 pages per story generation
- Use cache (default 7-day TTL)
- Consider pre-caching frequently used pages

### Memory Usage

- Cache stored on disk (not in memory)
- Each cached page: ~10-50 KB
- 100 pages ≈ 1-5 MB total

## 🎯 Best Practices

### 1. Pre-Cache Campaign Locations

Before your session:
```python
from rag_system import WikiClient

client = WikiClient("https://criticalrole.fandom.com/wiki")

# Cache all locations your party will visit
session_locations = [
    "Emon",
    "Greyskull Keep",
    "Kraghammer",
    "Vasselheim"
]

for location in session_locations:
    client.fetch_page(location)

print("✅ Session locations cached!")
```

### 2. Use Descriptive Location Names

In story prompts, use full proper names:
- ✅ "The party travels to Whitestone in Tal'Dorei"
- ❌ "The party goes to the city"

### 3. Verify Wiki Coverage

Not all settings have comprehensive wikis. Check coverage before enabling:
```python
from rag_system import WikiClient

client = WikiClient("https://your-wiki.com/wiki")
test_page = client.fetch_page("Main_Location")

if test_page:
    print(f"✅ Wiki has {len(test_page['sections'])} sections")
else:
    print("❌ Wiki may not have good coverage")
```

### 4. Combine with Custom Lore

For homebrew campaigns:
1. Create a wiki (free options: Fandom.com, MediaWiki, Notion)
2. Document key locations, NPCs, history
3. Point RAG to your wiki
4. Benefit from consistent lore across all AI generations

## 🔐 Privacy & Git

### What's Git-Ignored

The `.gitignore` includes:
```
# Ignore RAG cache directory (wiki content)
.rag_cache/
*.rag.json
rag_*.db
```

### What's in Version Control

Only configuration (not content):
- `.env.example` (template)
- `rag_system.py` (code)
- `history_check_helper.py` (code)

### Sharing Campaigns

To share campaigns with RAG:
1. Share `.env` settings (wiki URL)
2. **Don't** share `.rag_cache/` directory
3. Each user downloads their own wiki content

## 📝 Examples

### Example 1: Exandria Campaign

```properties
# .env
RAG_ENABLED=true
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki
RAG_CACHE_TTL=604800
```

```python
# Generate story in Whitestone
from dungeon_master import DMConsultant
from ai_client import AIClient

dm = DMConsultant(".", AIClient())
narrative = dm.generate_narrative_content(
    "The party investigates rumors of undead in Whitestone's Parchwood Timberlands",
    characters_present=["Vex'ahlia", "Vax'ildan", "Pike"],
    style="cinematic"
)
```

Result: AI generates narrative with accurate Whitestone history, the de Rolo family, and local geography.

### Example 2: Forgotten Realms Campaign

```properties
# .env
RAG_ENABLED=true
RAG_WIKI_BASE_URL=https://forgottenrealms.fandom.com/wiki
```

```python
# History check about Waterdeep
from history_check_helper import handle_history_check

result = handle_history_check("Waterdeep", check_result=22, character_name="Elara")
# Returns comprehensive lore about the City of Splendors
```

### Example 3: Homebrew Campaign

1. Create wiki at `https://your-campaign.fandom.com`
2. Configure:
   ```properties
   RAG_ENABLED=true
   RAG_WIKI_BASE_URL=https://your-campaign.fandom.com/wiki
   ```
3. Document your world's locations, history, factions
4. AI automatically uses your lore!

## 🎓 Technical Details

### How RAG Works

1. **Extraction**: System extracts proper nouns (capitalized phrases) from prompts
2. **Fetching**: Queries wiki for matching pages
3. **Parsing**: Extracts page title, sections, content using BeautifulSoup
4. **Caching**: Stores parsed content locally with timestamp
5. **Relevance**: Scores sections based on keyword matches
6. **Injection**: Adds relevant context to AI prompt
7. **Generation**: AI uses lore to generate accurate narrative

### Supported Wiki Types

- **Fandom.com wikis** (primary target)
- **MediaWiki sites** (partial support)
- **Custom wikis** (if HTML structure is similar)

### API Compatibility

RAG system is compatible with:
- OpenAI GPT models (gpt-3.5-turbo, gpt-4, etc.)
- Ollama local models (llama3.1:8b, qwen2.5:14b, etc.)
- OpenRouter models
- Any OpenAI-compatible API

## 🚀 Future Enhancements

Potential improvements:
- [ ] Semantic search using embeddings
- [ ] Multi-wiki search (search multiple settings at once)
- [ ] Image extraction from wiki pages
- [ ] Automatic relationship mapping
- [ ] Timeline extraction
- [ ] NPC database integration

## 📚 References

- [Critical Role Wiki](https://criticalrole.fandom.com/wiki/Exandria)
- [Forgotten Realms Wiki](https://forgottenrealms.fandom.com/wiki/Main_Page)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Documentation](https://docs.python-requests.org/)

---

**Questions or issues?** Create an issue on GitHub or check the troubleshooting section above.

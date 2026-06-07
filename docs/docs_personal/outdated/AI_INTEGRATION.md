# AI Integration Guide

## D&D Character Consultant System

This guide explains how to integrate AI/LLM capabilities into the D&D Character Consultant System.

## Features

The AI integration provides:

- **AI-Enhanced Character Reactions** - Characters respond with AI-generated dialogue and actions
- **Intelligent DC Suggestions** - AI-assisted difficulty calculations considering character abilities
- **Per-Character Configuration** - Each character can have unique AI settings
- **Provider Flexibility** - Works with OpenAI, Ollama (local), OpenRouter, and any OpenAI-compatible API
- **Graceful Fallback** - System works perfectly without AI (rule-based suggestions)
- **Structured JSON Output** - json_mode=True requests structured responses natively
- **Streaming** - chat_completion_stream() yields deltas for Gatsby/frontend display
- **Retry with Fallback Models** - tenacity-backed retry and model_chain for resilience
- **Call Logging** - JSONL audit log of every LLM call via AI_CALL_LOG_PATH

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages installed:

- `openai` - OpenAI SDK (compatible with many providers)
- `tenacity` - Retry logic with exponential backoff
- `python-dotenv` - Environment variable management

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# For OpenAI (default)
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# For Ollama (local LLMs)
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2

# For OpenRouter
OPENAI_API_KEY=your-openrouter-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct
```

### Alternative: Centralized Configuration

Instead of using environment variables, you can use the centralized configuration system:

1. Run the setup: `python setup.py`
2. Or use the CLI: Select "Configure Settings" from the main menu
3. This creates `game_data/config.json` with all settings in one place

The system supports both methods:

- Centralized config (`config.json`) takes precedence
- Environment variables still work as fallback

### 3. Test the Integration

```bash
python3 tests/run_all_tests.py ai
```

This will verify your configuration and test basic AI functionality.

## Provider Configuration

### OpenAI

```env
OPENAI_API_KEY=sk-...your-key...
# OPENAI_BASE_URL=  # Leave empty for default
OPENAI_MODEL=gpt-4o-mini
```

Get your API key from: <https://platform.openai.com/api-keys>

### Ollama (Local LLMs)

1. Install Ollama: <https://ollama.ai>
2. Pull a model: `ollama pull llama3.2`
3. Configure:

```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2  # or mistral, mixtral, etc.
```

Structured output (json_mode=True) uses `format=json` in the Ollama API body
automatically — no extra configuration needed.

### OpenRouter

```env
OPENAI_API_KEY=sk-or-v1-...your-key...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct
```

Get your API key from: <https://openrouter.ai/keys>

Browse models: <https://openrouter.ai/models>

### Other OpenAI-Compatible Providers

The system works with any OpenAI-compatible API:

```env
OPENAI_API_KEY=your-provider-key
OPENAI_BASE_URL=https://your-provider-url/v1
OPENAI_MODEL=your-model-name
```

## Per-Character AI Configuration

Each character can have individual AI settings in their JSON file:

```json
{
  "name": "Gandalf the Grey",
  "dnd_class": "Wizard",
  "level": 20,
  "backstory": "An ancient wizard...",
  "personality_traits": ["Wise", "Patient", "Mysterious"],

  "ai_config": {
    "enabled": true,
    "model": "gpt-4",
    "temperature": 0.9,
    "max_tokens": 1500,
    "system_prompt": "You are Gandalf the Grey, a wise and ancient wizard...",
    "custom_parameters": {}
  }
}
```

### Configuration Options

- **`enabled`** (boolean): Whether to use AI for this character
- **`model`** (string): Override global model for this character
- **`base_url`** (string): Override API endpoint for this character
- **`api_key`** (string): Use different API key for this character
- **`temperature`** (float 0.0-2.0): Controls randomness (higher = more creative)
- **`max_tokens`** (int): Maximum response length
- **`system_prompt`** (string): Custom system prompt for character roleplay
- **`custom_parameters`** (dict): Provider-specific parameters

### Character-Specific System Prompts

Create unique AI personalities for each character:

```json
{
  "name": "Aragorn",
  "ai_config": {
    "enabled": true,
    "temperature": 0.7,
    "system_prompt": "You are Aragorn, son of Arathorn, rightful heir to the throne of Gondor. You speak with quiet confidence and lead by example."
  }
}
```

### Building a Client for a Character

Use `build_client_for_character()` to create a client with character-level overrides:

```python
from src.ai.ai_client import build_client_for_character
from src.ai.ai_client import CharacterAIConfig, AIRequestParams

char_config = CharacterAIConfig(
    enabled=True,
    model="gpt-4",
    request_params=AIRequestParams(temperature=0.9, max_tokens=1500),
)

client = build_client_for_character(char_config, default_client=default_ai_client)
```

`CharacterAIConfig` is a pure data class — it holds configuration only. Client
construction is handled by the free function.

## Usage Examples

### In Interactive CLI

The CLI automatically uses AI if configured:

```bash
python3 dnd_consultant.py
```

Select **"3. Get Character Consultation"** - AI will be used automatically if available.

### In Python Code

```python
from src.ai.ai_client import AIClient, get_client_for_task

# Task-specific client (uses 'creative' profile for story, 'fast' for analysis)
ai_client = get_client_for_task("story_generation")

# Direct client — reads from centralized config or env vars
ai_client = AIClient()

# Chat completion
messages = [
    ai_client.create_system_message("You are a D&D narrator."),
    ai_client.create_user_message("Describe the party entering a dungeon."),
]
response = ai_client.chat_completion(messages)

# Structured JSON output (removes regex fallback parsing)
json_response = ai_client.chat_completion(messages, json_mode=True)

# Streaming output (returns a generator of str chunks)
for chunk in ai_client.chat_completion_stream(messages):
    print(chunk, end="", flush=True)
```

### Batch Embeddings

`embed()` accepts either a single string or a list of strings:

```python
# Single embedding
vector: list[float] = ai_client.embed("fireball spell description")

# Batch embedding (single API call, more efficient for Milvus reindexing)
vectors: list[list[float]] = ai_client.embed([
    "fireball spell description",
    "cure wounds spell description",
    "eldritch blast cantrip",
])
```

## Advanced Configuration

### Retry and Fallback

`AIClient` uses tenacity to retry transient failures (rate limits, connection
errors, timeouts). Configure via `**config` kwargs:

```python
client = AIClient(
    timeout=60.0,              # request timeout in seconds
    max_retries=5,             # attempts per model before giving up
    backoff_strategy="exponential",  # or "fixed"
    model_chain=["gpt-4o", "gpt-4o-mini"],  # fallback chain after primary
)
```

When the primary model exhausts its retries, the next model in `model_chain`
is tried automatically.

### Temperature Settings

- **0.0-0.3**: Deterministic, factual (good for rules/mechanics)
- **0.4-0.7**: Balanced (good for most roleplay)
- **0.8-1.2**: Creative, varied (good for quirky characters)
- **1.3-2.0**: Very random, experimental

### Max Tokens

- **500-1000**: Short responses, quick actions
- **1000-2000**: Standard roleplay and descriptions
- **2000+**: Detailed narratives, long-form content

### Custom Parameters

Some providers support additional parameters:

```json
{
  "ai_config": {
    "enabled": true,
    "custom_parameters": {
      "top_p": 0.9,
      "frequency_penalty": 0.5,
      "presence_penalty": 0.3
    }
  }
}
```

## Call Logging

Set `AI_CALL_LOG_PATH` to write a JSONL audit log of every `chat_completion`
call. Each line contains: `ts`, `model`, `latency`, `tokens`, `messages`,
`response`.

```env
AI_CALL_LOG_PATH=logs/ai_calls.jsonl
```

The log is appended to on every call. The parent directory is created
automatically. Leave unset to disable logging.

## Fallback Behavior

The system is designed to work without AI:

1. **AI Available**: Uses AI-enhanced suggestions with rule-based backup
2. **AI Configured but Fails**: Falls back via tenacity retry, then rule-based
3. **AI Not Configured**: Uses only rule-based suggestions

## Security & Privacy

- **Local LLMs**: Use Ollama for complete privacy
- **API Keys**: Stored in `.env` (gitignored)
- **Character Data**: Never sent to AI unless explicitly requested
- **Story Content**: AI only processes what you explicitly ask
- **Sidecar Auth**: Set SIDECAR_SECRET for header-based auth on all routes

## Cost Considerations

### Ollama (Local)

- **Free**: No per-request costs
- **Requires**: Decent GPU or CPU
- **Models**: 7B-13B work on most systems

### OpenRouter Pricing

- **Varies**: By model selected
- **Llama models**: Often very cheap or free

## Milvus Semantic Search (Optional)

Milvus is an optional vector database that replaces keyword-based retrieval
with semantic similarity search across characters, NPCs, story files, and
wiki lore. See [docs/MILVUS_INTEGRATION.md](MILVUS_INTEGRATION.md) for the
full quickstart.

### Enable Milvus

```env
MILVUS_ENABLED=true
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_EMBEDDING_MODEL=text-embedding-3-small
```

`MILVUS_EMBEDDING_MODEL` must refer to a model your AI provider supports for
embeddings calls. `AIClient.embed()` accepts a list of strings for batch
indexing — the full collection can be indexed in a fraction of the API calls
compared to one-at-a-time.

### Build or rebuild the index

```bash
python3 dnd_consultant.py --reindex
```

Or via the DDEV convenience wrapper (from `drupal-cms/`):

```bash
ddev milvus-reindex
```

---

## Troubleshooting

```bash
pip install -r requirements.txt
```

### "AI completion failed: api_key"

Check your `.env` file has `OPENAI_API_KEY` set correctly.

### "Connection failed"

- For Ollama: Ensure Ollama is running (`ollama serve`)
- For OpenAI/OpenRouter: Check internet connection
- For custom providers: Verify `OPENAI_BASE_URL` is correct

### AI responses are inconsistent

- Lower the temperature (0.5-0.7 for more consistency)
- Add more detailed system prompts
- Use character-specific configurations

## API Reference

### AIClient

```python
AIClient(
    api_key=None,           # API key (default: OPENAI_API_KEY env var)
    base_url=None,          # API endpoint (default: OpenAI)
    model=None,             # Model name (default: OPENAI_MODEL env var)
    # The following are passed via **config kwargs:
    default_temperature=0.7,     # Default temperature
    default_max_tokens=1000,     # Default max tokens
    timeout=30.0,                # Request timeout in seconds
    max_retries=3,               # Tenacity retry attempts on transient errors
    backoff_strategy="exponential",  # "exponential" or "fixed"
    model_chain=[],              # Fallback models tried after primary
    embedding_model="",          # Embedding model (OPENAI_EMBEDDING_MODEL env var)
)
```

Key methods:

- **`chat_completion(messages, json_mode=False, **kwargs)`** - Blocking completion
- **`chat_completion_stream(messages, **kwargs)`** - Generator of str chunks
- **`embed(text)`** - Single str → List[float]; List[str] → List[List[float]]
- **`create_system_message(prompt)`** / **`create_user_message(content)`**

### CharacterAIConfig

```python
CharacterAIConfig(
    enabled=False,          # Enable AI for character
    model=None,             # Character-specific model
    base_url=None,          # Character-specific endpoint
    api_key=None,           # Character-specific key
    system_prompt=None,     # Custom system prompt
    request_params=AIRequestParams(temperature=0.7, max_tokens=1000),
)
```

Build a client from this config:

```python
from src.ai.ai_client import build_client_for_character

client = build_client_for_character(char_config, default_client)
```

### Factory Functions

```python
from src.ai.ai_client import get_client_for_task, build_client_for_character

# Task-routed client (uses model profiles from config)
client = get_client_for_task("story_generation")

# Character-specific client
client = build_client_for_character(char_config, default_client)
```

### CharacterConsultant AI Methods

- **`suggest_reaction_ai(situation, context)`** - AI-enhanced character reaction
- **`suggest_dc_for_action_ai(action, context)`** - AI-assisted DC suggestion
- **`_get_ai_client()`** - Get appropriate AI client for character
- **`build_character_system_prompt()`** - Build character roleplay prompt

## RAG Integration: Spell and Ability Lookup

The system includes Retrieval-Augmented Generation (RAG) integration for
accurate D&D spell and ability descriptions.

### Shared Spell Lookup Helper

Located in `src/utils/spell_lookup_helper.py`, this utility provides
spell/ability lookup for story and combat narratives:

```python
from src.utils.spell_lookup_helper import lookup_spells_and_abilities

prompt = "The wizard casts Fireball and the paladin uses Divine Smite"
context = lookup_spells_and_abilities(prompt)
# Returns formatted rules context or empty string if RAG unavailable
```

Lookup is backed by `RAGSystem.get_rules_context_for_prompt()` — no hardcoded
spell lists. Any spell or ability that appears in the configured rules wiki
is supported.

### Graceful Fallback

If RAG system is unavailable:

- Stories and combat narratives still generate normally
- No RAG context is added, system continues without errors

### Configuration

Point `RAG_RULES_BASE_URL` at any D&D 5e rules wiki (e.g., `https://5thsrd.org`).

## Best Practices

1. **Start Small**: Test with one character first
2. **Use Templates**: Create reusable system prompts
3. **Monitor Costs**: Track API usage if using paid services; enable AI_CALL_LOG_PATH
4. **Local First**: Use Ollama for development and testing
5. **Fallback Always**: Don't rely solely on AI - rule-based works too
6. **Character Voice**: Use system prompts to maintain consistent character voice
7. **Privacy**: Use local models for sensitive campaign content

---

For questions or issues, refer to the main [README.md](../README.md) or create
an issue in the repository.

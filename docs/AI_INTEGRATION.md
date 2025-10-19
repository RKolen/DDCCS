# AI Integration Guide
## D&D Character Consultant System

This guide explains how to integrate AI/LLM capabilities into the D&D Character Consultant System.

##  Features

The AI integration provides:
- **AI-Enhanced Character Reactions** - Characters respond with AI-generated dialogue and actions
- **Intelligent DC Suggestions** - AI-assisted difficulty calculations considering character abilities
- **Per-Character Configuration** - Each character can have unique AI settings
- **Provider Flexibility** - Works with OpenAI, Ollama (local), OpenRouter, and any OpenAI-compatible API
- **Graceful Fallback** - System works perfectly without AI (rule-based suggestions)

##  Installation

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `openai` - OpenAI SDK (compatible with many providers)
- `python-dotenv` - Environment variable management

### 2. Configure Environment

Copy the example environment file:
```powershell
copy .env.example .env
```

Edit `.env` with your configuration:

```env
# For OpenAI (default)
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# For Ollama (local LLMs)
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2

# For OpenRouter
OPENAI_API_KEY=your-openrouter-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct
```

### 3. Test the Integration

```powershell
python test_ai_integration.py
```

This will verify your configuration and test basic AI functionality.

##  Provider Configuration

### OpenAI

```env
OPENAI_API_KEY=sk-...your-key...
# OPENAI_BASE_URL=  # Leave empty for default
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4, gpt-4-turbo
```

Get your API key from: https://platform.openai.com/api-keys

### Ollama (Local LLMs)

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3.2`
3. Configure:

```env
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.2  # or mistral, mixtral, etc.
```

### OpenRouter

```env
OPENAI_API_KEY=sk-or-v1-...your-key...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct
```

Get your API key from: https://openrouter.ai/keys

Browse models: https://openrouter.ai/models

### Other OpenAI-Compatible Providers

The system works with any OpenAI-compatible API:

```env
OPENAI_API_KEY=your-provider-key
OPENAI_BASE_URL=https://your-provider-url/v1
OPENAI_MODEL=your-model-name
```

##  Per-Character AI Configuration

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
    "system_prompt": "You are Aragorn, son of Arathorn, rightful heir to the throne of Gondor. You are a skilled ranger and warrior, humble yet noble. You speak with quiet confidence and lead by example. Your responses should reflect your duty to protect the innocent and restore the kingdom."
  }
}
```

##  Usage Examples

### In Interactive CLI

The CLI automatically uses AI if configured:

```powershell
python dnd_consultant.py
```

Select **"3. Get Character Consultation"** - AI will be used automatically if available.

### In Python Code

```python
from character_consultants import CharacterConsultant, CharacterProfile
from ai_client import AIClient
from character_sheet import DnDClass

# Create AI client
ai_client = AIClient()  # Uses environment configuration

# Load character
profile = CharacterProfile.load_from_file("characters/wizard.json")
consultant = CharacterConsultant(profile, ai_client=ai_client)

# Get AI-enhanced reaction
situation = "A dragon appears on the horizon"
reaction = consultant.suggest_reaction_ai(situation)

if reaction.get('ai_enhanced'):
    print(f"AI Response: {reaction['ai_response']}")
else:
    print(f"Rule-based: {reaction['class_reaction']}")

# Get AI-enhanced DC suggestion  
action = "Convince the king to send reinforcements"
dc_suggestion = consultant.suggest_dc_for_action_ai(action)

print(f"Suggested DC: {dc_suggestion['suggested_dc']}")
if dc_suggestion.get('ai_analysis'):
    print(f"AI Analysis: {dc_suggestion['ai_analysis']}")
```

### Character-Specific AI Client

```python
from ai_client import CharacterAIConfig

# Create character-specific config
config = CharacterAIConfig(
    enabled=True,
    model="gpt-4",
    temperature=0.9,
    system_prompt="You are a mischievous rogue with a heart of gold..."
)

# Add to character profile
profile.ai_config = config
profile.save_to_file("characters/rogue.json")
```

##  Advanced Configuration

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

##  Fallback Behavior

The system is designed to work without AI:

1. **AI Available**: Uses AI-enhanced suggestions with rule-based backup
2. **AI Configured but Fails**: Falls back to rule-based, logs error
3. **AI Not Configured**: Uses only rule-based suggestions
4. **Dependencies Missing**: System works normally without AI features

##  Security & Privacy

- **Local LLMs**: Use Ollama for complete privacy
- **API Keys**: Stored in `.env` (gitignored)
- **Character Data**: Never sent to AI unless explicitly requested
- **Story Content**: AI only processes what you explicitly ask

##  Cost Considerations

### OpenAI Pricing (approximate)
- **GPT-3.5-Turbo**: ~$0.002 per request
- **GPT-4**: ~$0.03-0.06 per request

### Ollama (Local)
- **Free**: No per-request costs
- **Requires**: Decent GPU or CPU
- **Models**: 7B-13B work on most systems

### OpenRouter
- **Varies**: By model selected
- **Llama models**: Often very cheap or free

##  Troubleshooting

### "Import openai could not be resolved"
```powershell
pip install -r requirements.txt
```

### "AI completion failed: api_key"
Check your `.env` file has `OPENAI_API_KEY` set correctly

### "Connection failed"
- For Ollama: Ensure Ollama is running (`ollama serve`)
- For OpenAI/OpenRouter: Check internet connection
- For custom providers: Verify `OPENAI_BASE_URL` is correct

### AI responses are inconsistent
- Lower the temperature (0.5-0.7 for more consistency)
- Add more detailed system prompts
- Use character-specific configurations

### Costs too high
- Switch to Ollama for local, free inference
- Use smaller OpenRouter models
- Use GPT-3.5-Turbo instead of GPT-4

##  API Reference

### AIClient

```python
AIClient(
    api_key=None,           # API key (default: env var)
    base_url=None,          # API endpoint (default: OpenAI)
    model=None,             # Model name (default: gpt-3.5-turbo)
    default_temperature=0.7, # Default temperature
    default_max_tokens=1000  # Default max tokens
)
```

### CharacterAIConfig

```python
CharacterAIConfig(
    enabled=False,          # Enable AI for character
    model=None,             # Character-specific model
    base_url=None,          # Character-specific endpoint
    api_key=None,           # Character-specific key
    temperature=0.7,        # Character-specific temperature
    max_tokens=1000,        # Character-specific max tokens
    system_prompt=None,     # Custom system prompt
    custom_parameters={}    # Additional parameters
)
```

### CharacterConsultant AI Methods

- **`suggest_reaction_ai(situation, context)`** - AI-enhanced character reaction
- **`suggest_dc_for_action_ai(action, context)`** - AI-assisted DC suggestion
- **`_get_ai_client()`** - Get appropriate AI client for character
- **`_build_character_system_prompt()`** - Build character roleplay prompt

##  Best Practices

1. **Start Small**: Test with one character first
2. **Use Templates**: Create reusable system prompts
3. **Monitor Costs**: Track API usage if using paid services
4. **Local First**: Use Ollama for development and testing
5. **Fallback Always**: Don't rely solely on AI - rule-based works too
6. **Character Voice**: Use system prompts to maintain consistent character voice
7. **Privacy**: Use local models for sensitive campaign content

##  Future Enhancements

Planned AI features:
- **Story generation** - AI-assisted plot development
- **NPC dialogue** - AI-powered NPC conversations
- **World-building** - AI help with locations and lore
- **Combat narration** - AI-enhanced combat descriptions
- **Character development** - AI suggestions for character arcs

---

For questions or issues, refer to the main [README.md](../README.md) or create an issue in the repository.

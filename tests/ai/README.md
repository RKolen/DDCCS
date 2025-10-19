# AI Integration Tests

## What We Test

This folder contains tests for the AI integration subsystem, which provides optional AI enhancement features for character consultants, story generation, and campaign wiki integration.

### Test Files

1. **test_ai_env_config.py** - AI Environment Configuration
   - Validates .env file configuration
   - Tests connection to Ollama local LLM server
   - Verifies configured model availability
   - Checks API endpoint accessibility

2. **test_ai_client.py** - AI Client Interface
   - Tests AIClient initialization (default, custom, partial configs)
   - Validates message helper methods (system, user, assistant)
   - Tests environment variable loading
   - Validates CharacterAIConfig dataclass operations
   - Tests configuration serialization/deserialization
   - Verifies client creation from character configs

3. **test_rag_system.py** - RAG System (Retrieval-Augmented Generation)
   - Tests WikiCache initialization and operations
   - Validates cache key generation and storage
   - Tests cache TTL (time-to-live) expiration
   - Verifies cache statistics and management
   - Tests WikiClient initialization
   - Validates custom item filtering (homebrew blocking)

4. **test_all_ai.py** - AI Subsystem Test Runner
   - Runs all AI tests in sequence
   - Provides comprehensive test summary
   - Returns proper exit codes for CI/CD

## Why We Test This

**AI features are optional** but must work correctly when enabled:

1. **Environment Configuration** - Users may use OpenAI, Ollama, or other providers
   - Must validate configuration before attempting API calls
   - Must detect connection issues early
   - Must verify model availability

2. **Client Interface** - Flexible AI client must support multiple providers
   - OpenAI API compatibility required
   - Environment variable fallbacks must work
   - Character-specific overrides must be possible
   - Configuration must be serializable (saved in character JSON)

3. **RAG System** - Wiki integration enhances story accuracy
   - Caching prevents redundant network requests
   - TTL prevents serving stale data
   - Custom items must be blocked from wiki lookups
   - Cache management prevents disk bloat

## Running Tests

### Run All AI Tests
```bash
python tests/run_all_tests.py ai
```

### Run Individual Test Files
```bash
# Environment configuration
python tests/ai/test_ai_env_config.py

# AI client interface
python tests/ai/test_ai_client.py

# RAG system
python tests/ai/test_rag_system.py

# All AI tests with comprehensive output
python tests/ai/test_all_ai.py
```

### Run Specific Test Functions
All test files can be run directly and will execute all their test functions.

## Test Coverage

### What's Tested
- ✅ Environment variable loading and defaults
- ✅ AI client initialization (all configuration modes)
- ✅ Message creation helpers
- ✅ CharacterAIConfig serialization
- ✅ WikiCache operations (set, get, delete, stats)
- ✅ Cache TTL expiration
- ✅ WikiClient initialization
- ✅ Custom item filtering

### What's NOT Tested (Intentionally)
- ❌ **Actual API calls** - Requires live connection + API keys
  - Would make tests slow and dependent on external services
  - Would consume API credits
  - Network issues would cause false failures
  
- ❌ **Actual web scraping** - Requires internet connection
  - Would be slow and unreliable
  - Fandom wikis may change structure
  - Rate limiting could cause failures

- ❌ **AI response quality** - Subjective and model-dependent
  - Different models produce different outputs
  - No objective "correct" answer
  - Would require human evaluation

### Future Test Enhancements
- Mock API call testing (if needed for edge cases)
- Integration tests with test API endpoints
- Performance benchmarks for caching
- Memory usage tests for large wiki pages

## Integration with Main System

### How AI Features Are Used

1. **Character Consultants** (src/characters/consultants/)
   - Optional AI-enhanced reactions
   - Character-specific AI configurations
   - Falls back to rule-based if AI disabled

2. **Story Generation** (src/stories/)
   - Optional AI assistance for plot hooks
   - RAG system provides campaign lore
   - Enhances consistency with wiki facts

3. **DM Tools** (src/dm/)
   - History check helper uses RAG system
   - Wiki lookups for locations, NPCs, events
   - Custom items blocked from lookups

### Configuration Files

**Environment Variables (.env):**
```env
# AI Provider Configuration
OPENAI_API_KEY=your_api_key_or_ollama
OPENAI_BASE_URL=http://localhost:11434/v1  # Ollama local
OPENAI_MODEL=qwen2.5:14b

# RAG System Configuration
RAG_ENABLED=true
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki
RAG_CACHE_TTL=604800  # 7 days in seconds
```

**Character AI Config (in character JSON):**
```json
{
  "ai_config": {
    "enabled": true,
    "model": "qwen2.5:14b",
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt": "You are a brave fighter..."
  }
}
```

## Dependencies

**Required:**
- Python 3.13+
- No external dependencies (uses only standard library)

**Optional (for AI features to work):**
- `openai` package (AI client)
- `requests` package (RAG system)
- `beautifulsoup4` package (RAG system)
- `python-dotenv` package (environment loading)

**Note:** Tests run successfully even without optional packages installed. They test the code structure and configuration handling, not the actual API calls.

## Quality Standards

All tests in this folder:
- ✅ Achieve 10.00/10 pylint rating
- ✅ Use no pylint disable comments
- ✅ Follow DRY principle (common code in test_helpers.py)
- ✅ Include comprehensive docstrings
- ✅ Clean up test data (use tempfile for caching tests)
- ✅ Work with run_all_tests.py master runner
- ✅ Provide clear, descriptive output

## Maintenance Notes

**When modifying AI system code:**
1. Ensure tests still pass with new changes
2. Add new tests for new functionality
3. Update this README if test coverage changes
4. Maintain 10.00/10 pylint on all test files

**Common Issues:**
- Import errors: Run from project root
- Ollama connection fails: Start Ollama service
- Model not found: Pull model with `ollama pull <model_name>`
- Cache tests fail: Ensure tempfile has write permissions

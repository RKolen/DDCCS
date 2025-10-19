"""
Test: Verify AI configuration is loaded from .env and uses Ollama local settings
"""

import os
import sys
from pathlib import Path
import requests
import test_helpers
# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and configure test environment (UTF-8, project paths)
project_root = test_helpers.setup_test_environment()

def load_env(env_path):
    """Load environment variables from .env file into a dictionary."""
    env_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

EXPECTED = {
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
    "OPENAI_BASE_URL": os.environ.get("OPENAI_BASE_URL"),
    "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
}

def test_ollama_connection_and_model():
    """Test that Ollama is running and the configured model is available."""
    env_path = project_root / ".env"
    env = load_env(env_path)
    base_url = env.get("OPENAI_BASE_URL")
    model_name = env.get("OPENAI_MODEL")
    print("--- AI Connection Details ---")
    print(f"OPENAI_BASE_URL: {base_url}")
    print(f"OPENAI_MODEL: {model_name}")
    print("----------------------------")
    if not base_url or not model_name:
        print("ERROR: OPENAI_BASE_URL and OPENAI_MODEL must be set in .env.")
        return
    # Try to connect to Ollama and list models
    try:
        # Use Ollama's /api/tags endpoint to list models
        api_url = base_url.replace("/v1", "") + "/api/tags"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]
        print(f"Available models: {models}")
        assert (
            model_name in models
        ), f"Expected model '{model_name}' not found in Ollama models: {models}"
        print(f"SUCCESS: Model '{model_name}' is loaded and available in Ollama.")
    except Exception as e:
        print(f"ERROR: Could not connect to Ollama or verify model. {e}")
        raise

if __name__ == "__main__":
    test_ollama_connection_and_model()

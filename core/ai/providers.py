import os
import logging
from pathlib import Path
from dotenv import load_dotenv

import google.generativeai as genai
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger("EH_Brain")

# Load environment configuration
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

def get_keys():
    """Retrieve necessary API keys from environment."""
    return {
        "GEMINI": os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", ""),
        "OPENAI": os.environ.get("OPENAI_API_KEY", ""),
        "GITHUB": os.environ.get("GITHUB_TOKEN", "")
    }

def initialize_providers(model_gemini="gemini-3-flash-preview", model_openai="gpt-4o", model_github="gpt-4o"):
    """
    Initialize AI providers.
    Returns a dictionary of configured clients, models, and keys.
    """
    keys = get_keys()
    providers = {
        "keys": keys,
        "github_client": None,
        "openai_client": None,
        "gemini_chat": None,
        "gemini_model": None,
        "model_openai": model_openai,
        "model_github": model_github,
        "model_gemini": model_gemini
    }

    if keys["GITHUB"] and OpenAI:
        try:
            providers["github_client"] = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=keys["GITHUB"]
            )
        except Exception as e:
            logger.warning(f"GitHub Client Init Failed: {e}")

    if keys["GEMINI"]:
        genai.configure(api_key=keys["GEMINI"])
        # The actual chat initialization usually requires the system prompt, 
        # so we leave gemini_chat empty here and let the client initialize it later
        # once the prompt is assembled.

    if keys["OPENAI"] and OpenAI:
        providers["openai_client"] = OpenAI(api_key=keys["OPENAI"])

    return providers

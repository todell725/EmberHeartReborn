import logging
import os
from pathlib import Path

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger("EH_Brain")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env", override=True)


def get_keys():
    return {
        "OLLAMA_BASE_URL": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "OLLAMA_MODEL": os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
    }


def initialize_providers():
    keys = get_keys()
    providers = {
        "keys": keys,
        "ollama_client": None,
        "model_ollama": keys["OLLAMA_MODEL"],
        # Raw Ollama base URL (no /v1) for native API calls like format=json
        "ollama_base": keys["OLLAMA_BASE_URL"].removesuffix("/v1").removesuffix("/"),
    }

    if not OpenAI:
        logger.warning("OpenAI SDK unavailable; Ollama client not initialized.")
        return providers

    try:
        providers["ollama_client"] = OpenAI(
            base_url=keys["OLLAMA_BASE_URL"],
            api_key="ollama",  # Ollama ignores this but the SDK requires a non-empty string.
        )
        logger.info(
            "Ollama client initialized: %s | Model: %s",
            keys["OLLAMA_BASE_URL"],
            keys["OLLAMA_MODEL"],
        )
    except Exception as e:
        logger.warning("Ollama Client Init Failed: %s", e)

    return providers

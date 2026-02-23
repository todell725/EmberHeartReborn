import os
import logging
from pathlib import Path
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger("EH_Brain")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

def get_keys():
    return {
        "OLLAMA_BASE_URL": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "OLLAMA_MODEL": os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
        "GEMINI": os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", ""),
        "OPENAI": os.environ.get("OPENAI_API_KEY", ""),
        "GITHUB": os.environ.get("GITHUB_TOKEN", "")
    }

def initialize_providers(model_gemini="gemini-2.0-flash", model_openai="gpt-4o", model_github="gpt-4o"):
    keys = get_keys()
    providers = {
        "keys": keys,
        "ollama_client": None,
        "github_client": None,
        "openai_client": None,
        "gemini_chat": None,
        "gemini_model": None,
        "model_ollama": keys["OLLAMA_MODEL"],
        "model_openai": model_openai,
        "model_github": model_github,
        "model_gemini": model_gemini,
        # Raw Ollama base URL (no /v1) for native API calls like format=json
        "ollama_base": keys["OLLAMA_BASE_URL"].rstrip("/v1").rstrip("/")
    }

    # 1. Ollama (Local — always try to connect)
    if OpenAI:
        try:
            providers["ollama_client"] = OpenAI(
                base_url=keys["OLLAMA_BASE_URL"],
                api_key="ollama"  # Ollama ignores this but the SDK requires a non-empty string
            )
            logger.info(f"Ollama client initialized: {keys['OLLAMA_BASE_URL']} | Model: {keys['OLLAMA_MODEL']}")
        except Exception as e:
            logger.warning(f"Ollama Client Init Failed: {e}")

    # 2. GitHub Models (Cloud fallback)
    if keys["GITHUB"] and OpenAI:
        try:
            providers["github_client"] = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=keys["GITHUB"]
            )
        except Exception as e:
            logger.warning(f"GitHub Client Init Failed: {e}")

    # 3. Gemini (Cloud fallback)
    if keys["GEMINI"] and genai:
        genai.configure(api_key=keys["GEMINI"])

    # 4. OpenAI (Cloud fallback)
    if keys["OPENAI"] and OpenAI:
        providers["openai_client"] = OpenAI(api_key=keys["OPENAI"])

    return providers

import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure logging doesn't clutter terminal during test unless desired
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test_Routing")

from core.ai.client import EHClient

async def test_routing():
    print("\n--- Starting specialized Model Routing Test ---")
    
    # Initialize client (it will load .env keys automatically)
    client = EHClient(thread_id="test_routing_thread")
    
    test_cases = [
        {"type": "rp", "prompt": "Hello! Who are you?", "desc": "Roleplay Routing (Mythomax)"},
        {"type": "reasoning", "prompt": "Analyze the state of the world.", "desc": "Reasoning Routing (DeepSeek-R1)"},
        {"type": "general", "prompt": "Hello.", "desc": "General Routing (Qwen/Gemma)"},
        {"type": "nonexistent", "prompt": "How are you?", "desc": "Fallback Check (General)"}
    ]
    
    for case in test_cases:
        print(f"\n[TEST] {case['desc']} | Type: {case['type']}")
        try:
            # We use a short timeout simulation if we don't want to actually wait for LLM output,
            # but here we actually want to see if the provider call succeeds.
            response = client.chat(case['prompt'], model_type=case['type'])
            print(f"[SUCCESS] Response length: {len(response)}")
            print(f"Preview: {response[:100]}...")
        except Exception as e:
            print(f"[FAILED] {e}")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_routing())
    except Exception as e:
        # Fallback for environments where loop is already running or client.chat isn't async
        print(f"Sync Execution Check...")
        # Note: EHClient.chat in the code I modified is SYNC (it uses _chat_openai_compatible which is sync)
        # So I don't actually need asyncio.run here, but it doesn't hurt.
        client = EHClient(thread_id="test_routing_thread_sync")
        for case in [
            {"type": "rp", "prompt": "Hello! Who are you?", "desc": "Roleplay Routing (Mythomax)"},
            {"type": "reasoning", "prompt": "Analyze the current narrative.", "desc": "Reasoning Routing (DeepSeek-R1)"}
        ]:
            print(f"\n[TEST] {case['desc']} | Type: {case['type']}")
            response = client.chat(case['prompt'], model_type=case['type'])
            print(f"[SUCCESS] Response length: {len(response)}")
            print(f"Preview: {response[:100]}...")

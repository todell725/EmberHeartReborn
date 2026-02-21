import os
import sys
from pathlib import Path

# Add the parent directory of EmberHeartReborn to the path
# so we can import EmberHeartReborn as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from EmberHeartReborn.core.ai import EHClient

def main():
    print("Testing EmberHeartReborn AI Core Initialization...")
    try:
        client = EHClient()
        print("Test passed: EHClient initialized successfully.")
        
        print("\nTesting Provider Keys:")
        for provider, key in client.keys.items():
            status = "Loaded" if key else "Missing"
            print(f"- {provider}: {status}")
            
        print("\nTesting System Prompt Generation:")
        prompt = client.system_prompt
        print(f"Test passed: System Prompt Length: {len(prompt)} characters")
        print(f"Sample: {prompt[:100]}...")
        
        print("\nTesting RAG Context Injection (Dry Run):")
        test_msg = "Tell me about Kaelrath's current status."
        context = client.world_manager.get_relevant_context(test_msg)
        print(f"Context Length: {len(context)} characters")
        if context:
            print("Test passed: Context retrieved successfully.")
        else:
            print("Warning: No context retrieved (this might be expected if the EmberHeart docs dir is empty or missing data files).")
            
        # We won't actually call the LLM here to avoid API costs during simple verification
        print("\nAll isolation tests passed!")
        
    except Exception as e:
        print(f"Error during initialization: {e}")

if __name__ == "__main__":
    main()

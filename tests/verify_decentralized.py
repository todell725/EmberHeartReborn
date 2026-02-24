import sys
from pathlib import Path

ROOT = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(ROOT))

from core.storage import resolve_character
from core.ai.rag import WorldContextManager

def test_character_resolution():
    print("--- Testing character resolution ---")
    targets = ["Marta Hale", "EH-49", "Silvara", "Borin"]
    for t in targets:
        match = resolve_character(t)
        if match:
            print(f"  OK: Found '{t}' -> {match.get('name')} [{match.get('id')}]")
        else:
            print(f"  FAILED: Could not find '{t}'")

def test_rag_injection():
    print("\n--- Testing RAG injection ---")
    wcm = WorldContextManager(ROOT)
    
    queries = [
        "Tell me about Marta Hale",
        "How is the party doing? Check health.",
        "What is Silvara's story?",
        "Kaelrath tells Silvy the current state of affairs."
    ]
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        context = wcm.get_relevant_context(q)
        if "### Character Sketch" in context or "PARTY STATUS" in context:
            # Print a snippet of the context
            lines = context.strip().split("\n")
            print(f"  OK: Context generated ({len(lines)} lines)")
            for line in lines[:5]:
                print(f"    {line}")
        else:
            print(f"  FAILED: No relevant character/party context found for '{q}'")

if __name__ == "__main__":
    try:
        test_character_resolution()
        test_rag_injection()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

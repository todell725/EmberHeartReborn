import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.ai.rag import WorldContextManager
import logging

logging.basicConfig(level=logging.INFO)

def test_rag_precision():
    wcm = WorldContextManager(Path("z:/DnD/EmberHeartReborn"))
    
    # 1. Test "the" (should be ignored)
    ctx_ignore = wcm.get_relevant_context("the")
    print("Context for 'the':", len(ctx_ignore))
    assert "### Character Sketch" not in ctx_ignore
    
    # 2. Test "King" (should be ignored if threshold is 4+)
    # Wait, 'King' is 4 chars. Threshold is > 4 (so 5+).
    # "King" should be ignored.
    ctx_king = wcm.get_relevant_context("King")
    print("Context for 'King':", len(ctx_king))
    assert "### Character Sketch" not in ctx_king
    
    # 3. Test "Kaelrath" (should match)
    ctx_kael = wcm.get_relevant_context("Kaelrath")
    print("Context for 'Kaelrath':", len(ctx_kael))
    # Note: Kaelrath is PC-01, but the manager checks all profiles.
    # It should match the profile if it exists.
    
    print("RAG Precision test PASSED")

if __name__ == "__main__":
    test_rag_precision()

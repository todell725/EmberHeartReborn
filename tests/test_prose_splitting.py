import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(project_root))

from core.formatting import parse_speaker_blocks

# Mock Identities
MOCK_IDENTITIES = {
    "Talmarr": {"name": "Talmarr", "avatar": "talmarr_url"},
    "Silvara": {"name": "Silvara", "avatar": "silvara_url"},
    "Mareth": {"name": "Mareth", "avatar": "mareth_url"},
    "Vaelis": {"name": "Vaelis", "avatar": "vaelis_url"},
    "DM": {"name": "DM", "avatar": "dm_url"}
}

TEST_P_CHAT = """Talmarr leaned back in her chair, eyes narrowed slightly as she asked, "What's going on with Garric? You mentioned something about an idea?" Silvara frowned, her brow furrowed in concern. "Is he planning something without consulting the Council or us?" Mareth set down her cup of drink and leaned forward, her interest piqued. "I've had some disagreements with him in the past, but he's usually been a steady hand on security matters." Vaelis scribbled some notes on a small piece of paper, muttering to herself about "frequency harmonics" before looking up at Kaelrath. "What did Garric say exactly?" she asked, her voice laced with curiosity and concern. The discussion was in full swing now, the party's dynamics coming together like a well-harmonized symphony."""

def test_split():
    print("Testing Heuristic Split...")
    # Since parse_speaker_blocks calls heuristic_prose_split if no tags are found:
    blocks = parse_speaker_blocks(TEST_P_CHAT, MOCK_IDENTITIES, set())
    
    for i, b in enumerate(blocks):
        print(f"[{i}] {b['speaker']}: {b['content'][:100]}...")
        
    expected_speakers = ["Talmarr", "Silvara", "Mareth", "Vaelis"]
    actual_speakers = [b['speaker'] for b in blocks if b['speaker'] != "DM"]
    
    if all(s in actual_speakers for s in expected_speakers):
        print("SUCCESS: All speakers detected and split.")
    else:
        print(f"FAILURE: Expected {expected_speakers}, got {actual_speakers}")

if __name__ == "__main__":
    test_split()

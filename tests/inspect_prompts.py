import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from core.ai.client import EHClient

def test_npc_prompt():
    print("--- Inspecting Selene Varis Prompt ---")
    client = EHClient(thread_id="test_thread", npc_name="Selene Varis")
    prompt = client.system_prompt
    print(prompt)
    
    # Check for forbidden keywords in the instructions part
    forbidden = ["Sovereign Advisor", "Antigravity", "AI helper"]
    # We only care if they appear as roles/identities, not if they are part of rule descriptions
    instructions = prompt.split("### WORLD LORE & LAWS:")[0]
    found = [f for f in forbidden if f in instructions]
    
    # Check if DM_RULES header leaked
    leaks = ["Dungeon Master Guidelines", "### RECENT ACCOMPLISHMENTS"]
    found_leaks = [l for l in leaks if l in prompt]
    
    if not found and not found_leaks:
        print("\n✅ Persona Shielding Verified: No Advisor logic or technical RAG headers in prompt.")
    else:
        print(f"\n❌ Persona Shielding Failed: Found {found + found_leaks}")

if __name__ == "__main__":
    test_npc_prompt()

import json
import re
from pathlib import Path

# Paths
ROOT = Path(r"z:\DnD\EmberHeartReborn")
NPC_PATH = ROOT / "state" / "NPC_STATE_FULL.json"
PARTY_PATH = ROOT / "state" / "PARTY_STATE.json"

# Import our actual code
import sys
sys.path.append(str(ROOT))
from core.ai.prompts import generate_world_rules

def verify_npc_persona(npc_name):
    print(f"\n--- Testing Persona: {npc_name} ---")
    
    # Simulate what EHClient does
    system_prompt = (
        f"You are {npc_name}. You are engaged in a private, 1-on-1 direct message with Kaelrath (the user).\n"
        f"### ROLEPLAY PROTOCOL:\n"
        f"1. You must strictly and exclusively roleplay as {npc_name} using the supplied lore.\n"
        f"2. You are a living inhabitant of the world, NOT an assistant or advisor.\n"
        f"3. Do NOT mention mechanics, file names, or 'injected context'.\n"
        f"5. **DIALOGUE SOVEREIGNTY**: NEVER describe the actions...\n"
    ) + generate_world_rules(ROOT, diegetic=True)
    
    # Audit for leaks
    weaver_leaks = re.findall(r"Chronicle Weaver|The Invisible DM|Dungeon Master", system_prompt)
    if weaver_leaks:
        print(f"FAILED: LEAKS FOUND: {weaver_leaks}")
    else:
        print("PASSED: No DM/Weaver leaks found.")
    
    # Audit for NPC name insertion
    if f"You are {npc_name}" in system_prompt:
        print(f"PASSED: Identity correctly set to {npc_name}")
    else:
        print(f"FAILED: Identity MISMATCH")

def verify_search_logic(target_name):
    print(f"\n--- Testing Search Logic: '{target_name}' ---")
    search_pool = []
    if NPC_PATH.exists():
        data = json.loads(NPC_PATH.read_text(encoding='utf-8'))
        search_pool.extend([n for n in data.get("npcs", [])])
    if PARTY_PATH.exists():
        data = json.loads(PARTY_PATH.read_text(encoding='utf-8'))
        search_pool.extend([p for p in data.get("party", [])])

    search_query = target_name.lower()
    
    # Match logic from characters.py
    match = next((n for n in search_pool if search_query == n.get('name', '').lower() or search_query == n.get('id', '').lower()), None)
    if not match:
        match = next((n for n in search_pool if search_query in n.get('name', '').lower()), None)
        
    if match:
        print(f"PASSED: Found: {match.get('name')} [{match.get('id')}]")
    else:
        print(f"FAILED: NOT FOUND")

if __name__ == "__main__":
    test_npcs = ["Marta Hale", "Jax", "Borin Ashmantle", "Silvara"]
    for npc in test_npcs:
        verify_npc_persona(npc)
        verify_search_logic(npc)
    
    # Test partial search
    verify_search_logic("Marta")
    verify_search_logic("EH-01")

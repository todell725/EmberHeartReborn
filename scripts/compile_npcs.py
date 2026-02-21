"""
compile_npcs.py — Rebuilds monoliths from individual character files.
Differentiates between NPCs (EH-XXX) and Party (PC-XXX).
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHARACTERS_DIR = ROOT / "characters"
NPC_OUT = ROOT / "state" / "NPC_STATE_FULL.json"
PARTY_OUT = ROOT / "state" / "PARTY_STATE.json"

def main():
    if not CHARACTERS_DIR.exists():
        print("Characters directory not found.")
        return

    npcs = []
    party = []

    # Find all character directories
    char_dirs = sorted([d for d in CHARACTERS_DIR.iterdir() if d.is_dir()])

    print(f"Aggregating {len(char_dirs)} characters...")

    for char_dir in char_dirs:
        profile_path = char_dir / "profile.json"
        state_path   = char_dir / "state.json"

        if not profile_path.exists():
            continue

        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)

        state = {}
        if state_path.exists():
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)

        # Merge: profile is base, state overlays runtime fields
        merged = {**profile, **state}
        
        char_id = merged.get("id", "")
        if char_id.startswith("EH-"):
            npcs.append(merged)
        elif char_id.startswith("PC-"):
            party.append(merged)
        
        print(f"  OK: Compiled {char_id}: {merged.get('name', '?')}")

    # Write NPC Monolith
    if npcs:
        with open(NPC_OUT, "w", encoding="utf-8") as f:
            json.dump({"npcs": npcs}, f, indent=2, ensure_ascii=False)
        print(f"\nRebuilt NPC_STATE_FULL.json - {len(npcs)} characters.")

    # Write Party Monolith
    if party:
        with open(PARTY_OUT, "w", encoding="utf-8") as f:
            json.dump({"party": party}, f, indent=2, ensure_ascii=False)
        print(f"Rebuilt PARTY_STATE.json - {len(party)} members.")

if __name__ == "__main__":
    main()

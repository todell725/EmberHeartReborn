import json
from pathlib import Path

# Mock ROOT_DIR
ROOT_DIR = Path(__file__).resolve().parent
db_path = ROOT_DIR / "EmberHeart" / "docs" / "SIDE_QUESTS_DB.json"
completion_path = ROOT_DIR / "EmberHeart" / "docs" / "QUEST_COMPLETION.json"
loot_path = ROOT_DIR / "EmberHeart" / "docs" / "PARTY_EQUIPMENT.json"
deeds_path = ROOT_DIR / "EmberHeart" / "docs" / "QUEST_DEEDS.md"
party_path = ROOT_DIR / "EmberHeart" / "docs" / "PARTY_STATE.json"

def test_sync():
    print("--- Testing Reward Sync Logic ---")
    qid = "SQ-01"
    xp = 750
    loot_list = ["Shard of Void-Glass", "150 Gold"]
    
    # 1. Test XP Sync
    try:
        print(f"Reading {party_path.name}...")
        data = json.loads(party_path.read_text(encoding='utf-8'))
        found_kael = False
        for char in data.get("party", []):
            if char['name'].startswith("Kaelrath"):
                old_xp = char.get("experience_points", 0)
                char["experience_points"] = old_xp + xp
                print(f"XP SYNC SUCCESS: {char['name']} {old_xp} -> {char['experience_points']}")
                found_kael = True
        if not found_kael:
            print("XP SYNC FAILED: Kaelrath not found in party list.")
    except Exception as e:
        print(f"XP SYNC ERROR: {e}")

    # 2. Test Loot Sync
    try:
        print(f"Reading {loot_path.name}...")
        data = json.loads(loot_path.read_text(encoding='utf-8'))
        inventory = data["party_equipment"]["King Kaelrath"]["inventory"]
        for item in loot_list:
            if item not in inventory:
                inventory.append(item)
                print(f"Added {item}")
        print("LOOT SYNC SUCCESS")
    except Exception as e:
        print(f"LOOT SYNC ERROR: {e}")

    # 3. Check Persistence Files
    print(f"Completion Path Exists: {completion_path.exists()}")
    print(f"Loot Path Exists: {loot_path.exists()}")
    print(f"Party Path Exists: {party_path.exists()}")
    print(f"Deeds Path Exists: {deeds_path.exists()}")

test_sync()

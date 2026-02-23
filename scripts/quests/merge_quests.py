import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
db_path = ROOT_DIR / 'EmberHeart' / 'docs' / 'SIDE_QUESTS_DB.json'
new_quests_path = ROOT_DIR / 'new_easy_quests_utf8.json'

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

with open(new_quests_path, 'r', encoding='utf-8') as f:
    new_quests_raw = json.load(f)

def normalize_quest(q):
    normalized = {
        "id": q["quest_id"],
        "title": q["title"],
        "difficulty": q["difficulty"],
        "xp_reward": q["rewards"].get("xp", 150),
        "prerequisites": "None",
        "description": q["hook"],
        "turns": [],
        "conclusion": "",
        "loot_table": q["rewards"].get("loot", []),
        "risk_matrix": {
            "failure_threshold": 3,
            "penalty": q["fail_condition"]
        }
    }
    
    for t in q["turns"]:
        normalized_turn = {
            "turn": t["turn_id"],
            "narrative": t["scenario"],
            "choice_a": t["choice_a"]["text"],
            "consequence_a": "Success.",
            "choice_b": t["choice_b"]["text"],
            "consequence_b": "Success.",
            "convergence": t["next_turn_narrative"]
        }
        normalized["turns"].append(normalized_turn)
    
    # Simple conclusion synthesis
    if normalized["turns"]:
        normalized["conclusion"] = f"The mission regarding '{q['title']}' is complete. {normalized['turns'][-1]['convergence']}"
    
    return normalized

# Normalize and merge
normalized_quests = [normalize_quest(q) for q in new_quests_raw]

# Check existing IDs to avoid duplicates (though these have EH_ prefix)
existing_ids = {q["id"] for q in db}
unique_new = [q for q in normalized_quests if q["id"] not in existing_ids]

db.extend(unique_new)

# Save merged DB
with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"Successfully merged {len(unique_new)} new quests into {db_path.name}")
print(f"Total quests now: {len(db)}")

import json
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'EmberHeart' / 'docs' / 'SIDE_QUESTS_DB.json'

with open(db_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

def get_difficulty(xp):
    if xp >= 2000:
        return "Grandmaster"
    if xp >= 1600:
        return "Elite"
    if xp >= 1200:
        return "Hard"
    if xp >= 800:
        return "Medium"
    return "Easy"

for q in db:
    xp = q.get("xp_reward", 0)
    # Special case: If already tagged "Grandmaster" or similar, keep it if it makes sense
    # but for standardization, we'll follow the XP logic.
    q["difficulty"] = get_difficulty(xp)

with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

# Count distributions
from collections import Counter
counts = Counter(q["difficulty"] for q in db)
print(f"Difficulty distribution: {dict(counts)}")

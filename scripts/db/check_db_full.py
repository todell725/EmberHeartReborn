import json
from pathlib import Path

p = Path(__file__).resolve().parent / 'EmberHeart' / 'docs' / 'SIDE_QUESTS_DB.json'
try:
    db = json.loads(p.read_text(encoding='utf-8'))
    print(f"Total quests: {len(db)}")
    required = ['id', 'title', 'xp_reward', 'loot_table']
    for i, q in enumerate(db):
        missing = [r for r in required if r not in q]
        if missing:
            print(f"Quest {q.get('id', i)} (Index {i}) missing: {missing}")
        elif not isinstance(q['loot_table'], list):
            print(f"Quest {q.get('id', i)} loot_table is NOT a list: {type(q['loot_table'])}")
except Exception as e:
    print(f"JSON Error: {e}")

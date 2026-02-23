import json
from pathlib import Path

p = Path(__file__).resolve().parent / 'EmberHeart' / 'docs' / 'SIDE_QUESTS_DB.json'
try:
    db = json.loads(p.read_text(encoding='utf-8'))
    print(f"Total quests: {len(db)}")
    turn_required = ['turn', 'narrative', 'choice_a', 'consequence_a', 'choice_b', 'consequence_b', 'convergence']
    for i, q in enumerate(db):
        qid = q.get('id', f'Index {i}')
        turns = q.get('turns', [])
        if not turns:
            print(f"Quest {qid} has NO turns!")
            continue
        for j, turn in enumerate(turns):
            missing = [r for r in turn_required if r not in turn]
            if missing:
                print(f"Quest {qid} Turn {j+1} missing: {missing}")
except Exception as e:
    print(f"JSON Error: {e}")

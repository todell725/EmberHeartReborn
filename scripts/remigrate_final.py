
import os
import shutil
import json
from pathlib import Path

source_dir = Path(r"z:\DnD\EmberHeartReborn\Character Pics")
target_root = Path(r"z:\DnD\EmberHeartReborn\characters")

# Manual mapping for the last 5 since they don't have direct folder name matches
final_map = {
    "Queen Elara.png": "EH-45_Elara_Moonwhisper",
    "Elder Thorne.png": "EH-47_Valerius_Thorne",
    "Rix (The Scavenger).png": "EH-52_Zael"
}

# Still unsure about Commander Vex and Grand Marshal Malakor 
# unless I find a folder for them. 

for pic_name, folder_name in final_map.items():
    src = source_dir / pic_name
    dst_dir = target_root / folder_name
    
    if src.exists() and dst_dir.exists():
        dst_file = dst_dir / pic_name
        print(f"Moving {pic_name} -> {folder_name}")
        shutil.move(src, dst_file)
        
        # Update profile.json
        p_path = dst_dir / "profile.json"
        if p_path.exists():
            data = json.loads(p_path.read_text(encoding='utf-8'))
            data['avatar_url'] = f"./{pic_name}"
            with open(p_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print("  Updated profile.json")

# List remaining
remaining = list(source_dir.iterdir())
if remaining:
    print(f"\nRemaining in Character Pics: {[p.name for p in remaining]}")

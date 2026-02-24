
import os
import shutil
import json
import re
from pathlib import Path

source_dir = Path(r"z:\DnD\EmberHeartReborn\Character Pics")
target_root = Path(r"z:\DnD\EmberHeartReborn\characters")

def normalize(name):
    # Remove extensions and special characters for a clean name match
    name = Path(name).stem
    # Remove parentheticals like (Refugee Leader) or (The Scavenger)
    name = re.sub(r'\(.*?\)', '', name).strip()
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

# Map folder names to their normalized character name
char_folders = {}
for folder in target_root.iterdir():
    if folder.is_dir():
        # Usually ID_Name, so EH-01_Marta_Hale
        parts = folder.name.split('_', 1)
        if len(parts) > 1:
            name_part = parts[1]
            char_folders[normalize(name_part)] = folder
        else:
            char_folders[normalize(folder.name)] = folder

# Manual overrides for tricky names
overrides = {
    normalize("The Chronicle Weaver"): target_root / "DM-00_The_Chronicle_Weaver",
    normalize("Silvara"): target_root / "PC-03_Silvara__Silvy",
    normalize("mareth"): target_root / "PC-04_Mareth",
    normalize("Vorenus of the Gilded Coast"): target_root / "EH-50_Vorenus_of_the_Gilded_Coast",
}
char_folders.update(overrides)

moves = []
for pic in source_dir.iterdir():
    if pic.is_file() and pic.suffix.lower() in ['.png', '.jpg', '.jpeg']:
        norm_name = normalize(pic.name)
        
        # Handle "Kaelen" variants
        if "kaelen" in norm_name:
            target_dir = target_root / "EH-46_Kaelen_Sunstrider"
        else:
            target_dir = char_folders.get(norm_name)
            
        if target_dir and target_dir.exists():
            # Use original name to prevent overwriting if multiple pics match one char
            dest = target_dir / pic.name
            moves.append((pic, dest))
        else:
            print(f"No match for: {pic.name}")

print(f"Planned moves: {len(moves)}")
for src, dst in moves:
    print(f"Moving {src.name} -> {dst.relative_to(target_root.parent)}")
    shutil.move(src, dst)
    
    # Update profile.json
    profile_path = dst.parent / "profile.json"
    if profile_path.exists():
        try:
            data = json.loads(profile_path.read_text(encoding='utf-8'))
            data['avatar_url'] = f"./{dst.name}" 
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"  Updated {profile_path.name}")
        except Exception as e:
            print(f"  Failed to update {profile_path.name}: {e}")

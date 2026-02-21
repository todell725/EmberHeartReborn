import json
import os
import shutil
import time
from pathlib import Path

from core.config import DB_DIR, ROOT_DIR

BACKUP_DIR = ROOT_DIR / "EmberHeartReborn" / "backups"

def load_json(filename: str):
    """Safely loads a JSON file from the state directory."""
    path = DB_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"State file not found: {path} (Ensure state migration has been run)")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename: str, data: dict | list):
    """Atomically saves data to a JSON file in the state directory."""
    # Ensure standard directory structure
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    path = DB_DIR / filename
    temp_path = path.with_suffix('.tmp')
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # Atomic replace
    if path.exists():
        os.replace(temp_path, path)
    else:
        os.rename(temp_path, path)

def backup_state():
    """Creates a timestamped backup of strict runtime state files."""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_folder = BACKUP_DIR / f"state_{timestamp}"
    backup_folder.mkdir()

    # The new live state manifests
    files_to_backup = [
        "SETTLEMENT_STATE.json",
        "NPC_STATE_FULL.json",
        "PARTY_STATE.json",
        "RELATIONSHIPS.json",
        "PARTY_RELATIONSHIPS.json",
        "QUEST_COMPLETION.json", 
        "LOOT_LEDGER.json",
        "FORGE_ACTIVE.json",
        "SLAYER_ACTIVE.json",
        "PARTY_EQUIPMENT.json"
    ]

    backed_up = 0
    for filename in files_to_backup:
        src = DB_DIR / filename
        if src.exists():
            shutil.copy2(src, backup_folder / filename)
            backed_up += 1
    
    print(f"✅ Backed up {backed_up} state files to {backup_folder}")
    return backup_folder

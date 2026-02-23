import json
import os
import shutil
import time
from pathlib import Path
from datetime import datetime

from core.config import DB_DIR, ROOT_DIR, CHARACTERS_DIR

BACKUP_DIR = ROOT_DIR / "backups"

def get_character_dir(char_id: str) -> Path | None:
    """Finds the character directory based on ID prefix (EH-XXX or PC-XXX)."""
    if not CHARACTERS_DIR.exists():
        return None
    for d in CHARACTERS_DIR.iterdir():
        if d.is_dir() and d.name.startswith(f"{char_id}_"):
            return d
    return None

def load_character_profile(char_id: str) -> dict:
    """Loads lore/static data for a specific character."""
    char_dir = get_character_dir(char_id)
    if not char_dir: return {}
    path = char_dir / "profile.json"
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_character_state(char_id: str) -> dict:
    """Loads runtime/dynamic state for a specific character."""
    char_dir = get_character_dir(char_id)
    if not char_dir: return {}
    path = char_dir / "state.json"
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_character_state(char_id: str, state: dict):
    """Atomically saves dynamic state for a specific character."""
    char_dir = get_character_dir(char_id)
    if not char_dir:
        # If folder doesn't exist, we might need to create it (though usually migrate handles this)
        # For now, let's just log or raise.
        raise FileNotFoundError(f"Character directory for {char_id} not found.")
    
    path = char_dir / "state.json"
    
    import uuid
    temp_path = path.with_suffix(f'.{uuid.uuid4()}.tmp')
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)
        
    max_retries = 5
    for i in range(max_retries):
        try:
            if path.exists():
                os.replace(temp_path, path)
            else:
                os.rename(temp_path, path)
            break
        except PermissionError:
            if i == max_retries - 1: raise
            time.sleep(0.5 * (i + 1))

def save_character_profile(char_id: str, profile: dict):
    """Atomically saves static profile data for a specific character."""
    char_dir = get_character_dir(char_id)
    if not char_dir:
        raise FileNotFoundError(f"Character directory for {char_id} not found.")
    
    path = char_dir / "profile.json"
    
    import uuid
    temp_path = path.with_suffix(f'.{uuid.uuid4()}.tmp')
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=4)
        
    max_retries = 5
    for i in range(max_retries):
        try:
            if path.exists():
                os.replace(temp_path, path)
            else:
                os.rename(temp_path, path)
            break
        except PermissionError:
            if i == max_retries - 1: raise
            time.sleep(0.5 * (i + 1))

def load_all_character_profiles() -> list:
    """Utility to load all character profiles from the characters/ directory."""
    profiles = []
    if not CHARACTERS_DIR.exists():
        return []
    for char_dir in CHARACTERS_DIR.iterdir():
        if not char_dir.is_dir(): continue
        profile_path = char_dir / "profile.json"
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profiles.append(json.load(f))
            except:
                pass
    return profiles

def resolve_character(query: str) -> dict | None:
    """Finds a character (NPC or PC) by ID, Name, or Partial Name match."""
    query = query.lower()
    all_chars = load_all_character_profiles()
    
    # 1. Exact match (ID or Name)
    match = next((c for c in all_chars if query == c.get('id', '').lower() or query == c.get('name', '').lower()), None)
    if match: return match
    
    # 2. Partial name match
    match = next((c for c in all_chars if query in c.get('name', '').lower()), None)
    return match

def load_all_character_states() -> list:
    """Utility to load all character profiles + states merged from the characters/ directory."""
    entities = []
    if not CHARACTERS_DIR.exists():
        return []
    for char_dir in CHARACTERS_DIR.iterdir():
        if not char_dir.is_dir(): continue
        profile_path = char_dir / "profile.json"
        state_path = char_dir / "state.json"
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if state_path.exists():
                    with open(state_path, 'r', encoding='utf-8') as f:
                        data.update(json.load(f))
                entities.append(data)
            except Exception:
                pass
    return entities

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
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # On network shares, sometimes mkdir fails despite folder existing or permissions being wonky
        if not DB_DIR.exists():
            print(f"⚠️ Warning: Failed to create DB_DIR {DB_DIR}: {e}")
    
    path = DB_DIR / filename
    # Use UUID in temp file to ensure thread-safety during concurrent writes
    import uuid
    temp_path = path.with_suffix(f'.{uuid.uuid4()}.tmp')
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # Atomic replace with retry for Windows file locking
    max_retries = 5
    retry_delay = 0.2  # seconds
    
    for i in range(max_retries):
        try:
            if path.exists():
                os.replace(temp_path, path)
            else:
                os.rename(temp_path, path)
            break
        except PermissionError as e:
            if i == max_retries - 1:
                print(f"❌ Final attempt failed to save {filename}: {e}")
                raise
            time.sleep(retry_delay)
            # exponential backoff
            retry_delay *= 2

def load_conversations() -> dict:
    """Loads all active conversation histories with corruption protection."""
    path = DB_DIR / "CONVERSATIONS.json"
    if not path.exists():
        return {}
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ Corruption detected in CONVERSATIONS.json: {e}")
        backup_path = path.with_suffix('.corrupt.bak')
        try:
            os.replace(path, backup_path)
            print(f"🔄 Corrupted file moved to {backup_path}. Starting fresh.")
        except Exception as e2:
            print(f"❌ Failed to move corrupted file: {e2}")
        return {}

def save_conversations(data: dict):
    """Saves conversation histories."""
    save_json("CONVERSATIONS.json", data)

def backup_state():
    """Creates a timestamped backup of strict runtime state files."""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_folder = BACKUP_DIR / f"state_{timestamp}"
    backup_folder.mkdir()

    # Back up the characters directory
    if CHARACTERS_DIR.exists():
        shutil.copytree(CHARACTERS_DIR, backup_folder / "characters")

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
        "PARTY_EQUIPMENT.json",
        "CONVERSATIONS.json"
    ]

    backed_up = 0
    for filename in files_to_backup:
        src = DB_DIR / filename
        if src.exists():
            shutil.copy2(src, backup_folder / filename)
            backed_up += 1
    
    print(f"✅ Backed up {backed_up} state files and character directory to {backup_folder}")
    return backup_folder

def log_narrative_event(event_text: str):
    """Appends a concise narrative event to the global NARRATIVE_LOG.md with pruning."""
    log_path = DB_DIR / "NARRATIVE_LOG.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = f"- [{timestamp}] {event_text}\n"
    
    lines = []
    if log_path.exists():
        lines = log_path.read_text(encoding='utf-8').splitlines(keepends=True)
    
    # Prune to last 50 events
    if len(lines) >= 50:
        lines = lines[-49:]
        
    lines.append(new_entry)
    
    # Atomic write with retry
    import uuid
    temp_path = log_path.with_suffix(f'.{uuid.uuid4()}.tmp')
    temp_path.write_text("".join(lines), encoding='utf-8')
    
    max_retries = 5
    for i in range(max_retries):
        try:
            if log_path.exists():
                os.replace(temp_path, log_path)
            else:
                os.rename(temp_path, log_path)
            break
        except PermissionError:
            if i == max_retries - 1:
                print(f"FAILED to save Narrative Log: Access Denied")
                raise
            time.sleep(0.5 * (i + 1))
        except Exception as e:
            print(f"Error saving Narrative Log: {e}")
            break

import json
import re
from pathlib import Path

# Paths
ROOT = Path(r"z:\DnD\EmberHeartReborn")
NPC_MONOLITH = ROOT / "state" / "NPC_STATE_FULL.json"
PARTY_MONOLITH = ROOT / "state" / "PARTY_STATE.json"
CHARACTERS_DIR = ROOT / "characters"

# Define field splits (Lore = Static/Authored, State = Dynamic/Runtime)
LORE_FIELDS = {
    "id", "name", "race", "role", "avatar_url", "description", "bio", 
    "motivation", "secret", "faction", "appearance", "council_role", 
    "discord_webhook_id", "alignment", "background", "gender", "class", "subclass"
}

STATE_FIELDS = {
    "influence", "loyalty", "fear", "corruption_exposure", 
    "cult_allegiance", "latent_symptom_flag", "hp_current", "hp_max", "active_quests",
    "level", "experience_points", "combat_profile", "inventory", "status_effects", 
    "last_seen", "relationship_flags", "xp_thresholds", "currency"
}

def sanitize_name(name):
    """Sanitize name for folder use."""
    return re.sub(r'[^A-Za-z0-9]', '_', name).strip('_')

def migrate_source(file_path, key):
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    entities = data.get(key, [])
    print(f"Migrating {len(entities)} from {file_path.name}...")

    for entity in entities:
        if not isinstance(entity, dict): continue
        
        char_id = entity.get("id")
        char_name = entity.get("name", "Unknown")
        if not char_id:
            print(f"Skipping entity with no ID: {char_name}")
            continue

        # Foldering: characters/ID_Name
        folder_name = f"{char_id}_{sanitize_name(char_name)}"
        char_dir = CHARACTERS_DIR / folder_name
        char_dir.mkdir(exist_ok=True, parents=True)

        profile = {}
        state = {}

        for k, v in entity.items():
            if k in LORE_FIELDS:
                profile[k] = v
            elif k in STATE_FIELDS:
                state[k] = v
            else:
                # If unknown field, default to profile (lore) unless it looks like a number/state
                if isinstance(v, (int, float, bool, list, dict)) and k not in ["bio", "appearance"]:
                    state[k] = v
                else:
                    profile[k] = v

        # Write files
        with open(char_dir / "profile.json", "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        with open(char_dir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print(f"  OK: Migrated {char_id}: {char_name}")

def migrate():
    CHARACTERS_DIR.mkdir(exist_ok=True)
    migrate_source(NPC_MONOLITH, "npcs")
    migrate_source(PARTY_MONOLITH, "party")
    print("\nMigration complete. Run compile_npcs.py to verify.")

if __name__ == "__main__":
    migrate()

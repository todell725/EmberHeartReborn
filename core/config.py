import json
import logging
from pathlib import Path

logger = logging.getLogger("EH_Core")

# Standardized Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = ROOT_DIR / "EmberHeartReborn" / "state"

# D&D 5E XP Thresholds
XP_THRESHOLDS = {
    1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500, 6: 14000, 7: 23000, 8: 34000, 
    9: 48000, 10: 64000, 11: 85000, 12: 100000, 13: 120000, 14: 140000, 
    15: 165000, 16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
}

# Identity Registry Base
IDENTITIES = {
    "DM": {"name": "The Chronicle Weaver", "avatar": "https://cdn.discordapp.com/attachments/1473540819146244218/1473803413988049192/image0.jpg?ex=699789e3&is=69963863&hm=ddcf70043b632ef81457595c1fa2b979128639e6c2aa284a7f882918d134c7d9&"},
    "STEWARD": {"name": "Royal Steward", "avatar": "https://i.imgur.com/4zYf4zD.png"},
    "SHADOW": {"name": "Your Shadow", "avatar": "https://i.imgur.com/u7yH8zW.png"},
    "NPC": {"name": "NPC", "avatar": "https://i.imgur.com/pYIe6oM.png"}
}

def load_npc_identities():
    """Populates IDENTITIES with data from NPC_STATE_FULL.json."""
    npc_file = DB_DIR / "NPC_STATE_FULL.json"
    if not npc_file.exists():
        logger.warning(f"NPC State file not found: {npc_file}")
        return

    try:
        with open(npc_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for npc in data.get("npcs", []):
                # Map by ID and by Name for easy lookup
                entry = {"name": npc["name"], "avatar": npc.get("avatar_url")}
                IDENTITIES[npc["id"]] = entry
                IDENTITIES[npc["name"]] = entry
    except Exception as e:
        logger.error(f"Failed to load NPC identities: {e}")

# Populate on initial import
load_npc_identities()

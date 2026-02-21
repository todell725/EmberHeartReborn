import logging
import json
from core.config import XP_THRESHOLDS, ROOT_DIR, DB_DIR

logger = logging.getLogger("EH_Combat")

class CombatTracker:
    def __init__(self):
        self.order = [] # List of {"name": str, "init": int, "hp": int}
        self.current_index = 0
        self.active = False
        self.party_path = DB_DIR / "PARTY_STATE.json"

    def add_combatant(self, name, roll, hp):
        self.order.append({"name": name, "init": roll, "hp": hp})
        self.order.sort(key=lambda x: x['init'], reverse=True)

    def next_turn(self):
        if not self.order: return None
        self.current_index = (self.current_index + 1) % len(self.order)
        return self.order[self.current_index]

    def clear(self):
        self.order = []
        self.current_index = 0
        self.active = False

    def add_party_xp(self, xp: int) -> list[tuple]:
        """
        Award XP to the entire party (negative XP = penalty). 
        Returns list of (name, new_level).
        Extracted here because Combat/Slays often tie directly to XP.
        """
        if not self.party_path.exists():
            logger.warning(f"XP Sync failed: {self.party_path} not found.")
            return []
            
        leveled_up = []
        try:
            data = json.loads(self.party_path.read_text(encoding='utf-8'))
            for char in data.get("party", []):
                old_xp = char.get("experience_points", 0)
                new_xp = max(0, old_xp + xp)
                char["experience_points"] = new_xp
                current_level = char.get("level", 1)
                new_level = current_level
                
                for lvl, thresh in sorted(XP_THRESHOLDS.items()):
                    if new_xp >= thresh:
                        new_level = lvl
                        
                if new_level > current_level:
                    char["level"] = new_level
                    leveled_up.append((char['name'], new_level))
                    logger.info(f"✨ [LEVEL UP] {char['name']} -> Level {new_level}")
                    
            self.party_path.write_text(json.dumps(data, indent=4), encoding='utf-8')
            return leveled_up
            
        except Exception as e:
            logger.error(f"XP sync failed: {e}", exc_info=True)
            return []

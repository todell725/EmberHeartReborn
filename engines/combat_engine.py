import logging
import json
from core.config import XP_THRESHOLDS, ROOT_DIR, DB_DIR

logger = logging.getLogger("EH_Combat")

class CombatTracker:
    def __init__(self):
        self.order = [] # List of {"name": str, "init": int, "hp": int}
        self.current_index = 0
        self.active = False

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

    def add_party_xp(self, xp: int, target_ids: list = None) -> list[tuple]:
        """
        Award XP to the party. If target_ids is provided, only those IDs get XP.
        Returns list of (name, new_level).
        """
        leveled_up = []
        try:
            from core.storage import load_all_character_states, save_character_state
            all_states = load_all_character_states()
            
            # Party = Characters with PC- prefix in ID
            party = [s for s in all_states if s.get("id", "").startswith("PC-")]
            
            if target_ids:
                party = [s for s in party if s.get("id") in target_ids]
            
            if not party:
                logger.warning(f"XP Sync failed: No matching party members {target_ids if target_ids else '(PC-*)'} found.")
                return []
                
            for char_state in party:
                char_id = char_state.get("id")
                old_xp = char_state.get("experience_points", 0)
                new_xp = max(0, old_xp + xp)
                char_state["experience_points"] = new_xp
                
                current_level = char_state.get("level", 1)
                new_level = current_level
                
                for lvl, thresh in sorted(XP_THRESHOLDS.items()):
                    if new_xp >= thresh:
                        new_level = lvl
                        
                if new_level > current_level:
                    char_state["level"] = new_level
                    leveled_up.append((char_state['name'], new_level))
                    logger.info(f"✨ [LEVEL UP] {char_state['name']} -> Level {new_level}")
                
                # Save individual character state
                # Note: char_state here is a merged dict if it came from load_all_character_states
                # We should be careful to only save state keys if we use load_all_character_states
                # or better, load the literal state file before saving.
                from core.storage import load_character_state
                actual_state = load_character_state(char_id)
                actual_state["experience_points"] = new_xp
                actual_state["level"] = new_level
                save_character_state(char_id, actual_state)
                    
            return leveled_up
            
        except Exception as e:
            logger.error(f"XP sync failed: {e}", exc_info=True)
            return []

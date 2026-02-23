import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from core.config import ROOT_DIR, DB_DIR
from engines.combat_engine import CombatTracker

logger = logging.getLogger("EH_QuestEngine")

class QuestEngine:
    def __init__(self):
        self.db_path = ROOT_DIR / "docs" / "SIDE_QUESTS_DB.json"
        self.completion_path = DB_DIR / "QUEST_COMPLETION.json"
        self.loot_path = DB_DIR / "PARTY_EQUIPMENT.json" # Shared bulk storage
        self.deeds_path = DB_DIR / "QUEST_DEEDS.md"
        self.sessions: Dict[int, dict] = {} # channel_id -> session state
        self.completed = self._load_completed()
        self.combat = CombatTracker() # Used for XP integration
        logger.info(f"QuestEngine initialised. {len(self.completed)} quests completed.")

    def _load_completed(self) -> set:
        if self.completion_path.exists():
            try:
                data = json.loads(self.completion_path.read_text(encoding='utf-8'))
                return set(data)
            except Exception as e:
                logger.error(f"Failed to load completed quests: {e}")
                return set()
        return set()

    def get_quest(self, qid: str) -> Optional[dict]:
        if not self.db_path.exists(): return None
        try:
            db_data = json.loads(self.db_path.read_text(encoding='utf-8'))
            # Support both flat array and the compiled metadata dict
            quests = db_data if isinstance(db_data, list) else db_data.get("quests", [])
            for q in quests:
                if q.get('id', '').upper() == qid.upper():
                    return q
        except Exception as e:
            logger.error(f"Failed reading quest DB: {e}")
        return None

    def check_prerequisites(self, qid: str) -> tuple:
        """Returns (ok: bool, missing: list). missing is [] when ok."""
        quest = self.get_quest(qid)
        if not quest:
            return False, [f"{qid} not found"]
            
        prereqs = quest.get('prerequisites', {})
        if not isinstance(prereqs, dict):
            return True, [] 
            
        required_quests = prereqs.get('quests_completed', [])
        missing = [q for q in required_quests if q.upper() not in self.completed]
        return (len(missing) == 0), missing

    def resolve_outcome(self, qid: str, path: list) -> Optional[str]:
        """Map the A/B choice path to a branching_outcome key."""
        quest = self.get_quest(qid)
        if not quest:
            return None
            
        bo = quest.get('branching_outcomes', {})
        if isinstance(bo, dict):
            outcomes = list(bo.keys())
        elif isinstance(bo, list):
            outcomes = [item.get('path', str(i)) for i, item in enumerate(bo)]
        else:
            return None
            
        if not outcomes:
            return None
        if not path:
            return outcomes[0]
            
        b_ratio = path.count('b') / len(path)
        idx = min(int(b_ratio * len(outcomes)), len(outcomes) - 1)
        return outcomes[idx]

    def apply_failure(self, qid: str) -> str:
        """Apply risk_matrix failure penalties. Returns critical_failure text."""
        quest = self.get_quest(qid)
        if not quest:
            return "Quest failed."
            
        rm = quest.get('risk_matrix', {})
        penalty = rm.get('failure_penalty', {})
        xp_loss = penalty.get('xp_loss', 0)
        
        if xp_loss > 0:
            self.combat.add_party_xp(-xp_loss)
            logger.info(f"[RISK] Applied -{xp_loss} XP penalty for {qid}")
            
        cf_text = rm.get('critical_failure', 'The quest failed with consequences.')
        self.log_deed(qid, quest.get('title', qid), f"[FAILED] {cf_text}")
        return cf_text

    def mark_completed(self, qid: str, path: list = None) -> List[tuple]:
        """Mark quest finished. Awards XP, loot, logs outcome + permanent effects."""
        leveled_up = []
        try:
            self.completed.add(qid.upper())
            items = sorted([str(x) for x in self.completed if isinstance(x, str)])
            self.completion_path.write_text(json.dumps(items, indent=4), encoding='utf-8')

            quest = self.get_quest(qid)
            if not quest:
                return leveled_up

            outcome_key = self.resolve_outcome(qid, path or [])
            outcome_data = {}
            if outcome_key:
                outcome_data = quest.get('branching_outcomes', {}).get(outcome_key, {})

            # 1. XP
            xp = quest.get('xp_reward', 0)
            if xp > 0:
                leveled_up = self.combat.add_party_xp(xp)

            # 2. Loot
            loot = list(quest.get('loot_table', []))
            item_reward = outcome_data.get('consequences', {}).get('item_reward')
            if item_reward and item_reward not in loot:
                loot.append(item_reward)
            self.sync_loot(loot)

            # 3. Conclusion & Effects Logging
            conclusion = outcome_data.get('description') or quest.get('conclusion') or 'The quest has concluded.'
            self.log_deed(qid, quest.get('title', qid), conclusion)

            all_effects = list(quest.get('permanent_world_effects_universal', []))
            all_effects += list(quest.get('permanent_effects', []))
            all_effects += outcome_data.get('permanent_world_effects', [])
            seen = set()
            for effect in all_effects:
                if effect and effect not in seen:
                    self.log_deed(qid, quest.get('title', qid), f"[WORLD] {effect}")
                    seen.add(effect)

            return leveled_up
            
        except Exception as e:
            logger.error(f"CRITICAL [mark_completed]: {e}", exc_info=True)
            return []

    def sync_loot(self, loot_list: list):
        if not loot_list: return
        
        settlement_path = DB_DIR / "SETTLEMENT_STATE.json"
        
        MUNDANE_KEYS = ["bone", "pelt", "hide", "scrap", "claw", "dust", "fang", "horn",
                        "gland", "shell", "chunk", "fragment", "nucleus", "membrane"]
        try:
            from core.storage import load_character_state, save_character_state, load_all_character_states
            equip_data = json.loads(self.loot_path.read_text(encoding='utf-8')) if self.loot_path.exists() else {"party_inventory": []}
            settlement_data = json.loads(settlement_path.read_text(encoding='utf-8'))
            
            # Need a backup list of PC names/IDs for auto-assign
            all_states = load_all_character_states()
            pcs = [s for s in all_states if s.get("id", "").startswith("PC-")]

            for item in loot_list:
                item_lower = item.lower()
                
                # Auto-Assign
                if "Gold" in item_lower or "OU" in item:
                    try:
                        amt = int(''.join(filter(str.isdigit, item)))
                        stock = settlement_data['settlement']['stockpiles']
                        if "gold" in stock:
                            stock["gold"] += amt
                        else:
                            stock["ore_stock_ou"] = stock.get("ore_stock_ou", 0) + amt
                        logger.info(f"[LOOT] +{amt} Gold/OU -> Settlement Treasury")
                    except Exception as e:
                        logger.error(f"Failed to parse OU from item '{item}': {e}")
                elif any(m in item_lower for m in MUNDANE_KEYS):
                    equip_data.setdefault("party_inventory", []).append(item)
                    logger.info(f"[LOOT] '{item}' -> Party Storage")
                else:
                    # Assign to Kaelrath (PC-01) by default, or the first PC
                    target_id = "PC-01" 
                    target_state = next((s for s in pcs if s['id'] == target_id), None)
                    if not target_state and pcs:
                        target_state = pcs[0]
                        target_id = target_state['id']
                    
                    if target_state:
                        target_state.setdefault('status', {}).setdefault('inventory', []).append(item)
                        save_character_state(target_id, target_state)
                        logger.info(f"[LOOT] '{item}' -> {target_state.get('name', 'Unknown')}'s Inventory")
                        
            # Save shared files
            self.loot_path.write_text(json.dumps(equip_data, indent=4), encoding='utf-8')
            settlement_path.write_text(json.dumps(settlement_data, indent=4), encoding='utf-8')
            
        except Exception as e:
            logger.error(f"Loot Sync failed: {e}", exc_info=True)

    def log_deed(self, qid: str, title: str, outcome: str):
        if not self.deeds_path.exists():
            self.deeds_path.parent.mkdir(parents=True, exist_ok=True)
            self.deeds_path.write_text("# 📜 The Chronicle of Deeds\n\n", encoding='utf-8')
        try:
            with open(self.deeds_path, "a", encoding="utf-8") as f:
                f.write(f"### {qid}: {title}\n> {outcome}\n\n")
        except Exception as e:
            logger.error(f"Failed to log deed: {e}")

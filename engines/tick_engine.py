import json
import logging
import random
from pathlib import Path
from core.config import ROOT_DIR, DB_DIR

logger = logging.getLogger("EH_Tick")

class TickEngine:
    def __init__(self):
        self.settlement_path = DB_DIR / "SETTLEMENT_STATE.json"
        self.npc_path = DB_DIR / "NPC_STATE_FULL.json"
        self.party_path = DB_DIR / "PARTY_STATE.json"
        self.relationship_path = DB_DIR / "RELATIONSHIPS.json"
        self.deeds_path = DB_DIR / "QUEST_DEEDS.md"

    def run_tick(self) -> str:
        """Executes the weekly logic. Returns a dictionary of changes for the Proclamation."""
        try:
            from core.storage import load_all_character_states, save_character_state, save_json
            settlement = json.loads(self.settlement_path.read_text(encoding='utf-8'))
            all_characters = load_all_character_states()
            
            summary = []
            
            # --- 1. Resource Balance ---
            stock = settlement['settlement']['stockpiles']
            calendar = settlement['settlement']['calendar']
            core = settlement['settlement']['core_status']
            
            food_status = "✨ Abundant (Infinite)" if stock.get('food_stock_fu') == "INFINITE" else f"📦 {stock.get('food_stock_fu', 0)} FU"
            summary.append(f"🍞 **Food Supply**: {food_status}")

            # --- 2. Cult Spread ---
            corruption_index = core.get('corruption_index', 0)
            exposed = []
            for char_data in all_characters:
                # NPCs only for cult spread usually, but we check allegiance
                if char_data.get('cult_allegiance', 0) > 0: continue
                
                chance = corruption_index * 2
                if random.randint(1, 100) <= chance:
                    # Update exposure
                    new_exposure = char_data.get('corruption_exposure', 0) + random.randint(10, 20)
                    
                    # Atomic save for this character
                    # We only save the fields that belong in state.json
                    from scripts.migrate_npcs import STATE_FIELDS
                    char_state = {k: v for k, v in char_data.items() if k in STATE_FIELDS or k == 'corruption_exposure'}
                    char_state['corruption_exposure'] = new_exposure
                    
                    try:
                        save_character_state(char_data['id'], char_state)
                        exposed.append(char_data.get('name', 'Unknown citizen'))
                    except Exception as e:
                        logger.error(f"Failed to save state for {char_data.get('id')}: {e}")
            
            if exposed:
                summary.append(f"👁️ **Cult Activity**: Dark rumors surround {len(exposed)} individuals.")
            else:
                summary.append(f"✅ **Security**: The Sovereignty remains pure.")

            # --- 3. Relationship Drift ---
            if self.relationship_path.exists():
                try:
                    rels = json.loads(self.relationship_path.read_text(encoding='utf-8'))
                    for rel in rels.get('relationships', []):
                        if rel.get('tension', 0) > 10:
                            rel['tension'] -= 1 
                    save_json("RELATIONSHIPS.json", rels)
                except Exception as e:
                    logger.warning(f"Could not drift relationships: {e}")

            # --- 4. Calendar & Income ---
            income = core.get('weekly_income_gold', 0)
            if income > 0:
                if "gold" in stock:
                    stock["gold"] += income
                else:
                    core["gold"] = core.get("gold", 0) + income
            
            summary.append(f"💰 **Treasury**: +{income:,} Gold deposited to the Royal Vault.")

            # Advance Week
            if 'week_index' in calendar:
                 calendar['week_index'] += 1
                 summary.append(f"📅 **Calendar**: It is now Week {calendar['week_index']} of the {calendar.get('season', 'Unknown Season')}.")

            # Save Settlement
            save_json("SETTLEMENT_STATE.json", settlement)
            
            return "\n".join([f"> {s}" for s in summary])
        except Exception as e:
            logger.error(f"Tick Failed: {e}", exc_info=True)
            return f"❌ **Tick Failure**: {e}"

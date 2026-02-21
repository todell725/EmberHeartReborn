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
            settlement = json.loads(self.settlement_path.read_text(encoding='utf-8'))
            npcs_data = json.loads(self.npc_path.read_text(encoding='utf-8'))
            
            summary = []
            
            # --- 1. Resource Balance (Adapt for Infinite) ---
            stock = settlement['settlement']['stockpiles']
            calendar = settlement['settlement']['calendar']
            core = settlement['settlement']['core_status']
            
            # We don't deduct food if it's INFINITE
            food_status = "✨ Abundant (Infinite)" if stock.get('food_stock_fu') == "INFINITE" else f"📦 {stock.get('food_stock_fu', 0)} FU"
            summary.append(f"🍞 **Food Supply**: {food_status}")

            # --- 2. Cult Spread ---
            corruption_index = core.get('corruption_index', 0)
            exposed = []
            for npc in npcs_data.get('npcs', []):
                if npc.get('cult_allegiance', 0) > 0: continue
                
                chance = corruption_index * 2
                if random.randint(1, 100) <= chance:
                    npc['corruption_exposure'] = npc.get('corruption_exposure', 0) + random.randint(10, 20)
                    exposed.append(npc.get('name', 'Unknown citizen'))
            
            if exposed:
                summary.append(f"👁️ **Cult Activity**: Dark rumors surround {len(exposed)} individuals.")
            else:
                summary.append(f"✅ **Security**: The Sovereignty remains pure.")

            # --- 3. Relationship Drift ---
            if self.relationship_path.exists():
                try:
                    rels = json.loads(self.relationship_path.read_text(encoding='utf-8'))
                    # Simplified drift for automation
                    for rel in rels.get('relationships', []):
                        if rel.get('tension', 0) > 10:
                            rel['tension'] -= 1 # Natural resolution over time
                    self.relationship_path.write_text(json.dumps(rels, indent=4), encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Could not drift relationships: {e}")

            # --- 4. Calendar & Income ---
            # Add income to Kingdom Treasury
            income = core.get('weekly_income_gold', 0)
            if income > 0:
                # Add to stockpiles if it exists, otherwise core_status
                if "gold" in stock:
                    stock["gold"] += income
                else:
                    core["gold"] = core.get("gold", 0) + income
                logger.info(f"[SOVEREIGN TICK] Banked {income} Weekly Gold in Kingdom Treasury.")
            
            summary.append(f"💰 **Treasury**: +{income:,} Gold deposited to the Royal Vault.")

            # Advance Week
            if 'week_index' in calendar:
                 calendar['week_index'] += 1
                 summary.append(f"📅 **Calendar**: It is now Week {calendar['week_index']} of the {calendar.get('season', 'Unknown Season')}.")

            # Save
            self.settlement_path.write_text(json.dumps(settlement, indent=4), encoding='utf-8')
            self.npc_path.write_text(json.dumps(npcs_data, indent=4), encoding='utf-8')
            
            return "\n".join([f"> {s}" for s in summary])
        except Exception as e:
            logger.error(f"Tick Failed: {e}", exc_info=True)
            return f"❌ **Tick Failure**: {e}"

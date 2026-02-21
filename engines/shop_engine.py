import json
import logging
import random
import difflib
from datetime import datetime
from core.config import ROOT_DIR, DB_DIR

logger = logging.getLogger("EH_Shop")

class DynamicShop:
    def __init__(self):
        # We read from static for blueprints, write to live state for stock
        self.forge_path = ROOT_DIR / "EmberHeartReborn" / "docs" / "FORGE_CATALOG.json" # Static
        self.spells_path = ROOT_DIR / "EmberHeartReborn" / "docs" / "DND_REFERENCE_INDEX.json" # Static
        self.settlement_path = DB_DIR / "SETTLEMENT_STATE.json" # Live State
        self.party_path = DB_DIR / "PARTY_STATE.json" # Live State
        self.last_rotation = None
        self.current_stock = []
        
    def load_data(self):
        """Load static catalog data."""
        forge_items = []
        if self.forge_path.exists():
            try:
                data = json.loads(self.forge_path.read_text(encoding='utf-8'))
                forge_items = data.get("blueprints", [])
            except Exception as e:
                logger.error(f"Failed to load Forge Catalog: {e}")

        spells = []
        if self.spells_path.exists():
            try:
                data = json.loads(self.spells_path.read_text(encoding='utf-8'))
                spells = list(data.values())
            except Exception as e:
                logger.error(f"Failed to load Spell Index: {e}")
                
        return forge_items, spells

    def generate_stock(self):
        """Generate a random 30-item stock (15 Forge, 15 Spells)."""
        forge_items, spells = self.load_data()
        stock = []
        
        # 1. Forge Items (15 random)
        if forge_items:
            valid_forge = [i for i in forge_items if isinstance(i, dict) and 'name' in i]
            count = min(len(valid_forge), 15)
            selected_forge = random.sample(valid_forge, count)
            for item in selected_forge:
                stock.append({
                    "name": item['name'],
                    "type": item.get('type', 'Item'),
                    "cost": f"{item.get('cost', {}).get('ore_ou', '?')} OU",
                    "rarity": "Forge-Pattern",
                    "desc": item.get('description', 'No data.')[:100]
                })

        # 2. Spells (15 random)
        if spells:
            import re
            valid_spells = [s for s in spells if isinstance(s, dict) and 'title' in s]
            count = min(len(valid_spells), 15)
            selected_spells = random.sample(valid_spells, count)
            for spell in selected_spells:
                clean_title = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', spell['title'])
                stock.append({
                    "name": f"Scroll of {clean_title}",
                    "type": "Scroll",
                    "cost": "500 OU", 
                    "rarity": "Common", 
                    "desc": re.sub(r'[\[\]]', '', spell.get('category', 'Spell'))
                })
                
        random.shuffle(stock)
        self.current_stock = stock[:30]
        self.last_rotation = datetime.now()
        logger.info(f"Shop Stock Generated: {len(self.current_stock)} items.")

    def purchase_item(self, buyer_id: str, item_query: str) -> tuple[bool, str]:
        """Buy an item from the current stock."""
        if not self.current_stock:
            return False, "The shop shelves are bare..."

        stock_names = [i['name'] for i in self.current_stock]
        matches = difflib.get_close_matches(item_query, stock_names, n=1, cutoff=0.4)
        
        if not matches:
             return False, f"Item not found in current rotation. Did you mean: {', '.join(difflib.get_close_matches(item_query, stock_names, n=3, cutoff=0.3))}?"
        
        target_name = matches[0]
        target_item = next((i for i in self.current_stock if i['name'] == target_name), None)
        
        try:
            cost_val = int(target_item['cost'].split()[0])
        except:
            return False, "Price is invalid or not listed."

        try:
            settlement = json.loads(self.settlement_path.read_text(encoding='utf-8'))
            current_ou = settlement['settlement']['stockpiles'].get('ore_stock_ou', 0)
            
            if current_ou < cost_val:
                 return False, f"Treasury insufficient. Need **{cost_val} OU**, but only **{current_ou} OU** available."
            
            settlement['settlement']['stockpiles']['ore_stock_ou'] -= cost_val
            self.settlement_path.write_text(json.dumps(settlement, indent=4), encoding='utf-8')
            
        except Exception as e:
            logger.error(f"Transaction Failed (Settlement): {e}")
            return False, "Bank error processing funds."

        try:
            party_data = json.loads(self.party_path.read_text(encoding='utf-8'))
            buyer = next((p for p in party_data['party'] if p['id'] == buyer_id), None)
            
            if not buyer:
                return False, "Buyer profile not found."
                
            buyer.setdefault('status', {}).setdefault('inventory', []).append(target_name)
            self.party_path.write_text(json.dumps(party_data, indent=4), encoding='utf-8')
            
            return True, f"**Transaction Complete:** Purchased **{target_name}** for **{cost_val} OU**. (Treasury: {settlement['settlement']['stockpiles']['ore_stock_ou']} OU)"
            
        except Exception as e:
            logger.error(f"Transaction Failed (Party): {e}")
            return False, "Inventory update failed."

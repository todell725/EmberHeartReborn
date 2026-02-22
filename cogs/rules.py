import discord
from discord.ext import commands
import logging
import json
import re
import difflib
from collections import Counter
from core.config import ROOT_DIR, DB_DIR
from core.routing import require_channel
from core.transport import TransportAPI

logger = logging.getLogger("Cog_Rules")
DND_INDEX_PATH = ROOT_DIR / "EmberHeartReborn" / "docs" / "DND_REFERENCE_INDEX.json"

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from core.transport import transport
        self.transport = transport

    @commands.command()
    @require_channel("resources")
    async def rule(self, ctx, *, query: str):
        """AI-powered 5e rules/spell reference. Searches local D&D index first."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        normalized_query = re.sub(r'[^a-zA-Z0-9\s]', '', query.lower()).strip()
        
        # Check local index first
        if DND_INDEX_PATH.exists():
            index = json.loads(DND_INDEX_PATH.read_text(encoding='utf-8'))
            
            if normalized_query in index:
                entry = index[normalized_query]
                ref_filename = entry['path'].split('/')[-1] if '/' in entry['path'] else entry['path']
                file_path = ROOT_DIR / "EmberHeartReborn" / "docs" / ref_filename
                if not file_path.exists():
                    file_path = ROOT_DIR / "EmberHeart" / entry['path'] # Fallback
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    await self.transport.send(channel, f"📚 **Reference Found: {entry['title']}**\n{content}", "DM")
                    return
            
            matches = [k for k in index.keys() if normalized_query in k]
            if not matches:
                matches = difflib.get_close_matches(normalized_query, index.keys(), n=5, cutoff=0.6)

            if matches:
                if len(matches) == 1:
                    entry = index[matches[0]]
                    ref_filename = entry['path'].split('/')[-1] if '/' in entry['path'] else entry['path']
                    file_path = ROOT_DIR / "EmberHeartReborn" / "docs" / ref_filename
                    if not file_path.exists():
                        file_path = ROOT_DIR / "EmberHeart" / entry['path']
                    if file_path.exists():
                        content = file_path.read_text(encoding='utf-8')
                        await self.transport.send(channel, f"📚 **Reference Found ({matches[0]}): {entry['title']}**\n{content}", "DM")
                        return
                else:
                    suggestions = ", ".join([f"`{index[m]['title']}`" for m in matches])
                    await self.transport.send(channel, f"🔍 **Multiple matches found for '{query}':**\n{suggestions}\n\n*Try being more specific!*")
                    return

        # Let user know AI fallback isn't fully handled here directly as AI owns chat.
        # But we could trigger bot.cogs['BrainCog'].chat if we wanted to.
        await self.transport.send(channel, "🔍 Concept not found in static rules. Ask the DM AI directly in the main channel.", "DM")

    @commands.command()
    @require_channel("royal-treasury")
    async def loot(self, ctx, action: str = "list", *, item: str = None):
        """Party & Kingdom Inventory Management: !loot add/remove/list."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        settlement_path = DB_DIR / "SETTLEMENT_STATE.json"
        equip_path = DB_DIR / "PARTY_EQUIPMENT.json"
        
        from core.storage import load_all_character_states, load_character_state, save_character_state, resolve_character
        
        if action == "list":
            msg_parts = ["**🏹 Current World Hoard**"]
            
            try:
                all_states = load_all_character_states()
                party = [s for s in all_states if s.get("id", "").startswith("PC-")]
                
                if party:
                    msg_parts.append("\n**-- Core Inventory --**")
                    for p in party:
                        inv = p.get("status", {}).get("inventory", [])
                        if inv:
                            counts = Counter(inv)
                            inv_str = ", ".join([f"`{i} x{c}`" if c > 1 else f"`{i}`" for i, c in counts.items()])
                        else:
                            inv_str = "*Empty*"
                        msg_parts.append(f"**{p.get('name', 'Unknown')}**: {inv_str}")
            except Exception as e:
                logger.error(f"Loot Party Error: {e}")

            try:
                if equip_path.exists():
                    data = json.loads(equip_path.read_text(encoding='utf-8'))
                    equip_data = data.get("party_equipment", {})
                    # Also handle flat list if PARTY_EQUIPMENT is just an inventory list
                    p_inv = data.get("party_inventory", [])
                    
                    msg_parts.append("\n**-- Equipment & Quest Loot --**")
                    if p_inv:
                         counts = Counter(p_inv)
                         inv_str = ", ".join([f"`{i} x{c}`" if c > 1 else f"`{i}`" for i, c in counts.items()])
                         msg_parts.append(f"**Shared Storage**: {inv_str}")
                         
                    for name, details in equip_data.items():
                        inv = details.get("inventory", [])
                        if inv:
                            counts = Counter(inv)
                            inv_str = ", ".join([f"`{i} x{c}`" if c > 1 else f"`{i}`" for i, c in counts.items()])
                        else:
                            inv_str = "*None*"
                        msg_parts.append(f"**{name}**: {inv_str}")
            except Exception as e:
                logger.error(f"Loot Equip Error: {e}")

            try:
                if settlement_path.exists():
                    data = json.loads(settlement_path.read_text(encoding='utf-8'))
                    settlement_inv = data.get("settlement", {}).get("inventory", [])
                    if settlement_inv:
                        msg_parts.append("\n**-- Kingdom Hoard --**")
                        counts = Counter([i for i in settlement_inv if not isinstance(i, str) or not i.startswith("SEE:")])
                        for i_name, count in counts.items():
                            qty_str = f" x{count}" if count > 1 else ""
                            msg_parts.append(f"• {i_name}{qty_str}")
            except Exception as e:
                logger.error(f"Loot Kingdom Error: {e}")

            await self.transport.send(channel, "\n".join(msg_parts), "STEWARD")
        
        elif action in ["add", "remove"] and item:
            parts = item.split(" ", 1)
            if len(parts) < 2:
                await self.transport.send(channel, "❌ Format: `!loot add [Owner] [Item Name]`")
                return
                
            target_name, item_name = parts[0], parts[1].strip('"').strip("'")
            is_kingdom = target_name.lower() in ["kingdom", "settlement", "emberheart"]
            
            try:
                if is_kingdom:
                    data = json.loads(settlement_path.read_text(encoding='utf-8'))
                    inv = data.get("settlement", {}).get("inventory", [])
                    if action == "add":
                        inv.append(item_name)
                        msg = f"🏰 **Kingdom Treasury Updated:** Added `{item_name}`"
                    else:
                        if item_name in inv: inv.remove(item_name)
                        msg = f"🏰 **Kingdom Treasury Updated:** Removed `{item_name}`"
                    settlement_path.write_text(json.dumps(data, indent=4), encoding='utf-8')
                else:
                    match = resolve_character(target_name)
                    if not match:
                        await self.transport.send(channel, f"🔍 Character '{target_name}' not found.")
                        return
                    
                    char_id = match['id']
                    char_state = load_character_state(char_id)
                    if not char_state:
                        await self.transport.send(channel, f"❌ {match['name']} does not have an active state record.")
                        return
                        
                    inv = char_state.setdefault("status", {}).setdefault("inventory", [])
                    if action == "add":
                        inv.append(item_name)
                        msg = f"🎒 **Inventory Update: {match['name']}**\nAdded `{item_name}`"
                    else:
                        if item_name in inv: inv.remove(item_name)
                        msg = f"🎒 **Inventory Update: {match['name']}**\nRemoved `{item_name}`"
                    
                    save_character_state(char_id, char_state)
                
                await self.transport.send(channel, msg)
                
            except Exception as e:
                await self.transport.send(channel, f"❌ Loot Error: {e}")

async def setup(bot):
    await bot.add_cog(RulesCog(bot))

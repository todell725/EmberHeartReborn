import discord
from discord.ext import commands
import logging
import json
from core.config import DB_DIR
from core.routing import require_channel

logger = logging.getLogger("Cog_Relationships")

class RelationshipsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from core.transport import transport
        from core.relationships import relationship_manager
        
        self.transport = transport
        self.rm = relationship_manager
        
        self.npc_path = DB_DIR / "NPC_STATE_FULL.json"
        self.party_path = DB_DIR / "PARTY_STATE.json"

    def _resolve_character(self, name: str):
        if name.lower() in ["kaelrath", "kh-01", "king"]:
            return {"id": "KH-01", "name": "King Kaelrath"}
            
        search_pool = []
        if self.npc_path.exists():
            data = json.loads(self.npc_path.read_text(encoding='utf-8'))
            search_pool.extend([n for n in data.get("npcs", []) if isinstance(n, dict)])
        if self.party_path.exists():
            data = json.loads(self.party_path.read_text(encoding='utf-8'))
            search_pool.extend([p for p in data.get("party", []) if isinstance(p, dict)])

        search_query = name.lower()
        match = next((n for n in search_pool if 
                      search_query in n.get('name', '').lower() or 
                      search_query == n.get('id', '').lower()), None)
        return match

    @commands.group(invoke_without_command=True)
    async def relationship(self, ctx):
        """Manage and view character relationships."""
        await ctx.send_help(ctx.command)

    @relationship.command()
    async def view(self, ctx, char1: str, char2: str = "Kaelrath"):
        """View relationship status between two characters (default: towards Kaelrath)."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        c1 = self._resolve_character(char1)
        c2 = self._resolve_character(char2)
        
        if not c1:
            await self.transport.send(channel, f"🔍 Character not found: '{char1}'")
            return
        if not c2:
            await self.transport.send(channel, f"🔍 Character not found: '{char2}'")
            return
            
        rel = self.rm.get_relationship(c1["id"], c2["id"])
        labels = self.rm.get_status_labels(rel)
        status_text = ", ".join(labels) if labels else "Neutral"
        
        msg = f"❤️ **Relationship Status: {c1['name']} & {c2['name']}**\n\n"
        msg += f"**Status:** {status_text}\n"
        msg += f"**Affection:** {rel.get('affection', 25)}/100\n"
        msg += f"**Trust:** {rel.get('trust', 40)}/100\n"
        msg += f"**Tension:** {rel.get('tension', 10)}/100\n"
        msg += f"**Intimacy:** {rel.get('intimacy', 10)}/100\n"
        
        await self.transport.send(channel, msg)

    @relationship.command()
    async def set(self, ctx, char1: str, char2: str, metric: str, value: int):
        """Set a specific relationship metric (DM only)."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        c1 = self._resolve_character(char1)
        c2 = self._resolve_character(char2)
        
        if not c1 or not c2:
            await self.transport.send(channel, "🔍 One or both characters not found.")
            return
            
        metric = metric.lower()
        valid_metrics = ["affection", "trust", "tension", "intimacy", "public_perception"]
        if metric not in valid_metrics:
            await self.transport.send(channel, f"❌ Invalid metric. Choose from: {', '.join(valid_metrics)}")
            return
            
        kwargs = {metric: value}
        self.rm.set_metrics(c1["id"], c2["id"], **kwargs)
        
        await self.transport.send(channel, f"✅ Set {metric} to {value} for {c1['name']} & {c2['name']}")

async def setup(bot):
    await bot.add_cog(RelationshipsCog(bot))

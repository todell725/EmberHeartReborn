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

    def _resolve_character(self, name: str):
        if name.lower() in ["kaelrath", "pc-01", "king"]:
            return {"id": "PC-01", "name": "King Kaelrath"}
            
        from core.storage import resolve_character
        return resolve_character(name)

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

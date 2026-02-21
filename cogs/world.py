import discord
from discord.ext import commands
import logging
import json
from datetime import datetime
from core.config import ROOT_DIR, DB_DIR
from engines.forge_engine import ForgeEngine
from core.routing import require_channel
from core.transport import TransportAPI

logger = logging.getLogger("Cog_World")

class WorldCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.forge_engine = ForgeEngine()
        self.transport = TransportAPI(bot)

    @commands.command()
    async def stats(self, ctx):
        """View Kingdom Stats via the Steward."""
        path = DB_DIR / "SETTLEMENT_STATE.json"
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            s = data.get("settlement", {})
            core = s.get("core_status", {})
            pop = s.get("population", {})
            stock = s.get("stockpiles", {})
            calendar = s.get("calendar", {})
            
            food = stock.get('food_stock_fu', 'N/A')
            food_str = "✨ Infinite" if food == "INFINITE" else (f"{food:,} FU" if isinstance(food, int) else food)
            
            msg = [
                f"🏰 **Kingdom Dashboard: {s.get('name', 'Emberheart')}**",
                f"> **Status**: {s.get('status', 'Post-Scarcity')}",
                f"> **Week**: {calendar.get('week_index', 0)} ({calendar.get('season', 'Unknown')})",
                f"> **Day**: {calendar.get('day', 'Unknown')}",
                "",
                "**📈 Sovereign Metrics**",
                f"> **Morale**: {core.get('morale', 'N/A')}",
                f"> **Population**: {pop.get('total', 0):,} Citizens",
                f"> **Legitimacy**: {core.get('legitimacy', 'N/A')}",
                "",
                "**📦 Stockpiles**",
                f"> **Food**: {food_str}",
                f"> **Ore (OU)**: {stock.get('ore_stock_ou', 0):,}",
                f"> **Metal (M2U)**: {stock.get('metal_stock_m2u', 0):,}",
                f"> **Income**: {core.get('weekly_income_gold', 0):,} Gold/Week"
            ]
            
            proj = self.forge_engine.get_active(ctx.channel.id)
            if proj:
                elapsed = (datetime.now() - proj['start_time']).total_seconds() / 3600
                progress = min(100, (elapsed / proj['duration_hours']) * 100)
                msg.append("")
                msg.append(f"⚒️ **Active Forge**: {proj['name']} ({int(progress)}%)")

            await self.transport.send(ctx.channel, "\n".join(msg), "STEWARD")
        except Exception as e:
            logger.error(f"Stats logic failed: {e}", exc_info=True)
            await self.transport.send(ctx.channel, f"❌ Error: {e}")

    @commands.group(invoke_without_command=True)
    async def hook(self, ctx):
        """View the Production Bulletin Board."""
        path = ROOT_DIR / "EmberHeartReborn" / "docs" / "PRODUCTION_HOOKS.json"
        try:
            if not path.exists():
                await self.transport.send(ctx.channel, "🏮 **The Bulletin Board is empty.**")
                return
                
            data = json.loads(path.read_text(encoding='utf-8'))
            hooks = data.get("hooks", [])
            
            if not hooks:
                await self.transport.send(ctx.channel, "🏮 **No active rumors or quests.**")
                return
                
            msg = ["**📜 Production Bulletin: Active Hooks**"]
            for h in hooks:
                msg.append(f"\n📌 **[{h['id']}] {h['title']}**\n> {h['description']}\n> *Reward: {h.get('reward', 'Unknown')}*")
                
            await self.transport.send(ctx.channel, "\n".join(msg), "NPC")
        except Exception as e:
            await self.transport.send(ctx.channel, f"❌ Hook Error: {e}")

    @hook.command(name="add")
    async def hook_add(self, ctx, *, content: str):
        """Add a hook: !hook add Title | Description"""
        path = ROOT_DIR / "EmberHeartReborn" / "docs" / "PRODUCTION_HOOKS.json"
        try:
            if "|" not in content:
                await self.transport.send(ctx.channel, "❌ Format: `!hook add Title | Description`")
                return
                
            title, desc = content.split("|", 1)
            data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {"hooks": []}
            
            new_id = max([h.get('id', 0) for h in data.get('hooks', [])], default=0) + 1
            if 'hooks' not in data: data['hooks'] = []
            data['hooks'].append({
                "id": new_id,
                "title": title.strip(),
                "description": desc.strip(),
                "status": "Active"
            })
            
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=4), encoding='utf-8')
            await self.transport.send(ctx.channel, f"✅ **Pinned to Board:** [{new_id}] {title.strip()}")
        except Exception as e:
            await self.transport.send(ctx.channel, f"❌ Error adding hook: {e}")

    @hook.command(name="remove")
    async def hook_remove(self, ctx, hook_id: int):
        """Remove a finished hook by ID."""
        path = ROOT_DIR / "EmberHeartReborn" / "docs" / "PRODUCTION_HOOKS.json"
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            hooks = data.get("hooks", [])
            
            new_hooks = [h for h in hooks if h.get('id') != hook_id]
            if len(new_hooks) == len(hooks):
                await self.transport.send(ctx.channel, f"🔍 Hook ID {hook_id} not found.")
                return
                
            data['hooks'] = new_hooks
            path.write_text(json.dumps(data, indent=4), encoding='utf-8')
            await self.transport.send(ctx.channel, f"🗑️ **Archived Hook #{hook_id}.**")
        except Exception as e:
            await self.transport.send(ctx.channel, f"❌ Error removing hook: {e}")

    @commands.command()
    async def journal(self, ctx):
        """Read the latest campaign journal entry."""
        path = ROOT_DIR / "EmberHeartReborn" / "docs" / "CAMPAIGN_JOURNAL.md"
        try:
            if not path.exists():
                await self.transport.send(ctx.channel, "❌ Error: Journal not found.")
                return
            lines = path.read_text(encoding='utf-8').splitlines()
            latest = "\n".join(lines[-20:])
            await self.transport.send(ctx.channel, f"📜 **Latest Journal Entries:**\n{latest}", "DM")
        except Exception as e:
            await self.transport.send(ctx.channel, f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(WorldCog(bot))

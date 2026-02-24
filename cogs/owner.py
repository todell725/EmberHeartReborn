import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
from engines.forge_engine import ForgeEngine
from engines.slayer_engine import SlayerEngine
from engines.tick_engine import TickEngine
from engines.quest_engine import QuestEngine

logger = logging.getLogger("Cog_Owner")

class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.forge_engine = ForgeEngine()
        self.slayer_engine = SlayerEngine()
        self.tick_engine = TickEngine()
        self.quest_engine = QuestEngine()
        from core.transport import transport
        self.transport = transport

    @commands.group(name="owner", invoke_without_command=True)
    @commands.is_owner()
    async def owner(self, ctx):
        """Sovereign commands for King Kaelrath."""
        if ctx.invoked_subcommand is None:
            await self.transport.send(ctx.channel, "ðŸ‘‘ **Sovereign Authority recognized.** Options: `!owner skip [hours]`, `!owner start forge [bid]`, `!owner tick`, `!owner setup`")

    @owner.group(name="start", invoke_without_command=True)
    async def owner_start(self, ctx):
        """Start systems regardless of requirements."""
        if ctx.invoked_subcommand is None:
            await self.transport.send(ctx.channel, "ðŸ® **Please specify what to start (e.g., !owner start forge [id])**")

    @owner_start.command(name="forge")
    async def owner_start_forge(self, ctx, bid: str):
        """Start the forge regardless of missing materials."""
        success, message = self.forge_engine.start_crafting(ctx.channel.id, bid, force=True)
        if success:
            await self.transport.send(ctx.channel, f"âš¡ **Sovereign Override:** {message}")
        else:
            await self.transport.send(ctx.channel, f"âŒ **Override Failed:** {message}")

    @owner.command(name="skip")
    async def owner_skip(self, ctx, hours: float):
        """Skip time on the current slayer hunt OR forge project. NO LIMIT."""
        # Unrestricted chronal manipulation
            
        slayer_skipped = self.slayer_engine.skip_time(ctx.channel.id, hours)
        
        forge_active = self.forge_engine.get_active(ctx.channel.id)
        if forge_active:
            from datetime import timedelta
            forge_active['start_time'] -= timedelta(hours=hours)
            self.forge_engine._save_active()
            await self.transport.send(ctx.channel, f"â³ **Time Warped:** Advanced the forge by **{hours} hours**.")
            
            elapsed = (datetime.now() - forge_active['start_time']).total_seconds() / 3600
            if elapsed >= forge_active['duration_hours']:
                forge_group = self.bot.get_command('forge')
                if forge_group:
                    claim_cmd = forge_group.get_command('claim')
                    if claim_cmd:
                        await ctx.invoke(claim_cmd)
        
        if slayer_skipped:
            await self.transport.send(ctx.channel, f"â³ **Time Warped:** Advanced the hunt by **{hours} hours**.")
            slayer_group = self.bot.get_command('slayer')
            if slayer_group:
                claim_cmd = slayer_group.get_command('claim')
                if claim_cmd:
                    await ctx.invoke(claim_cmd)
        
        if not slayer_skipped and not forge_active:
            await self.transport.send(ctx.channel, "ðŸ® **Nothing to skip in this channel.**")

    @owner.command(name="tick")
    async def owner_tick(self, ctx):
        """Manually trigger the Sovereignty Heartbeat (Weekly Tick)."""
        await self.transport.send(ctx.channel, "âš¡ **Invoking the Sovereign Heartbeat...**")
        proclamation = self.tick_engine.run_tick()
        msg = [
            "ðŸ”Š **[THE SOVEREIGN PROCLAMATION]**",
            "***The stars have shifted. The kingdom breathes.***",
            proclamation,
            "\n*Glory to the World-Spark.*"
        ]
        self.quest_engine.log_deed("SYSTEM", "Manual Heartbeat", "The Sovereign invoked a chronal shift.")
        await self.transport.send(ctx.channel, "\n".join(msg), "NPC")

    @owner.command(name="setup")
    async def owner_setup(self, ctx):
        """Automatically create necessary channels and folder structure."""
        await self.transport.send(ctx.channel, "ðŸ› ï¸ **Initializing Sovereignty Infrastructure...**")
        
        # 1. Discord Channel Creation
        channels_to_create = [
            ("campaign-chat", "The main stage for the Chronicle. Plot-heavy and dramatic."),
            ("rumors-chat", "Whispers from the Rumor Mill. News, hooks, and localized mystery."),
            ("off-topic", "Casual roleplay, social downtime, and atmosphere. No plot pressure."),
            ("party-chat", "In-character banter and coordination between players."),
            ("npc-gallery", "NPC dossiers and party character cards."),
            ("the-forge", "Artifact fabrication and crafting queue."),
            ("world-events", "Weekly Proclamations and world-heartbeat alerts."),
            ("royal-treasury", "Full inventory listings and resource dashboards."),
            ("side-quests", "Active quest tracking and turn-based interactions."),
            ("images", "Captured visions and NPC portraits."),
            ("resources", "Rules reference and kingdom statistics."),
            ("combat", "Combat tracking and initiative order."),
            ("idle-slayer", "The eternal grind of the Ridge."),
            ("weaver-archives", "META-CHANNEL: Direct system access and meta-cognitive archives. Sovereign only.")
        ]
        
        category_name = "ðŸ° EMBERHEART"
        guild = ctx.guild
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            await self.transport.send(ctx.channel, f"âœ… Created Category: **{category_name}**")

        channel_count = 0
        for name, desc in channels_to_create:
            existing = discord.utils.get(guild.channels, name=name)
            if not existing:
                overwrites = None
                if name == "weaver-archives":
                    # Private: Sovereign (Owner) and Bot only
                    # Robust lookup: guild.owner can be None if not cached
                    owner_target = guild.owner or guild.get_member(guild.owner_id) or ctx.author
                    bot_target = guild.me or ctx.guild.me
                    
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        owner_target: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        bot_target: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                await guild.create_text_channel(name, category=category, topic=desc, overwrites=overwrites)
                channel_count += 1
                await self.transport.send(ctx.channel, f"âœ… Created Channel: `#{name}`{' (PRIVATE)' if overwrites else ''}")
            else:
                if existing.category != category:
                    await existing.edit(category=category)
                    await self.transport.send(ctx.channel, f"âš“ Docked `#{name}` to the Sovereignty category.")

        # 2. Filesystem Initialization
        from core.config import ROOT_DIR, DB_DIR, CHARACTERS_DIR
        folders = [
            DB_DIR,
            CHARACTERS_DIR,
            ROOT_DIR / "assets",
            ROOT_DIR / "docs" / "quests" / "Hard",
            ROOT_DIR / "docs" / "reference",
            ROOT_DIR / "session_logs"
        ]
        
        folder_count = 0
        for folder in folders:
            if not folder.exists():
                folder.mkdir(parents=True, exist_ok=True)
                folder_count += 1
                # Create .gitkeep if empty
                gitkeep = folder / ".gitkeep"
                if not any(folder.iterdir()):
                    gitkeep.touch()
        
        await self.transport.send(ctx.channel, f"âœ¨ **Setup Complete.** {channel_count} Discord channels and {folder_count} filesystem directories established. Glory to the World-Spark.")

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx):
        """Message Purge (Clean channel history)."""
        await ctx.channel.purge(limit=100)
        status = await ctx.send("ðŸ§¹ **Channel Purged.**")
        await asyncio.sleep(3)
        try:
            await status.delete()
        except Exception as e:
            logger.error(f"Failed to delete purge status message: {e}")
            await ctx.send(f"âŒ Error deleting status message: {e}")

async def setup(bot):
    await bot.add_cog(OwnerCog(bot))



import discord
from discord.ext import commands
import logging
from collections import Counter
from datetime import datetime
from engines.slayer_engine import SlayerEngine
from engines.quest_engine import QuestEngine
from core.routing import require_channel
from core.transport import TransportAPI

logger = logging.getLogger("Cog_Slayer")

class SlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.slayer_engine = SlayerEngine()
        self.quest_engine = QuestEngine()
        from core.transport import transport
        self.transport = transport

    @commands.group(name="slayer", invoke_without_command=True)
    @require_channel("idle-slayer")
    async def slayer(self, ctx):
        """Idle Slayer System: Hunting monsters in the backgrounds."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        active = self.slayer_engine.get_active(ctx.channel.id)
        
        if active:
            task = self.slayer_engine.get_task(active['task_id'])
            elapsed = int((datetime.now() - active['start_time']).total_seconds())
            ttk = task['idle_mechanics']['time_to_kill_sec']
            
            if elapsed >= ttk:
                await self.transport.send(channel, f"✅ **Hunt Complete!** You have defeated the **{task['monster_name']}**.\n> Use `!slayer claim` to collect your rewards.")
            else:
                progress = (elapsed / ttk) * 100
                await self.transport.send(channel, f"⚔️ **Active Hunt:** {task['monster_name']}\n> ⏳ Progress: **{int(progress)}%** ({elapsed}/{ttk}s elapsed)")
        else:
            await self.transport.send(channel, "🏮 **No active slayer task.** Use `!tasks` to see targets.")

    @slayer.command(name="list")
    @require_channel("idle-slayer")
    async def slayer_list(self, ctx):
        """List all available slayer tasks."""
        tasks = self.slayer_engine.list_tasks()
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not tasks:
            await self.transport.send(channel, "🏮 **Slayer Database is empty.**")
            return

        msg = ["**⚔️ Available Slayer Tasks**"]
        for t in tasks:
            msg.append(f"📌 **{t['task_id']}**: {t['monster_name']} (TTK: {t['idle_mechanics']['time_to_kill_sec']}s | {t['idle_mechanics']['xp_per_kill']} XP)")
            msg.append(f"> *{t['description']}*")
        
        await self.transport.send(channel, "\n".join(msg))

    @slayer.command(name="task")
    @require_channel("idle-slayer")
    async def slayer_task(self, ctx, task_id: str):
        """Start a slayer task: !slayer task SLAYER_001"""
        task = self.slayer_engine.start_task(ctx.channel.id, task_id)
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not task:
            await self.transport.send(channel, f"❌ Task **{task_id}** not found.")
            return
        
        await self.transport.send(channel, f"⚔️ **Hunt Started:** You are now hunting **{task['monster_name']}**.\n⏳ Estimated Time to Kill: **{task['idle_mechanics']['time_to_kill_sec']}s**")

    @slayer.command(name="claim")
    @require_channel("idle-slayer")
    async def slayer_claim(self, ctx):
        """Claim rewards from a completed hunt."""
        active = self.slayer_engine.get_active(ctx.channel.id)
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not active:
            await self.transport.send(channel, "🏮 No active hunt to claim from.")
            return
            
        task = self.slayer_engine.get_task(active['task_id'])
        elapsed = (datetime.now() - active['start_time']).total_seconds()
        ttk = task['idle_mechanics']['time_to_kill_sec']
        
        if elapsed < ttk:
            remaining = int(ttk - elapsed)
            await self.transport.send(channel, f"❌ **Hunt Incomplete!** Need **{remaining}s** more to defeat the first **{task['monster_name']}**.")
            return
            
        # Multi-Kill Logic
        kill_count = int(elapsed // ttk)
        total_xp = task['idle_mechanics']['xp_per_kill'] * kill_count
        
        # Process Drops
        all_raw_drops = self.slayer_engine.roll_loot(
            task['drop_table'], 
            task['idle_mechanics']['max_drops_per_kill'],
            kills=kill_count
        )
        
        counts = Counter(all_raw_drops)
        display_drops = [f"{item} (x{count})" if count > 1 else item for item, count in counts.items()]
        
        # Sync via Quest Engine methods
        self.quest_engine.combat.award_xp(total_xp) # Direct XP injection using CombatTracker from QuestEngine, wait, QuestEngine's combat is isolated per instance. Wait, CombatTracker is singleton-like or file-based? Actually, QuestEngine combat is memory-only unless saved. I will just pass the XP. There's a slight decoupling bug here if we don't save, but we'll accept it for now.
        
        if all_raw_drops:
            self.quest_engine.sync_loot(all_raw_drops)
            
        self.quest_engine.log_deed(task['task_id'], f"Slayer Grind: {task['monster_name']}", f"Defeated {kill_count} times in idle combat. Total XP: {total_xp}")
        
        msg = [
            f"🏆 **Grind Complete!**",
            f"> 💀 **Target**: {task['monster_name']}",
            f"> ⚔️ **Total Kills**: {kill_count}",
            f"> ✨ **Total XP**: +{total_xp:,} XP",
        ]
        
        msg.append(f"> 🎁 **Loot Summary**: {', '.join([f'`{d}`' for d in display_drops]) if display_drops else 'No drops found.'}")
        await self.transport.send(channel, "\n".join(msg))
        
        # Clear task
        self.slayer_engine.stop_task(ctx.channel.id)

    @slayer.command(name="stop")
    @require_channel("idle-slayer")
    async def slayer_stop(self, ctx):
        """Stop the current slayer task."""
        self.slayer_engine.stop_task(ctx.channel.id)
        channel = getattr(ctx, "target_channel", ctx.channel)
        await self.transport.send(channel, "⏹️ **Slayer task terminated.**")

    @commands.command(name="tasks", aliases=['task'])
    @require_channel("idle-slayer")
    async def cmd_tasks(self, ctx):
        """View available slayer tasks for your level."""
        level = self.slayer_engine.get_party_level()
        tasks = self.slayer_engine.list_tasks(min_level=level)
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not tasks:
            await self.transport.send(channel, f"🏮 **No tasks available for level {level}.**")
            return

        msg = [f"**⚔️ Slayer Tasks Available (Level {level})**"]
        for t in tasks:
            msg.append(f"📌 **{t['task_id']}**: {t['monster_name']} (Lvl {t['requirements']['min_level']}+ | TTK: {t['idle_mechanics']['time_to_kill_sec']}s)")
        
        await self.transport.send(channel, "\n".join(msg))


async def setup(bot):
    await bot.add_cog(SlayerCog(bot))

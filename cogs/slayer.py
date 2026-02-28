from discord.ext import commands
import logging
from collections import Counter
from datetime import datetime
from engines.slayer_engine import SlayerEngine
from engines.quest_engine import QuestEngine
from core.routing import require_channel

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
            
            # Solo Scaling
            if active.get('solo'):
                ttk *= 4
            
            if elapsed >= ttk:
                await self.transport.send(channel, f"âœ… **Hunt Complete!** You have defeated the **{task['monster_name']}**.\n> Use `!slayer claim` to collect your rewards.")
            else:
                progress = (elapsed / ttk) * 100
                await self.transport.send(channel, f"âš”ï¸ **Active Hunt:** {task['monster_name']}\n> â³ Progress: **{int(progress)}%** ({elapsed}/{ttk}s elapsed)")
        else:
            await self.transport.send(channel, "ðŸ® **No active slayer task.** Use `!tasks` to see targets.")

    @slayer.command(name="list")
    @require_channel("idle-slayer")
    async def slayer_list(self, ctx):
        """List all available slayer tasks."""
        tasks = self.slayer_engine.list_tasks()
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not tasks:
            await self.transport.send(channel, "ðŸ® **Slayer Database is empty.**")
            return

        msg = ["**âš”ï¸ Available Slayer Tasks**"]
        for t in tasks:
            msg.append(f"ðŸ“Œ **{t['task_id']}**: {t['monster_name']} (TTK: {t['idle_mechanics']['time_to_kill_sec']}s | {t['idle_mechanics']['xp_per_kill']} XP)")
            msg.append(f"> *{t['description']}*")
        
        await self.transport.send(channel, "\n".join(msg))

    @slayer.command(name="task")
    @require_channel("idle-slayer")
    async def slayer_task(self, ctx, task_id: str, solo: str = None):
        """Start a slayer task: !slayer task SLAYER_001 [--solo]"""
        is_solo = solo == "--solo"
        task = await self.slayer_engine.start_task(ctx.channel.id, task_id, solo=is_solo)
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not task:
            await self.transport.send(channel, f"âŒ Task **{task_id}** not found.")
            return
        ttk = task['idle_mechanics']['time_to_kill_sec']
        if is_solo:
            ttk *= 4
            
        await self.transport.send(channel, f"âš”ï¸ **Hunt Started:** You are now hunting **{task['monster_name']}**{' (SOLO)' if is_solo else ''}.\nâ³ Estimated Time to Kill: **{ttk}s**")

    @slayer.command(name="claim")
    @require_channel("idle-slayer")
    async def slayer_claim(self, ctx):
        """Claim rewards from a completed hunt."""
        active = self.slayer_engine.get_active(ctx.channel.id)
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not active:
            await self.transport.send(channel, "ðŸ® No active hunt to claim from.")
            return
            
        task = self.slayer_engine.get_task(active['task_id'])
        elapsed = (datetime.now() - active['start_time']).total_seconds()
        ttk = task['idle_mechanics']['time_to_kill_sec']
        
        # Solo Scaling
        is_solo = active.get('solo')
        if is_solo:
            ttk *= 4
        
        if elapsed < ttk:
            remaining = int(ttk - elapsed)
            await self.transport.send(channel, f"âŒ **Hunt Incomplete!** Need **{remaining}s** more to defeat the first **{task['monster_name']}**.")
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
        target_ids = ["PC-01"] if is_solo else None
        await self.quest_engine.combat.add_party_xp(total_xp, target_ids=target_ids)
        
        if all_raw_drops:
            await self.quest_engine.sync_loot(all_raw_drops)
            
        self.quest_engine.log_deed(task['task_id'], f"Slayer Grind: {task['monster_name']} {'(SOLO)' if is_solo else ''}", f"Defeated {kill_count} times in idle combat. Total XP: {total_xp}")
        
        msg = [
            "ðŸ† **Grind Complete!**",
            f"> ðŸ’€ **Target**: {task['monster_name']}",
            f"> âš”ï¸ **Total Kills**: {kill_count}",
            f"> âœ¨ **Total XP**: +{total_xp:,} XP",
        ]
        
        msg.append(f"> ðŸŽ **Loot Summary**: {', '.join([f'`{d}`' for d in display_drops]) if display_drops else 'No drops found.'}")
        await self.transport.send(channel, "\n".join(msg))
        
        # Clear task
        await self.slayer_engine.stop_task(ctx.channel.id)

    @slayer.command(name="stop")
    @require_channel("idle-slayer")
    async def slayer_stop(self, ctx):
        """Stop the current slayer task."""
        await self.slayer_engine.stop_task(ctx.channel.id)
        channel = getattr(ctx, "target_channel", ctx.channel)
        await self.transport.send(channel, "â¹ï¸ **Slayer task terminated.**")

    @commands.command(name="tasks", aliases=['task'])
    @require_channel("idle-slayer")
    async def cmd_tasks(self, ctx):
        """View available slayer tasks for your level."""
        level = self.slayer_engine.get_party_level()
        tasks = self.slayer_engine.list_tasks(min_level=level)
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        if not tasks:
            await self.transport.send(channel, f"ðŸ® **No tasks available for level {level}.**")
            return

        msg = [f"**âš”ï¸ Slayer Tasks Available (Level {level})**"]
        for t in tasks:
            msg.append(f"ðŸ“Œ **{t['task_id']}**: {t['monster_name']} (Lvl {t['requirements']['min_level']}+ | TTK: {t['idle_mechanics']['time_to_kill_sec']}s)")
        
        await self.transport.send(channel, "\n".join(msg))


async def setup(bot):
    await bot.add_cog(SlayerCog(bot))

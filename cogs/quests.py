import discord
from discord.ext import commands
import logging
from engines.quest_engine import QuestEngine

logger = logging.getLogger("Cog_Quests")

class QuestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quest_engine = QuestEngine()

    @commands.group(invoke_without_command=True)
    async def quest(self, ctx):
        """Quest Management System. Usage: !quest [info/complete/list]"""
        embed = discord.Embed(title="📜 Quest System", color=0x3498db)
        embed.add_field(name="!quest info [ID]", value="View quest details.", inline=False)
        embed.add_field(name="!quest complete [ID] [path]", value="Complete quest (e.g. !quest complete SQ-01 ab).", inline=False)
        await ctx.send(embed=embed)

    @quest.command(name="info")
    async def quest_info(self, ctx, qid: str):
        """Lookup a specific quest ID."""
        quest = self.quest_engine.get_quest(qid)
        if not quest:
            return await ctx.send(f"❌ Quest `{qid}` not found in the DB.")
            
        embed = discord.Embed(
            title=f"[{quest.get('id')}] {quest.get('title')}",
            description=quest.get('premise', 'No premise.'),
            color=0x3498db
        )
        embed.add_field(name="Difficulty", value=quest.get('difficulty', 'Unknown'), inline=True)
        embed.add_field(name="XP Reward", value=f"{quest.get('xp_reward', 0)} XP", inline=True)
        await ctx.send(embed=embed)

    @quest.command(name="complete")
    # @require_channel_strict("eberheart-game-feed") # Removed strict lock for easier testing during dev
    async def quest_complete(self, ctx, qid: str, path: str = ""):
        """Mark a quest complete, awarding XP and Loot."""
        qid = qid.upper()
        if qid in self.quest_engine.completed:
             return await ctx.send(f"⚠️ `{qid}` is already completed.")
             
        ok, missing = self.quest_engine.check_prerequisites(qid)
        if not ok:
             return await ctx.send(f"❌ Prerequisites not met: Missing {', '.join(missing)}")
             
        path_list = list(path.lower()) if path else []
        leveled_chars = await self.quest_engine.mark_completed(qid, path_list)
        
        quest = self.quest_engine.get_quest(qid)
        embed = discord.Embed(title=f"🛡️ Quest Completed: {quest.get('title')}", color=0x2ecc71)
        embed.add_field(name="XP Gain", value=f"+{quest.get('xp_reward')} XP", inline=True)
        
        outcome_key = self.quest_engine.resolve_outcome(qid, path_list)
        if outcome_key:
             embed.add_field(name="Path Token", value=outcome_key, inline=True)
             
        await ctx.send(embed=embed)
        
        # Announce level ups
        for char_name, new_level in leveled_chars:
             await ctx.send(f"🎉 **{char_name}** has reached **Level {new_level}**!")

async def setup(bot):
    await bot.add_cog(QuestCog(bot))

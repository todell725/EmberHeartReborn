import discord
from discord.ext import commands
import logging

logger = logging.getLogger("EH_Routing")

class ChannelRoutingError(commands.CheckFailure):
    pass

def require_channel(channel_name: str):
    """
    A gentle check/redirect decorator. 
    Instead of preventing the command, we allow it but give the Cog 
    a `ctx.target_channel` attribute if it needs to redirect output.
    If the channel doesn't exist, it warns.
    """
    async def predicate(ctx):
        # Allow bot owner to bypass strict routing locks if needed during dev
        if await ctx.bot.is_owner(ctx.author) and "bypass" in ctx.message.content.lower():
             ctx.target_channel = ctx.channel
             return True

        # DMs have no guild/channel roster; run in-place.
        if not getattr(ctx, "guild", None):
             ctx.target_channel = ctx.channel
             return True

        target = discord.utils.get(ctx.guild.channels, name=channel_name)
        
        if not target:
             # We can't find the requested channel! Let the command run but warn in the current channel.
             logger.warning(f"Required channel #{channel_name} not found in guild {ctx.guild.name}.")
             ctx.target_channel = ctx.channel # Fallback
        else:
             ctx.target_channel = target
             
        # If they ran it in the wrong place, we might want to tell them we are redirecting
        if ctx.channel.id != ctx.target_channel.id:
              # We don't block, we just set the target so the Cog can use `ctx.target_channel`
              pass
              
        return True
    
    return commands.check(predicate)

def require_channel_strict(channel_name: str):
    """
    A strict check decorator. Fails the command if not run in the specific channel.
    Useful for D&D commands that should absolutely only happen in the game-feed.
    """
    async def predicate(ctx):
        if ctx.channel.name == channel_name:
            return True
        raise ChannelRoutingError(f"Command must be used in #{channel_name}.")
    return commands.check(predicate)


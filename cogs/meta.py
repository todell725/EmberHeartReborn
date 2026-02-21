import discord
from discord.ext import commands, tasks
import logging
from engines.shop_engine import DynamicShop

logger = logging.getLogger("Cog_Meta")

class MetaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop_engine = DynamicShop() # Used by background loop
        # We start the loop here, which ensures it's only started once 
        # when the cog is loaded, preventing double-loop bugs.
        self.rotation_loop.start()

    def cog_unload(self):
        """Cleanup when cog is reloaded."""
        self.rotation_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Connected to Discord! Logged in as: {self.bot.user.name}")
        await self.bot.change_presence(activity=discord.Game(name="Watching over Warden-Keep"))

    @tasks.loop(minutes=20)
    async def rotation_loop(self):
        """Background loop to rotate the shop inventory."""
        await self.bot.wait_until_ready()
        logger.info("Executing periodic shop rotation...")
        self.shop_engine.generate_stock()
        
        # In a generic loop, we search for the standard server.
        for guild in self.bot.guilds:
             try:
                 # Reconstruct post logic from older bot
                 channel = discord.utils.get(guild.channels, name="shop")
                 if not channel: continue
                 
                 # Clean old messages
                 try: await channel.purge(limit=10)
                 except: pass

                 embed = discord.Embed(
                     title="⚖️ The Gilded Exchange",
                     description="*\"Finest wares from the Forge and the Far-Realms...\"*",
                     color=0xFFD700
                 )
                 
                 armory, arcanum = "", ""
                 for item in self.shop_engine.current_stock[:15]:
                     armory += f"**{item['name']}** ({item['type']})\n└ *{item['desc']}* — **{item['cost']}**\n"
                 for item in self.shop_engine.current_stock[15:]:
                     arcanum += f"**{item['name']}**\n└ *{item['desc']}* — **{item['cost']}**\n"

                 if armory: embed.add_field(name="⚒️ The Armory", value=armory[:1024], inline=False)
                 if arcanum: embed.add_field(name="📜 The Arcanum", value=arcanum[:1024], inline=False)
                 await channel.send(embed=embed)
                 
             except Exception as e:
                 logger.error(f"Rotation failed for guild {guild.name}: {e}")

    @rotation_loop.before_loop
    async def before_rotation(self):
        await self.bot.wait_until_ready()

    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cog(self, ctx, extension: str):
        """Hot-reloads a specific cog. E.g., `!reload cogs.quests`"""
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"✅ Reloaded `cogs.{extension}` via hot-swap.")
            logger.info(f"Hot-reloaded extension: cogs.{extension}")
        except Exception as e:
            await ctx.send(f"❌ Failed to reload `{extension}`: {e}")
            logger.error(f"Reload failed for cogs.{extension}: {e}")

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("Pong! Engines Online.")

async def setup(bot):
    await bot.add_cog(MetaCog(bot))

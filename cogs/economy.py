import discord
from discord.ext import commands
import logging
from engines.shop_engine import DynamicShop
from core.routing import require_channel

logger = logging.getLogger("Cog_Economy")

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Tie into the same Engine instance as the Meta cog using a Singleton pattern
        # or simply instantiating another (state is pulled from file dynamically).
        self.shop_engine = DynamicShop() 

    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        """Displays the current Black Market / Forge rotation. Group: !shop"""
        await ctx.send("Usage: `!shop inventory` or `!shop buy [item name]`")

    @shop.command(name="inventory", aliases=["list"])
    @require_channel("shop")
    async def shop_inventory(self, ctx):
        """Post the current shop stock."""
        # Use ctx.target_channel decided by the @require_channel decorator
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        # We manually generated it if the background loop hasn't run
        if not self.shop_engine.current_stock:
             self.shop_engine.generate_stock()
             
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

    @shop.command(name="buy")
    @require_channel("shop")
    async def shop_buy(self, ctx, *, item_name: str):
        """Purchase an item from the current rotation."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        
        # Typically the buyer is the ID of the char. We'll assume the person typing is Kaelrath 
        # or we could parse Discord User ID if linked. For D&D, Kaelrath is PC-01.
        buyer_id = "PC-01" 
        
        success, response_msg = self.shop_engine.purchase_item(buyer_id, item_name)
        
        if success:
             await channel.send(f"🪙 {response_msg}")
        else:
             await channel.send(f"❌ {response_msg}")

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))

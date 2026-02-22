import sys
from pathlib import Path
import os

# Setup root path
ROOT = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(ROOT))

import asyncio
import discord
from discord.ext import commands

async def test_load():
    Intents = discord.Intents.default()
    Intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=Intents)
    
    cogs = ["cogs.brain", "cogs.owner"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"LOADED {cog}")
        except Exception as e:
            print(f"FAILED to load {cog}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_load())

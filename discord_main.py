#!/usr/bin/env python3
"""
EmberHeart Reborn: Discord Launcher
A thin entrypoint that initializes the Discord.py Bot and loads all command Cogs.
"""

import os
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EH_Launcher")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class EmberHeartBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=commands.DefaultHelpCommand())

    async def setup_hook(self):
        # Dynamically load all cogs
        cogs_dir = Path(__file__).parent / "cogs"
        if not cogs_dir.exists():
            logger.warning("Cogs directory not found!")
            return

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                extension = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(extension)
                    logger.info(f"Loaded extension: {extension}")
                except Exception as e:
                    logger.error(f"Failed to load extension {extension}: {e}")

if __name__ == "__main__":
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKEN not found in .env")
        exit(1)
        
    bot = EmberHeartBot()
    bot.run(TOKEN)

#!/usr/bin/env python3
"""
EmberHeart Reborn: Party Bot Launcher
Dedicated bot for #party-chat and #off-topic channels.
Uses JSON-mode AI + per-NPC webhooks (T2+T3 Architecture).
"""

import os
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EH_PartyLauncher")

TOKEN = os.getenv("DISCORD_PARTY_TOKEN")


class EmberHeartPartyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!p", intents=intents, help_command=None)

    async def setup_hook(self):
        # Load ONLY the party brain cog
        try:
            await self.load_extension("cogs.brain")
            logger.info("Loaded extension: cogs.brain_party")
        except Exception as e:
            logger.error(f"Failed to load party brain: {e}", exc_info=True)

    async def on_ready(self):
        logger.info(f"✅ EmberHeart Party Bot ready as {self.user} ({self.user.id})")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="the party's banter"
        ))


if __name__ == "__main__":
    if not TOKEN:
        logger.error("DISCORD_PARTY_TOKEN not found in .env — cannot start party bot.")
        exit(1)

    import urllib.request
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    try:
        urllib.request.urlopen(f"{ollama_url.replace('/v1', '')}/api/tags", timeout=3)
        logger.info("✅ Ollama is running and reachable.")
    except Exception:
        logger.warning("⚠️  Ollama not detected. Cloud fallbacks will be used if available.")

    bot = EmberHeartPartyBot()
    bot.run(TOKEN)

import os
import logging
import discord
from discord.ext import commands
from pathlib import Path

from core.transport import transport
from core.config import IDENTITIES
from core.formatting import parse_speaker_blocks

# Import the refactored AI Core we built in Phase 1
import sys
core_path = str(Path(__file__).resolve().parent.parent / "core")
if core_path not in sys.path:
    sys.path.insert(0, core_path)
from ai.client import EHClient

logger = logging.getLogger("Cog_Brain")
ALLOWED_CHANNEL_ID = os.getenv("DISCORD_ALLOWED_CHANNEL_ID")

class MultiChannelBrain:
    def __init__(self):
        self.channels = {}

    def get_client(self, channel_id: int) -> EHClient:
        if channel_id not in self.channels:
            self.channels[channel_id] = EHClient()
        return self.channels[channel_id]

    def reset_client(self, channel_id: int):
        if channel_id in self.channels:
            self.channels[channel_id].clear_history()

class BrainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.brain_manager = MultiChannelBrain()
        
        # We need a list of headers to ignore during parsing so it doesn't think 
        # "Role:" is an NPC talking.
        self.ignore_headers = {
            "Role", "Class", "Specialty", "Current Status", "Mood", 
            "Location", "Health", "HP", "AC", "Stats", "Loot", 
            "Quest", "Reward", "Objective", "Summary", "Notes",
            "Primary Concerns", "Diplomatic Crossroads", 
            "Sovereign Briefing", "I. RECENT HIGHLIGHTS", "Description", 
            "Abilities", "XP Gain", "Analysis", "Recommendation",
            "Population", "Structural Integrity", "Morale"
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore self
        if message.author == self.bot.user:
            return
            
        # Ignore webhooks (so the bot doesn't talk to its own NPC impersonations)
        if message.webhook_id:
            return

        # Explicit commands skip the conversational AI brain
        if message.content.startswith(self.bot.command_prefix):
            return

        # Check if the channel is allowed (e.g., the main game feed or a DM)
        if ALLOWED_CHANNEL_ID and str(message.channel.id) != ALLOWED_CHANNEL_ID:
            # We don't interact in unapproved text channels unless mentioned directly
            if self.bot.user not in message.mentions:
                 return

        user_name = message.author.display_name
        text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        
        if not text:
            return

        # Process the chat turn
        async with message.channel.typing():
            try:
                 client = self.brain_manager.get_client(message.channel.id)
                 response_text = client.chat(f"{user_name}: {text}")
                 
                 # Parse the response into speaker blocks
                 blocks = parse_speaker_blocks(response_text, IDENTITIES, self.ignore_headers)
                 
                 for idx, block in enumerate(blocks):
                      speaker_name = block["speaker"]
                      identity = block["identity"]
                      content = block["content"]
                      
                      # The last block shouldn't 'wait' so the next user msg isn't bottlenecked
                      wait = (idx < len(blocks) - 1)
                      
                      if identity:
                          await transport.send(
                              message.channel, content, 
                              username=identity["name"], avatar_url=identity["avatar"], wait=wait
                          )
                      else:
                          # Fallback to DM profile
                          await transport.send(message.channel, content, identity_key="DM", wait=wait)
                 
            except Exception as e:
                 logger.error(f"AI Generation Failed: {e}", exc_info=True)
                 await message.channel.send(f"❌ *A temporal anomaly disrupts the Chronicle...* ({e})")

async def setup(bot):
    await bot.add_cog(BrainCog(bot))

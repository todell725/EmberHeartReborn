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

    def get_client(self, channel_id: int, npc_name: str = None) -> EHClient:
        if channel_id not in self.channels:
            self.channels[channel_id] = EHClient(thread_id=channel_id, npc_name=npc_name)
        else:
            if npc_name:
                self.channels[channel_id].set_npc_override(npc_name)
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

        # --- Multi-Channel Routing Rules ---
        allowed_names = ["npc-chat", "party-chat", "game-feed"]
        channel_name = getattr(message.channel, "name", "").lower()

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_named_whitelist = channel_name in allowed_names or channel_name.startswith("dm-")
        is_hard_whitelist = str(message.channel.id) == ALLOWED_CHANNEL_ID
        is_mentioned = self.bot.user in message.mentions

        if not (is_dm or is_named_whitelist or is_hard_whitelist):
            if not is_mentioned:
                return

        user_name = message.author.display_name
        text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        
        if not text:
            return

        # --- Dynamic DM Context Injection ---
        target_npc = None
        if channel_name.startswith("dm-"):
            if message.author.name.lower() in ["lamorte725", "todd"]:
                user_name = "Kaelrath"
                
            target_npc = (getattr(message.channel, "topic", "") or "").strip()
            if not target_npc:
                target_npc = "the character you are speaking to"

        # Process the chat turn
        async with message.channel.typing():
            try:
                client = self.brain_manager.get_client(message.channel.id, npc_name=target_npc)
                response_text = client.chat(f"{user_name}: {text}")
                
                if target_npc:
                    # 1-on-1 Mode: Force the identity to the target_npc and strip generated prefixes
                    import re
                    # Strips strings like "Selene Varis [EH-29]: ", "**Name**: ", or just "Name: "
                    clean_text = re.sub(r'^(?:\*\*)?[^:\n*]+(?:\[[A-Z0-9-]+\])?(?:\*\*)?:\s*(?:\"\s*)?', '', response_text).strip()
                    
                    # Attempt to lookup identity (User suggestion: use IDs as source of truth)
                    match_key = None
                    
                    # 1. Try extracting ID from topic: "Name [ID]"
                    id_match = re.search(r'\[([A-Z0-9-]+)\]', target_npc)
                    if id_match:
                        token = id_match.group(1)
                        if token in IDENTITIES:
                            match_key = token
                    
                    # 2. Try exact name match if ID lookup fails
                    if not match_key:
                        clean_name = re.sub(r'\s*\[[A-Z0-9-]+\]', '', target_npc).strip()
                        match_key = next((k for k in IDENTITIES if isinstance(k, str) and k.lower() == clean_name.lower()), None)
                    
                    identity = IDENTITIES[match_key] if match_key else {"name": target_npc, "avatar": IDENTITIES.get("NPC", {}).get("avatar")}
                    
                    # Final name cleaning for display (strip [ID] if present)
                    display_name = re.sub(r'\s*\[[A-Z0-9-]+\]', '', identity["name"]).strip()
                    
                    await transport.send(
                        message.channel, clean_text, 
                        username=display_name, avatar_url=identity.get("avatar"), wait=False
                    )
                else:
                    # Parse the response into speaker blocks for multi-character channels
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

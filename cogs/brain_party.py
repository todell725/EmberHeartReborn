"""
cogs/brain_party.py — EmberHeart Party Bot Brain
Handles ONLY #party-chat and #off-topic channels.
Uses JSON-mode AI output + per-NPC webhooks (T2+T3 Architecture).
"""

import os
import re
import logging
import discord
from discord.ext import commands
from pathlib import Path

import sys
core_path = str(Path(__file__).resolve().parent.parent / "core")
if core_path not in sys.path:
    sys.path.insert(0, core_path)

from core.transport import transport
from core.config import IDENTITIES
from core.formatting import strip_god_moding
from core.storage import log_narrative_event
from ai.client import EHClient, PARTY_JSON_SCHEMA

logger = logging.getLogger("Cog_PartyBrain")

# ─── Sovereignty: These names can NEVER appear as speakers ───────────────────
SOVEREIGN_NAMES = {"kaelrath", "king kaelrath", "the king", "sovereign", "king"}

# ─── Party roster for #party-chat (strict) ───────────────────────────────────
PARTY_MEMBERS = {"Talmarr", "Silvara", "Mareth", "Vaelis Thorne", "Vaelis", 'Silvara "Silvy"'}

# ─── Channel names this cog responds to ─────────────────────────────────────
PARTY_CHANNELS = ["party-chat", "off-topic"]


class PartyBrain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # One shared EHClient for the party group context
        # The system prompt includes the JSON schema
        self._client_cache = {}

    def _get_client(self, channel_id: int) -> EHClient:
        if channel_id not in self._client_cache:
            client = EHClient(thread_id=f"party_{channel_id}")
            # Inject JSON schema into the system prompt
            if client.unified_history and client.unified_history[0]["role"] == "system":
                existing = client.unified_history[0]["content"]
                if "RESPONSE FORMAT" not in existing:
                    client.unified_history[0]["content"] = PARTY_JSON_SCHEMA.strip() + "\n\n" + existing
                    client._save_history()
            self._client_cache[channel_id] = client
        return self._client_cache[channel_id]

    def _build_channel_context(self, channel_name: str) -> str:
        """Build the channel-specific context prefix for the AI prompt."""
        if "party-chat" in channel_name:
            return (
                "[CHANNEL: PARTY-CHAT — Private Inner Circle]\n"
                "You are the core party: Talmarr, Silvara, Mareth, and Vaelis Thorne.\n"
                "React naturally to what the King just said. 1-3 of you may respond.\n"
                "Stay in the moment. Internal banter, bonding, and reaction only.\n"
                "Do NOT narrate the King's actions or speak for him."
            )
        elif "off-topic" in channel_name:
            return (
                "[CHANNEL: OFF-TOPIC — Casual World Interaction]\n"
                "Any character from the EmberHeart world may respond here: party members, tavern patrons, guards, merchants — whoever fits the mood.\n"
                "Keep it casual, social, and atmospheric. 1-2 speakers max.\n"
                "Do NOT narrate the King's actions or speak for him."
            )
        return ""

    def _filter_blocks(self, blocks: list, channel_name: str) -> list:
        """Apply sovereignty + channel-specific filters to parsed JSON blocks."""
        valid = []
        for block in blocks:
            speaker = block.get("speaker", "").strip()
            content = block.get("content", "").strip()

            # Sovereignty: never allow the King as a speaker
            if speaker.lower() in SOVEREIGN_NAMES:
                logger.warning(f"BLOCKED sovereign speaker: '{speaker}'")
                continue

            # Party-chat: only known party members allowed
            if "party-chat" in channel_name:
                is_party = any(pm.lower() in speaker.lower() or speaker.lower() in pm.lower() for pm in PARTY_MEMBERS)
                if not is_party:
                    logger.info(f"OFF-ROSTER speaker '{speaker}' skipped in party-chat.")
                    continue

            # Clean content
            content = strip_god_moding(content)
            if not content:
                continue

            valid.append({"speaker": speaker, "content": content})
        return valid

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore self, other bots, webhooks, commands
        if message.author.bot:
            return
        if message.webhook_id:
            return
        if message.content.startswith(self.bot.command_prefix):
            return

        channel_name = getattr(message.channel, "name", "").lower()

        # Only respond in our designated channels
        if not any(name in channel_name for name in PARTY_CHANNELS):
            return

        # Get user name — map owner to Kaelrath
        user_name = message.author.display_name
        is_owner = message.author.name.lower() in ["lamorte725", "todd"]
        if is_owner:
            user_name = "King Kaelrath"

        text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        if not text:
            return

        channel_context = self._build_channel_context(channel_name)
        full_message = f"{channel_context}\n\n{user_name}: {text}" if channel_context else f"{user_name}: {text}"

        logger.info(f"[PartyBrain] #{channel_name} | {user_name}: {text[:60]}...")

        async with message.channel.typing():
            try:
                client = self._get_client(message.channel.id)

                # Use JSON mode
                response_text = client.chat_json(full_message)
                logger.debug(f"[PartyBrain] Raw response: {response_text[:200]}")

                # Parse the JSON response
                blocks = client.parse_response(response_text)

                # Apply sovereignty + channel filters
                blocks = self._filter_blocks(blocks, channel_name)

                if not blocks:
                    logger.warning(f"[PartyBrain] No valid blocks after filtering for #{channel_name}. Raw: {response_text[:100]}")
                    return

                # Route each block to its NPC webhook
                for block in blocks:
                    speaker = block["speaker"]
                    content = block["content"]

                    # Look up avatar
                    identity = IDENTITIES.get(speaker)
                    if not identity:
                        match = next((k for k in IDENTITIES if isinstance(k, str) and k.lower() == speaker.lower()), None)
                        if match:
                            identity = IDENTITIES[match]
                    avatar_url = identity.get("avatar") if identity else None

                    await transport.send_as_npc(message.channel, speaker, content, avatar_url)
                    # Brief pause between multiple speakers for natural pacing
                    if len(blocks) > 1:
                        import asyncio
                        await asyncio.sleep(0.8)

                # Log narrative pulse
                if len(response_text) > 50:
                    chan_label = f"#{message.channel.name}"
                    speakers = ", ".join(list(dict.fromkeys([b["speaker"] for b in blocks])))
                    log_narrative_event(f"{user_name} and {speakers} chatted in {chan_label}.")

            except Exception as e:
                logger.error(f"[PartyBrain] AI Generation Failed: {e}", exc_info=True)
                await message.channel.send(f"❌ *The party seems distracted...* ({e})")

    @commands.command(name="pclear")
    async def pclear(self, ctx):
        """Wipes the Party Brain's memory for this channel."""
        channel_id = ctx.channel.id
        if channel_id in self._client_cache:
            self._client_cache[channel_id].clear_history()
            del self._client_cache[channel_id]
        await transport.send(ctx.channel, "🧹 **Party memory cleared.** Fresh start.", identity_key="DM")


async def setup(bot):
    await bot.add_cog(PartyBrain(bot))

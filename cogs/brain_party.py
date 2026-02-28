"""
cogs/brain_party.py - EmberHeart Party Bot Brain
Handles ONLY #party-chat and #off-topic channels.
Uses prose output + per-NPC webhooks (T2+T3 Architecture).
"""

import os
import re
import asyncio
import logging
from discord.ext import commands

from core.transport import transport
from core.config import list_identity_roster, normalize_identity_id, resolve_identity
from core.formatting import strip_god_moding
from core.storage import log_narrative_event
from core.ai.client import EHClient

logger = logging.getLogger("Cog_PartyBrain")

# Sovereignty: these names/IDs can never appear as speakers
SOVEREIGN_NAMES = {"kaelrath", "king kaelrath", "the king", "sovereign", "king"}
SOVEREIGN_IDS = {"PC-01"}

# Canonical party roster (all PCs except the Sovereign)
_PARTY_ROSTER = list_identity_roster(prefixes={"PC"}, exclude_ids=SOVEREIGN_IDS)
PARTY_ID_TO_NAME = {row["id"]: row["name"] for row in _PARTY_ROSTER}
PARTY_MEMBER_IDS = set(PARTY_ID_TO_NAME.keys())

# Name aliases for fallback resolution when model misses an ID
PARTY_CANONICAL = {
    "talmarr": "Talmarr",
    "silvara": 'Silvara "Silvy"',
    "silvy": 'Silvara "Silvy"',
    'silvara "silvy"': 'Silvara "Silvy"',
    "mareth": "Mareth",
    "vaelis": "Vaelis Thorne",
    "vaelis thorne": "Vaelis Thorne",
}

PARTY_CHANNELS = ["party-chat", "off-topic"]
AI_JSON_TIMEOUT_SECONDS = float(os.getenv("AI_JSON_TIMEOUT_SECONDS", os.getenv("AI_CALL_TIMEOUT_SECONDS", "130")))


class PartyBrain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._client_cache = {}

    def _get_client(self, channel_id: int) -> EHClient:
        if channel_id not in self._client_cache:
            client = EHClient(thread_id=f"party_{channel_id}")

            self._client_cache[channel_id] = client
        return self._client_cache[channel_id]

    def _party_roster_context(self) -> str:
        if not _PARTY_ROSTER:
            return ""
        lines = [f"- {row['id']}: {row['name']}" for row in _PARTY_ROSTER]
        return "\n".join(lines)

    def _build_channel_context(self, channel_name: str) -> str:
        party_roster = self._party_roster_context()

        if "party-chat" in channel_name:
            return (
                "[CHANNEL: PARTY-CHAT - Private Inner Circle]\n"
                "You are the core party responding to King Kaelrath.\n"
                "React naturally. 1-3 of you may respond.\n"
                "Stay in the moment. Internal banter, bonding, and reaction only.\n"
                "Do NOT narrate the King's actions or speak for him.\n"
                "Format each response block as **Name [ID]**: content.\n"
                f"Use this roster for valid names/IDs:\n{party_roster}"
            )

        if "off-topic" in channel_name:
            return (
                "[CHANNEL: OFF-TOPIC - Casual World Interaction]\n"
                "Any character from the EmberHeart world may respond here.\n"
                "Keep it casual, social, and atmospheric. 1-2 speakers max.\n"
                "Do NOT narrate the King's actions or speak for him.\n"
                "When possible, format as **Name [ID]**: content."
            )

        return ""

    def _extract_speaker_id(self, block: dict) -> str:
        if not isinstance(block, dict):
            return ""
        raw_id = block.get("speaker_id") or block.get("identity_id") or block.get("id") or ""
        if not raw_id:
            raw_id = block.get("speaker", "")
        return normalize_identity_id(str(raw_id))

    def _canonical_party_speaker(self, speaker: str, speaker_id: str):
        """Resolve canonical party speaker name using ID-first identity routing."""
        token, canonical_name, canonical_id = resolve_identity(speaker=speaker, speaker_id=speaker_id)

        if canonical_id in PARTY_ID_TO_NAME:
            return PARTY_ID_TO_NAME[canonical_id], canonical_id, token

        # Name fallback for malformed model output
        clean = re.sub(r"\[[^\]]+\]", "", str(speaker or ""))
        clean = re.sub(r"\b(?:EH|PC|DM)-?\d+\b", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s+", " ", clean).strip(" :-\t\n\r")
        low = clean.lower()

        if low in PARTY_CANONICAL:
            guessed_name = PARTY_CANONICAL[low]
            token, canonical_name, canonical_id = resolve_identity(speaker=guessed_name, speaker_id="")
            if canonical_id in PARTY_ID_TO_NAME:
                return PARTY_ID_TO_NAME[canonical_id], canonical_id, token
            return guessed_name, canonical_id, token

        return canonical_name or clean, canonical_id, token

    def _filter_blocks(self, blocks: list, channel_name: str) -> list:
        valid = []

        for block in blocks:
            raw_speaker = str(block.get("speaker", "")).strip()
            raw_id = self._extract_speaker_id(block)

            speaker, speaker_id, identity = self._canonical_party_speaker(raw_speaker, raw_id)
            content = str(block.get("content", "")).strip()

            if speaker.lower() in SOVEREIGN_NAMES or speaker_id in SOVEREIGN_IDS:
                logger.warning("BLOCKED sovereign speaker: '%s' (%s)", raw_speaker, speaker_id)
                continue

            if "party-chat" in channel_name:
                if speaker_id not in PARTY_MEMBER_IDS:
                    logger.info(
                        "OFF-ROSTER speaker '%s' id='%s' -> '%s' skipped in party-chat.",
                        raw_speaker,
                        raw_id,
                        speaker,
                    )
                    continue

            content = strip_god_moding(content)
            if not content:
                continue

            payload = {"speaker": speaker, "content": content}
            if speaker_id:
                payload["speaker_id"] = speaker_id
            if isinstance(identity, dict):
                payload["identity"] = identity
            valid.append(payload)

        return valid

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.webhook_id:
            return
        if message.content.startswith(self.bot.command_prefix):
            return

        channel_name = getattr(message.channel, "name", "").lower()
        if not any(name in channel_name for name in PARTY_CHANNELS):
            return

        user_name = message.author.display_name
        is_owner = message.author.name.lower() in ["lamorte725", "todd"]
        if is_owner:
            user_name = "King Kaelrath"

        text = message.clean_content.replace(f"@{self.bot.user.display_name}", "").strip()
        if not text:
            return

        channel_context = self._build_channel_context(channel_name)
        full_message = f"{channel_context}\n\n{user_name}: {text}" if channel_context else f"{user_name}: {text}"

        logger.info(f"[PartyBrain] #{channel_name} | {user_name}: {text[:60]}...")

        async with message.channel.typing():
            try:
                client = self._get_client(message.channel.id)
                response_text = await asyncio.wait_for(
                    asyncio.to_thread(client.chat_json, full_message),
                    timeout=AI_JSON_TIMEOUT_SECONDS,
                )
                logger.debug(f"[PartyBrain] Raw response: {response_text[:200]}")

                blocks = client.parse_response(response_text)
                blocks = self._filter_blocks(blocks, channel_name)

                if not blocks:
                    logger.warning(f"[PartyBrain] No valid blocks after filtering for #{channel_name}. Raw: {response_text[:100]}")
                    return

                for idx, block in enumerate(blocks):
                    speaker = block["speaker"]
                    content = block["content"]

                    identity = block.get("identity") if isinstance(block.get("identity"), dict) else None
                    if not identity:
                        identity, canonical_name, canonical_id = resolve_identity(
                            speaker=speaker,
                            speaker_id=block.get("speaker_id", ""),
                        )
                        if canonical_name:
                            speaker = canonical_name
                        if canonical_id:
                            block["speaker_id"] = canonical_id

                    avatar_url = identity.get("avatar") if identity else None

                    await transport.send_as_npc(message.channel, speaker, content, avatar_url)
                    if idx < len(blocks) - 1:
                        await asyncio.sleep(0.8)

                if len(response_text) > 50:
                    chan_label = f"#{message.channel.name}"
                    speakers = ", ".join(list(dict.fromkeys([b["speaker"] for b in blocks])))
                    log_narrative_event(f"{user_name} and {speakers} chatted in {chan_label}.")

            except asyncio.TimeoutError:
                logger.error(
                    "[PartyBrain] AI generation timed out after %.1fs in #%s",
                    AI_JSON_TIMEOUT_SECONDS,
                    channel_name,
                )
                await message.channel.send("[PartyBrain] The party is taking too long to respond. Try again in a moment.")
            except Exception as e:
                logger.error(f"[PartyBrain] AI Generation Failed: {e}", exc_info=True)
                await message.channel.send(f"[PartyBrain] The party seems distracted... ({e})")

    @commands.command(name="pclear")
    async def pclear(self, ctx):
        """Wipes the Party Brain's memory for this channel."""
        channel_id = ctx.channel.id
        if channel_id in self._client_cache:
            self._client_cache[channel_id].clear_history()
            del self._client_cache[channel_id]
        await transport.send(ctx.channel, "Party memory cleared. Fresh start.", identity_key="DM")


async def setup(bot):
    await bot.add_cog(PartyBrain(bot))

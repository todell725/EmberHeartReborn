import os
import asyncio
import logging
import discord
from discord.ext import commands
from pathlib import Path

from core.transport import transport
from core.config import IDENTITIES, list_identity_roster, normalize_identity_id, resolve_identity
from core.formatting import parse_speaker_blocks, IGNORE_SPEAKERS, strip_god_moding

# Import the refactored AI Core we built in Phase 1
import sys
core_path = str(Path(__file__).resolve().parent.parent / "core")
if core_path not in sys.path:
    sys.path.insert(0, core_path)
from ai.client import EHClient

logger = logging.getLogger("Cog_Brain")
ALLOWED_CHANNEL_ID = os.getenv("DISCORD_ALLOWED_CHANNEL_ID")
AI_CALL_TIMEOUT_SECONDS = float(os.getenv("AI_CALL_TIMEOUT_SECONDS", "130"))

SCENE_JSON_SCHEMA = """
### RESPONSE FORMAT (MANDATORY):
You MUST respond with a valid JSON array and NOTHING ELSE.
Schema: [{"speaker_id": "EH-01", "speaker": "Marta Hale", "content": "Their dialogue or action text"}]
- Include 1-3 speakers who naturally fit the channel and moment.
- NEVER include King Kaelrath as a speaker.
- `speaker_id` is REQUIRED for each block and must come from the allowed roster in context.
- `speaker` must match the canonical name for that ID.
- Do NOT invent IDs.
"""

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
        # Ensure the client is instantiated (loads disk history) before wiping it
        client = self.get_client(channel_id)
        client.clear_history()

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

        # Shared ID-lock roster for non-party multi-speaker channels.
        self.scene_roster = list_identity_roster(prefixes={"EH", "PC", "DM"}, exclude_ids={"PC-01"})
        self.scene_roster_text = "\n".join([f"- {r['id']}: {r['name']}" for r in self.scene_roster])

    def _build_scene_id_context(self, channel_name: str, target_npc: str) -> str:
        """Inject ID roster so AI can emit speaker_id deterministically."""
        target_token, target_name, target_id = resolve_identity(speaker=target_npc or "", speaker_id="")

        if target_id:
            return (
                "[ID LOCK]\n"
                f"Allowed speaker for this turn:\n- {target_id}: {target_name}\n"
                "Return exactly 1 block for that speaker_id."
            )

        # Rumor mill is a synthetic identity without numeric ID. Keep name-lock fallback.
        if target_token and not target_id:
            return (
                "[ID LOCK]\n"
                f"You are speaking as: {target_name}.\n"
                "If no numeric ID exists, keep speaker name exact and consistent."
            )

        roster = self.scene_roster_text
        if not roster:
            roster = "- EH-01: Marta Hale"

        return (
            "[ID LOCK]\n"
            "Use ONLY speaker_id values from this roster:\n"
            f"{roster}\n"
            "Every block must include speaker_id + matching speaker name."
        )

    def _normalize_json_blocks(self, blocks: list, user_name: str, display_name: str, target_npc: str, channel_name: str) -> list:
        """Normalize parsed blocks to canonical names/IDs and enforce ID-lock rules."""
        normalized = []
        restricted_speakers = {str(s).lower() for s in (IGNORE_SPEAKERS | {user_name, display_name})}
        sovereign_names = {"kaelrath", "king kaelrath", "the king", "sovereign", "king"}

        target_token, target_name, target_id = resolve_identity(speaker=target_npc or "", speaker_id="")
        target_name_low = str(target_name or "").strip().lower()

        for raw in blocks:
            raw_speaker = str(raw.get("speaker", "")).strip()
            raw_content = str(raw.get("content", "")).strip()
            if not raw_content:
                continue

            raw_id = raw.get("speaker_id") or raw.get("identity_id") or raw.get("id") or ""
            parsed_id = normalize_identity_id(str(raw_id))
            if not parsed_id:
                parsed_id = normalize_identity_id(raw_speaker)

            token, canonical_name, canonical_id = resolve_identity(speaker=raw_speaker, speaker_id=parsed_id)
            speaker = canonical_name or raw_speaker
            speaker_low = speaker.lower()

            if speaker_low in restricted_speakers or speaker_low in sovereign_names or canonical_id == "PC-01":
                continue

            # For ID-lock parity, non-weaver multi-speaker output must resolve to a numeric ID.
            # Synthetic identities (e.g., Rumor Mill) are exempt if explicitly targeted.
            if not canonical_id:
                if not (target_token and not target_id and target_name_low and speaker_low == target_name_low):
                    logger.info("ID-LOCK skip unresolved speaker '%s' in #%s", raw_speaker, channel_name)
                    continue

            if target_npc:
                if target_id and canonical_id and canonical_id != target_id:
                    continue
                if target_id and not canonical_id:
                    continue
                if not target_id and target_name_low and target_name_low != "the character you are speaking to":
                    if speaker_low != target_name_low and target_name_low not in speaker_low and speaker_low not in target_name_low:
                        continue

            content = strip_god_moding(raw_content)
            if not content:
                continue

            row = {
                "speaker": speaker,
                "content": content,
                "identity": token,
            }
            if canonical_id:
                row["speaker_id"] = canonical_id

            normalized.append(row)

        return normalized

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
        # NOTE: party-chat, off-topic, and weaver-archives are handled by the Party Bot (discord_party.py)
        allowed_names = ["npc-chat", "game-feed", "campaign-chat", "rumors-chat"]
        channel_name = getattr(message.channel, "name", "").lower()

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_named_whitelist = any(name in channel_name for name in allowed_names) or channel_name.startswith("dm-")
        is_hard_whitelist = str(message.channel.id) == ALLOWED_CHANNEL_ID
        is_mentioned = self.bot.user in message.mentions

        logger.info(
            f"MSG: #{channel_name} ({message.channel.id}) | Whitelist: {is_named_whitelist} | Hard: {is_hard_whitelist} | Mention: {is_mentioned}"
        )

        if not (is_dm or is_named_whitelist or is_hard_whitelist):
            if not is_mentioned:
                return

        # Specifically defer party/meta channels to Party Bot unless explicitly mentioned
        reserved_channels = ["party-chat", "off-topic", "weaver-archives"]
        if any(res in channel_name for res in reserved_channels) and not is_mentioned:
            return

        user_name = message.author.display_name
        is_owner = message.author.name.lower() in ["lamorte725", "todd"]
        if is_owner:
            user_name = "King Kaelrath"

        text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        if not text:
            return

        target_npc = None
        channel_context = ""

        if "rumors-chat" in channel_name:
            target_npc = "RUMORS"
            channel_context = "[CHANNEL: RUMORS-CHAT] Provide rumors, hooks, or news. Be atmospheric and mysterious."
        elif "campaign-chat" in channel_name:
            channel_context = "[CHANNEL: CAMPAIGN-CHAT] Progress the main storyline and provide narrative momentum."

        if channel_name.startswith("dm-"):
            target_npc = (getattr(message.channel, "topic", "") or "").strip()
            if not target_npc:
                target_npc = "the character you are speaking to"

        # Mentions in whitelisted channels can also set target_npc for that turn
        if not target_npc and (is_named_whitelist or is_hard_whitelist):
            mentioned_npcs = []
            for mention in message.mentions:
                token, canonical_name, canonical_id = resolve_identity(
                    speaker=mention.display_name,
                    speaker_id="",
                )
                if not token:
                    token, canonical_name, canonical_id = resolve_identity(
                        speaker=mention.name,
                        speaker_id="",
                    )
                if token:
                    mentioned_npcs.append((canonical_name, canonical_id))

            if len(mentioned_npcs) == 1:
                m_name, m_id = mentioned_npcs[0]
                target_npc = f"{m_name} [{m_id}]" if m_id else m_name

        async with message.channel.typing():
            try:
                client = self.brain_manager.get_client(message.channel.id, npc_name=target_npc)

                is_weaver = "weaver-archives" in channel_name
                if is_weaver:
                    client.apply_weaver_mode()

                id_lock_context = "" if is_weaver else self._build_scene_id_context(channel_name, target_npc)
                schema_context = "" if is_weaver else SCENE_JSON_SCHEMA.strip()

                parts = [p for p in [channel_context, schema_context, id_lock_context, f"{user_name}: {text}"] if p]
                full_message = "\n\n".join(parts)

                m_type = "reasoning" if is_weaver else "rp"

                if is_weaver:
                    response_text = await asyncio.wait_for(
                        asyncio.to_thread(client.chat, full_message, m_type),
                        timeout=AI_CALL_TIMEOUT_SECONDS,
                    )
                    raw_blocks = parse_speaker_blocks(response_text, IDENTITIES, self.ignore_headers)
                    blocks = []
                    for b in raw_blocks:
                        speaker = str(b.get("speaker", "")).strip()
                        content = str(b.get("content", "")).strip()
                        if not speaker or not content:
                            continue
                        identity = b.get("identity") if isinstance(b.get("identity"), dict) else None
                        canonical_id = ""
                        if identity:
                            canonical_id = normalize_identity_id(identity.get("id", ""))
                        if not identity:
                            identity, canonical_name, canonical_id = resolve_identity(speaker=speaker, speaker_id="")
                            if canonical_name:
                                speaker = canonical_name
                        row = {"speaker": speaker, "content": content, "identity": identity}
                        if canonical_id:
                            row["speaker_id"] = canonical_id
                        blocks.append(row)
                else:
                    response_text = await asyncio.wait_for(
                        asyncio.to_thread(client.chat_json, full_message, m_type),
                        timeout=AI_CALL_TIMEOUT_SECONDS,
                    )
                    raw_blocks = client.parse_response(response_text)
                    blocks = self._normalize_json_blocks(
                        raw_blocks,
                        user_name=user_name,
                        display_name=message.author.display_name,
                        target_npc=target_npc,
                        channel_name=channel_name,
                    )

                    if not blocks:
                        salvaged = parse_speaker_blocks(response_text, IDENTITIES, self.ignore_headers)
                        salvage_payload = [
                            {"speaker": b.get("speaker", ""), "content": b.get("content", "")}
                            for b in salvaged
                        ]
                        blocks = self._normalize_json_blocks(
                            salvage_payload,
                            user_name=user_name,
                            display_name=message.author.display_name,
                            target_npc=target_npc,
                            channel_name=channel_name,
                        )

                if not blocks:
                    logger.warning(f"BLOCK FILTER: No blocks survived for {channel_name}. Response text: {response_text[:100]}...")
                    return

                for idx, block in enumerate(blocks):
                    speaker_name = str(block.get("speaker", "")).strip()
                    content = strip_god_moding(str(block.get("content", "")).strip())
                    identity = block.get("identity") if isinstance(block.get("identity"), dict) else None

                    if not content:
                        continue

                    if not identity:
                        identity, canonical_name, canonical_id = resolve_identity(
                            speaker=speaker_name,
                            speaker_id=block.get("speaker_id", ""),
                        )
                        if canonical_name:
                            speaker_name = canonical_name
                        if canonical_id:
                            block["speaker_id"] = canonical_id

                    wait = idx < len(blocks) - 1

                    if identity:
                        await transport.send_as_npc(
                            message.channel,
                            npc_name=speaker_name,
                            content=content,
                            avatar_url=identity.get("avatar"),
                            wait=wait,
                        )
                        if wait:
                            await asyncio.sleep(0.75)
                    else:
                        await transport.send(message.channel, content, identity_key="DM", wait=wait)

                if len(response_text) > 50 and "weaver-archives" not in channel_name:
                    chan_label = f"#{message.channel.name}" if hasattr(message.channel, "name") else "DMs"
                    summary = f"{user_name} interacted in {chan_label}."
                    if len(blocks) > 0:
                        speakers = ", ".join(list(set([b["speaker"] for b in blocks if b.get("speaker")])))
                        summary = f"{user_name} and {speakers} discussed matters in {chan_label}."

                    from core.storage import log_narrative_event
                    log_narrative_event(summary)

            except asyncio.TimeoutError:
                logger.error(
                    "AI Generation timed out after %.1fs in #%s",
                    AI_CALL_TIMEOUT_SECONDS,
                    channel_name,
                )
                await message.channel.send("The Chronicle is taking too long to answer. Try again in a moment.")
            except Exception as e:
                logger.error(f"AI Generation Failed: {e}", exc_info=True)
                await message.channel.send(f"A temporal anomaly disrupts the Chronicle... ({e})")

    @commands.command(name="clear", aliases=["reset"])
    async def clear(self, ctx, message_id: int = None):
        """Wipes AI memory or rolls back to a specific message. !clear [ID] to rollback."""
        channel_id = ctx.channel.id
        channel_label = f"#{ctx.channel.name}" if hasattr(ctx.channel, "name") else "DMs"
        
        try:
            client = self.brain_manager.get_client(channel_id)
            
            if message_id:
                # 1. Fetch target message
                try:
                    target_msg = await ctx.channel.fetch_message(message_id)
                except discord.NotFound:
                    await transport.send(ctx.channel, f"**Error:** Message `{message_id}` not found in this channel.", identity_key="DM")
                    return

                # 2. Priority Discord Purge: Delete everything AFTER the target message
                # We do this first so the channel looks right immediately
                deleted = await ctx.channel.purge(after=target_msg, limit=500)
                
                # 3. Synchronize AI Memory
                # Attempt rollback using content matching
                success = client.rollback_to_id(message_id, target_msg.content)
                
                status_msg = f"**Chronicle Rolled Back:** Discord history cleared after `{message_id}` ({len(deleted)} messages)."
                
                if success:
                    status_msg += "\nAI internal memory successfully synced with rollback."
                else:
                    # FALLBACK: If rollback failed, rebuild from the remaining history
                    # We fetch last 10 messages (including the target message)
                    messages = []
                    async for m in ctx.channel.history(limit=11):
                        if m.id <= target_msg.id: # Include target and things before it
                            messages.append(m)
                    
                    # Reverse to chronological
                    messages.reverse()
                    client.rebuild_from_messages(messages)
                    status_msg += f"\nAI memory resynced by rebuilding context from the last {len(messages)} surviving messages."
                
                from core.storage import log_narrative_event
                log_narrative_event(f"The Chronicle of {channel_label} was rolled back to message {message_id}.")
                
                await transport.send(ctx.channel, status_msg, identity_key="DM")
            else:
                # Full wipe
                self.brain_manager.reset_client(channel_id)
                from core.storage import log_narrative_event
                log_narrative_event(f"The Chronicle's local memory of {channel_label} was reset.")
                await transport.send(ctx.channel, f"**Memory Cleared:** The AI's local context for {channel_label} has been wiped.", identity_key="DM")
                
        except Exception as e:
            logger.error(f"Clear command error: {e}", exc_info=True)
            await transport.send(ctx.channel, f"Error during clear: {e}")

    @commands.command(name="refresh")
    async def refresh(self, ctx, limit: int = 10):
        """Rebuilds the AI's internal context from the last [limit] messages."""
        channel_id = ctx.channel.id
        channel_label = f"#{ctx.channel.name}" if hasattr(ctx.channel, "name") else "DMs"
        
        try:
            async with ctx.channel.typing():
                # Fetch recent history (excluding the command itself)
                messages = []
                async for m in ctx.channel.history(limit=limit + 1):
                    if m.id != ctx.message.id:
                        messages.append(m)
                
                # Reverse to get chronological order
                messages.reverse()
                
                client = self.brain_manager.get_client(channel_id)
                client.rebuild_from_messages(messages)
                
                from core.storage import log_narrative_event
                log_narrative_event(f"The Chronicle of {channel_label} was refreshed from channel history.")
                
                await transport.send(ctx.channel, f"**Context Refreshed:** History rebuilt from the last {len(messages)} messages.", identity_key="DM")
        except Exception as e:
            logger.error(f"Refresh command error: {e}", exc_info=True)
            await transport.send(ctx.channel, f"Error during refresh: {e}")

    @commands.command(name="pulse")
    async def pulse(self, ctx, *, manual_event: str = None):
        """Force a refresh of the narrative pulse or manually log a global event. !pulse [text] to save."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        try:
            from core.storage import DB_DIR, log_narrative_event
            
            if manual_event:
                log_narrative_event(f"MANUAL: {manual_event}")
                from core.transport import transport
                await transport.send(channel, "**Chronicle Updated:** Recorded manual entry.", identity_key="DM")
                return

            log_path = DB_DIR / "NARRATIVE_LOG.md"
            if not log_path.exists():
                await transport.send(channel, "**Narrative Pulse is silent.** No global events recorded yet.", identity_key="DM")
                return
                
            lines = log_path.read_text(encoding='utf-8').splitlines()
            recent = lines[-5:]
            
            msg = ["**Global Narrative Pulse (Latest Events)**"]
            msg.extend(recent)
            msg.append("\n*The Chronicle remains synchronized across all channels.*")
            
            from core.transport import transport
            await transport.send(channel, "\n".join(msg), identity_key="DM")
        except Exception as e:
            from core.transport import transport
            await transport.send(channel, f"Error checking pulse: {e}")

async def setup(bot):
    await bot.add_cog(BrainCog(bot))

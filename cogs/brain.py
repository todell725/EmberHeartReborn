import os
import re
import logging
import discord
from discord.ext import commands
from pathlib import Path

from core.transport import transport
from core.config import IDENTITIES
from core.formatting import parse_speaker_blocks, IGNORE_SPEAKERS, strip_god_moding

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
        allowed_names = ["npc-chat", "party-chat", "game-feed", "campaign-chat", "rumors-chat", "off-topic", "weaver-archives"]
        channel_name = getattr(message.channel, "name", "").lower()

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_named_whitelist = any(name in channel_name for name in allowed_names) or channel_name.startswith("dm-")
        is_hard_whitelist = str(message.channel.id) == ALLOWED_CHANNEL_ID
        is_mentioned = self.bot.user in message.mentions

        logger.info(f"MSG: #{channel_name} ({message.channel.id}) | Whitelist: {is_named_whitelist} | Hard: {is_hard_whitelist} | Mention: {is_mentioned}")

        if not (is_dm or is_named_whitelist or is_hard_whitelist):
            if not is_mentioned:
                return
        
        user_name = message.author.display_name
        # --- Sovereign Identity Mapping ---
        # Ensure the owner is known by their narrative name in all specialized channels
        is_owner = message.author.name.lower() in ["lamorte725", "todd"]
        if is_owner:
            user_name = "King Kaelrath"
            
        text = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
        
        if not text:
            return

        # --- Specialized Channel Handling ---
        target_npc = None
        channel_context = ""
        
        if "rumors-chat" in channel_name:
            target_npc = "RUMORS"
            channel_context = "[CHANNEL: RUMORS-CHAT] Provide rumors, hooks, or news. Be atmospheric and mysterious."
        elif "off-topic" in channel_name:
            channel_context = (
                "[CHANNEL: OFF-TOPIC/CASUAL-RP] Focus on character flavor, social interaction, and atmosphere. "
                "Do NOT push the main campaign plot. Stay in the moment.\n"
                "### DIALOGUE SOVEREIGNTY: NEVER speak for, describe the actions of, or narrate the internal state of King Kaelrath (the user).\n"
                "### FORMATTING: You MUST use the **Name**: \"Dialogue\" format for ALL NPCs and PC companions. Do NOT provide third-person prose summaries or book-style narration describing multiple people at once. Focus on one-at-a-time interaction."
            )
        elif "campaign-chat" in channel_name:
            channel_context = "[CHANNEL: CAMPAIGN-CHAT] Progress the main storyline and provide narrative momentum."
        elif "party-chat" in channel_name:
            channel_context = (
                "[CHANNEL: PARTY-CHAT] This is the private, internal communication and banter of the core party (King Kaelrath, Talmarr, Silvara, Mareth, and Vaelis Thorne). It is your 'Private Circle' chat.\n"
                "### RULES:\n"
                "1. PRIVATE CIRCLE: This is for internal bonding, processing info, and lateral discussion. Do NOT push for the next campaign goal or mission unless Kaelrath explicitly asks for a direction. Stay in the moment.\n"
                "2. ACTIVE LISTENING: If Kaelrath provides information, updates, or ideas, you MUST acknowledge and analyze the specific details. Do not brush past 'info relay' to get to the action.\n"
                "3. NO EXTERNALS: Even if the King addresses an NPC directly, that NPC cannot speak here.\n"
                "4. NO SUMMARIES: Do NOT provide third-person narration or 'Book-style' prose. You are the characters themselves.\n"
                "5. MANDATORY FORMATTING: Each party member MUST speak in their own individual block using the **Name**: \"Dialogue\" format.\n"
                "6. SOVEREIGNTY: NEVER speak for King Kaelrath. Reaction ONLY."
            )
        elif "weaver-archives" in channel_name:
            target_npc = "The Chronicle Weaver"
            channel_context = "[META-CHANNEL: WEAVER-ARCHIVES] Direct system access for King Kaelrath. No immersion masking required."

        # --- Dynamic DM Context Injection ---
        if channel_name.startswith("dm-"):
            target_npc = (getattr(message.channel, "topic", "") or "").strip()
            if not target_npc:
                target_npc = "the character you are speaking to"
        
        # Mentions in whitelisted channels can also set target_npc for that turn
        if not target_npc and (is_named_whitelist or is_hard_whitelist):
            # Check for mentions of NPCs in IDENTITIES
            mentioned_npcs = []
            for mention in message.mentions:
                # Check display name and name
                if mention.display_name in IDENTITIES or mention.name in IDENTITIES:
                    mentioned_npcs.append(mention.display_name)
            
            if len(mentioned_npcs) == 1:
                m_name = mentioned_npcs[0]
                # Try to find the [ID] version for better prompt lookup
                match = next((k for k in IDENTITIES if isinstance(k, str) and m_name.lower() in k.lower() and "[" in k), None)
                target_npc = match if match else m_name

        # Process the chat turn
        async with message.channel.typing():
            try:
                client = self.brain_manager.get_client(message.channel.id, npc_name=target_npc)
                
                # Special Case: Weaver Archives Meta-Awareness
                if "weaver-archives" in channel_name:
                    client.apply_weaver_mode()

                full_message = f"{channel_context}\n\n{user_name}: {text}" if channel_context else f"{user_name}: {text}"
                
                response_text = client.chat(full_message)
                
                # --- Unified Speaker Parsing ---
                # We always parse speaker blocks to catch "hallucinated" extra NPCs or narrator tags
                blocks = parse_speaker_blocks(response_text, IDENTITIES, self.ignore_headers)
                
                # Filter restricted speakers (Sovereignty Check)
                restricted_speakers = IGNORE_SPEAKERS | {user_name, message.author.display_name}
                logger.info(f"Raw Blocks: {[b['speaker'] for b in blocks]} | Restricted: {restricted_speakers}")
                
                # SPECIAL CASE: weaver-archives is transparent. We don't filter it.
                if "weaver-archives" in channel_name:
                    # Identity for Weaver is enforced later if blocks match, 
                    # but we allow all blocks to pass here for meta-transparency.
                    pass 
                else:
                    blocks = [b for b in blocks if b['speaker'] not in restricted_speakers]
                
                if target_npc:
                    # 1-on-1 ENFORCEMENT:
                    # If we are in a targeted DM, we only want blocks matching the target_npc.
                    target_name = re.sub(r'\s*\[[A-Z0-9-]+\]', '', target_npc).strip()
                    character_blocks = [b for b in blocks if target_name.lower() in b['speaker'].lower()]
                    
                    if character_blocks:
                        blocks = character_blocks
                    else:
                        # Fallback for Weaver or DM if no specific character blocks found
                        is_weaver = "weaver-archives" in channel_name
                        if is_weaver:
                             # Keep all blocks in Weaver mode
                             pass
                        elif len(blocks) == 1 and (blocks[0]['speaker'] == "DM" or blocks[0]['speaker'] == "Chronicle Weaver"):
                            blocks[0]['speaker'] = target_name # Re-assign to target
                        else:
                            valid_blocks = [b for b in blocks if b['speaker'] != "DM" and b['speaker'] != "Chronicle Weaver"]
                            if valid_blocks:
                                blocks = [valid_blocks[0]]
                else:
                    # PC-Only Lockdown for party-chat
                    if "party-chat" in channel_name:
                        allowed_pcs = {"Talmarr", "Silvara", "Mareth", "Vaelis Thorne", "Vaelis"}
                        pc_blocks = [b for b in blocks if any(pc.lower() in b['speaker'].lower() for pc in allowed_pcs)]
                        if pc_blocks:
                            blocks = pc_blocks
                        # If no PC blocks, allow DM narration as fallback so the bot isn't silent
                        else:
                            blocks = [b for b in blocks if b['speaker'] == "DM"]
                
                if not blocks:
                    logger.warning(f"BLOCK FILTER: No blocks survived for {channel_name}. Response text: {response_text[:100]}...")
                    return # No valid dialogue generated

                # --- Auto-Targeting & Narrator Suppression (Phase 10 Extension) ---
                if not target_npc and "off-topic" in channel_name:
                    # If we have NPC dialogue + DM narration, drop the narration to stay in character
                    npc_blocks = [b for b in blocks if not any(x in b['speaker'] for x in ["DM", "Chronicle", "Weaver"])]
                    if npc_blocks:
                        # Suppress the narrator if there is actual character dialogue in off-topic
                        blocks = npc_blocks
                    
                    # If only one NPC is left, treat it as a "Soft Target" for display cleaning
                    if len(blocks) == 1:
                        target_npc = blocks[0]['speaker']
                    
                for idx, block in enumerate(blocks):
                    speaker_name = block["speaker"]
                    identity = block["identity"]
                    content = strip_god_moding(block["content"])
                    
                    if not content:
                        continue # Entire sentence was god-moding
                    
                    # 1-on-1 Mode Override: Force identity if we know who we are talking to
                    if target_npc:
                        # Try to resolve identity once for the whole message
                        id_match = re.search(r'\[([A-Z0-9-]+)\]', target_npc)
                        token = None
                        if id_match and id_match.group(1) in IDENTITIES:
                            token = IDENTITIES[id_match.group(1)]
                        
                        if not token:
                            clean_name = re.sub(r'\s*\[[A-Z0-9-]+\]', '', target_npc).strip()
                            match_key = next((k for k in IDENTITIES if isinstance(k, str) and k.lower() == clean_name.lower()), None)
                            token = IDENTITIES[match_key] if match_key else None
                            
                        if token:
                            identity = token
                            display_name = re.sub(r'\s*\[[A-Z0-9-]+\]', '', token["name"]).strip()
                            speaker_name = display_name
                    
                    # The last block shouldn't 'wait' so the next user msg isn't bottlenecked
                    wait = (idx < len(blocks) - 1)
                    
                    if identity:
                        await transport.send(
                            message.channel, content, 
                            username=identity["name"] if not target_npc else speaker_name, 
                            avatar_url=identity.get("avatar"), wait=wait
                        )
                    else:
                        # Fallback to DM profile
                        await transport.send(message.channel, content, identity_key="DM", wait=wait)
                    
                    # --- Narrative Pulse Logging ---
                    # Log a summary of this interaction if it's substantial
                    # EXCLUSION: weaver-archives is outside the campaign plot.
                    if len(response_text) > 50 and "weaver-archives" not in channel_name:
                        chan_label = f"#{message.channel.name}" if hasattr(message.channel, "name") else "DMs"
                        summary = f"{user_name} interacted in {chan_label}."
                        # If multi-speaker, mention them
                        if len(blocks) > 0:
                            speakers = ", ".join(list(set([b['speaker'] for b in blocks])))
                            summary = f"{user_name} and {speakers} discussed matters in {chan_label}."
                        
                        from core.storage import log_narrative_event
                        log_narrative_event(summary)
                 
            except Exception as e:
                logger.error(f"AI Generation Failed: {e}", exc_info=True)
                await message.channel.send(f"❌ *A temporal anomaly disrupts the Chronicle...* ({e})")

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
                    await transport.send(ctx.channel, f"❌ **Error:** Message `{message_id}` not found in this channel.", identity_key="DM")
                    return

                # 2. Priority Discord Purge: Delete everything AFTER the target message
                # We do this first so the channel looks right immediately
                deleted = await ctx.channel.purge(after=target_msg, limit=500)
                
                # 3. Synchronize AI Memory
                # Attempt rollback using content matching
                success = client.rollback_to_id(message_id, target_msg.content)
                
                status_msg = f"⏳ **Chronicle Rolled Back:** Discord history cleared after `{message_id}` ({len(deleted)} messages)."
                
                if success:
                    status_msg += "\n✅ AI internal memory successfully synced with rollback."
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
                    status_msg += f"\n🔄 AI memory resynced by rebuilding context from the last {len(messages)} surviving messages."
                
                from core.storage import log_narrative_event
                log_narrative_event(f"The Chronicle of {channel_label} was rolled back to message {message_id}.")
                
                await transport.send(ctx.channel, status_msg, identity_key="DM")
            else:
                # Full wipe
                self.brain_manager.reset_client(channel_id)
                from core.storage import log_narrative_event
                log_narrative_event(f"The Chronicle's local memory of {channel_label} was reset.")
                await transport.send(ctx.channel, f"🧹 **Memory Cleared:** The AI's local context for {channel_label} has been wiped.", identity_key="DM")
                
        except Exception as e:
            logger.error(f"Clear command error: {e}", exc_info=True)
            await transport.send(ctx.channel, f"❌ Error during clear: {e}")

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
                
                await transport.send(ctx.channel, f"🧘 **Context Refreshed:** History rebuilt from the last {len(messages)} messages.", identity_key="DM")
        except Exception as e:
            logger.error(f"Refresh command error: {e}", exc_info=True)
            await transport.send(ctx.channel, f"❌ Error during refresh: {e}")

    @commands.command(name="pulse")
    async def pulse(self, ctx, *, manual_event: str = None):
        """Force a refresh of the narrative pulse or manually log a global event. !pulse [text] to save."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        try:
            from core.storage import DB_DIR, log_narrative_event
            
            if manual_event:
                log_narrative_event(f"MANUAL: {manual_event}")
                from core.transport import transport
                await transport.send(channel, f"📜 **Chronicle Updated:** Recorded manual entry.", identity_key="DM")
                return

            log_path = DB_DIR / "NARRATIVE_LOG.md"
            if not log_path.exists():
                await self.transport.send(channel, "🔍 **Narrative Pulse is silent.** No global events recorded yet.")
                return
                
            lines = log_path.read_text(encoding='utf-8').splitlines()
            recent = lines[-5:]
            
            msg = ["**📜 Global Narrative Pulse (Latest Events)**"]
            msg.extend(recent)
            msg.append("\n*The Chronicle remains synchronized across all channels.*")
            
            from core.transport import transport
            await transport.send(channel, "\n".join(msg), identity_key="DM")
        except Exception as e:
            from core.transport import transport
            await transport.send(channel, f"❌ Error checking pulse: {e}")

async def setup(bot):
    await bot.add_cog(BrainCog(bot))

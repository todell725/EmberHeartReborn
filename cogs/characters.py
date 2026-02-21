import discord
from discord.ext import commands
import logging
import json
import asyncio
from core.config import ROOT_DIR, DB_DIR
from core.routing import require_channel
from core.transport import TransportAPI

logger = logging.getLogger("Cog_Characters")

class CharactersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from core.transport import transport
        self.transport = transport

    @commands.command()
    @require_channel("npc-gallery")
    async def npc(self, ctx, *, name: str):
        """Lookup an NPC or Party Member character card."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        try:
            from core.storage import resolve_character
            match = resolve_character(name)
            
            if not match:
                await self.transport.send(channel, f"🔍 No Character found matching '{name}'")
                return

            role = match.get('role', f"Level {match.get('level', '?')} {match.get('class', 'Hero')}")
            status = match.get('status', match.get('loyalty_status', 'Active'))
            if isinstance(status, dict): status = "Stabilized"
            
            bio = match.get('bio', match.get('background', match.get('secret', 'No further data.')))
            motivation = match.get('motivation', 'Unknown')
            description = match.get('description', 'No visual data provided.')
            
            is_party = 'combat_profile' in match
            if is_party:
                cp = match.get('combat_profile', {})
                msg = (f"👤 **Character Card: {match['name']}**\n"
                       f"*{match.get('race')} {match.get('class')} (Level {match.get('level')})*\n\n"
                       f"✨ **Background:** {match.get('background')}\n"
                       f"🌿 **Visuals:** {description}\n"
                       f"🌱 **Motivation:** {motivation}\n"
                       f"💭 **Bio:** {bio}\n\n"
                       f"⚔️ **Combat:** AC {cp.get('ac')} | HP {cp.get('hp')} | Init +{cp.get('initiative_bonus')}")
            else:
                msg = (f"👤 **NPC Card: {match['name']}**\n"
                       f"*{match.get('role', 'Unknown')}*\n\n"
                       f"**Status:** {status}\n"
                       f"**Visuals:** {description}\n"
                       f"**Motivation:** {motivation}\n"
                       f"**Details:** {bio[:500]}")
                       
            target_avatar = match.get('avatar_url')
            final_msg = msg
            if target_avatar:
                final_msg += f"\n\n{target_avatar}"

            await self.transport.send(
                channel, 
                final_msg, 
                identity_key="NPC", 
                username=match['name'], 
                avatar_url=target_avatar
            )
        except Exception as e:
            await self.transport.send(channel, f"❌ Error: {e}")

    @commands.command()
    @require_channel("npc-gallery")
    async def worn(self, ctx):
        """Show the party's currently equipped gear."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        try:
            if not self.party_path.exists():
                await self.transport.send(channel, "❌ Error: Party state file not found.")
                return
                
            data = json.loads(self.party_path.read_text(encoding='utf-8'))
            party = data.get("party", [])
            
            msg_parts = ["**🛡️ Worn Equipment: The Royal Guard**"]
            
            for p in party:
                eq = p.get("status", {}).get("equipment", {})
                if eq:
                    msg_parts.append(f"\n**{p['name']} ({p.get('class')})**")
                    msg_parts.append(f"• **Head**: {eq.get('head', 'None')}")
                    msg_parts.append(f"• **Body**: {eq.get('body', 'None')}")
                    msg_parts.append(f"• **Main Hand**: {eq.get('main_hand', 'None')}")
                    msg_parts.append(f"• **Off Hand**: {eq.get('off_hand', 'None')}")
                    msg_parts.append(f"• **Accessory**: {eq.get('accessory', 'None')}")
                else:
                    msg_parts.append(f"\n**{p['name']}**: No equipment data found.")
                    
            await self.transport.send(channel, "\n".join(msg_parts))
        except Exception as e:
            await self.transport.send(channel, f"❌ Error reading equipment: {e}")

    @commands.command()
    @require_channel("npc-gallery")
    async def capture(self, ctx):
        """Scan current channel for images and map them to characters in the state files."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        await self.transport.send(channel, "🔍 **Scanning for character portraits...**")
        
        try:
            party_data = json.loads(self.party_path.read_text(encoding='utf-8')) if self.party_path.exists() else {"party": []}
            npc_data = json.loads(self.npc_path.read_text(encoding='utf-8')) if self.npc_path.exists() else {"npcs": []}
            
            all_chars = party_data.get("party", []) + npc_data.get("npcs", [])
            updates_found = 0
            
            async for message in channel.history(limit=None, oldest_first=True):
                if not message.attachments:
                    continue
                    
                content_lower = message.content.lower().strip()
                id_match_char = None
                for char in all_chars:
                    char_id = char.get("id", "").lower()
                    if char_id and char_id in content_lower:
                        id_match_char = char
                        break
                
                if id_match_char:
                    for attachment in message.attachments:
                        img_url = attachment.url
                        if id_match_char.get("avatar_url") != img_url:
                            id_match_char["avatar_url"] = img_url
                            updates_found += 1
                    continue

                for char in all_chars:
                    full_name = char.get("name", "").lower()
                    clean_name = full_name.replace('"', '').replace("'", "").replace('(', '').replace(')', '')
                    tokens = [t.strip() for t in clean_name.split() if len(t.strip()) > 2]
                    
                    if full_name in content_lower or any(t in content_lower for t in tokens):
                        for attachment in message.attachments:
                            img_url = attachment.url
                            if char.get("avatar_url") != img_url:
                                char["avatar_url"] = img_url
                                updates_found += 1
                                break 

            if updates_found > 0:
                self.party_path.write_text(json.dumps(party_data, indent=4), encoding='utf-8')
                self.npc_path.write_text(json.dumps(npc_data, indent=4), encoding='utf-8')
                
            total_chars = len(all_chars)
            with_visuals = len([c for c in all_chars if c.get("avatar_url") or c.get("description")])
            
            summary_msg = await channel.send(
                f"📊 **Capture Complete!**\n"
                f"🔄 **New Links Found:** {updates_found}\n"
                f"🖼️ **Total Portraits Locked:** {len([c for c in all_chars if c.get('avatar_url')])}\n"
                f"🏮 **Gallery Coverage:** {with_visuals}/{total_chars}\n\n"
                f"*Self-destructing text tags in 5 seconds...*"
            )
            
            deleted_count = 0
            async for message in channel.history(limit=None):
                if message.id == summary_msg.id: continue
                if not message.attachments:
                    try:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(1.25)
                    except: pass
            
            await asyncio.sleep(5)
            await summary_msg.delete()

        except Exception as e:
            await self.transport.send(channel, f"❌ Error during capture: {e}")

    @commands.command()
    @require_channel("npc-gallery")
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx):
        """Gallery Maintenance: Delete all messages in this channel that do NOT have images."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        try:
            status_msg = await channel.send("🧹 **Cleanup Initiative Started...**")
            deleted_count = 0
            async for message in channel.history(limit=None):
                if message.id == status_msg.id: continue
                if not message.attachments:
                    try:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(1.25)
                    except: pass
            await status_msg.edit(content=f"✨ **Cleanup Complete!** Purged {deleted_count} text-only messages. Leaving gallery in 5 seconds...")
            await asyncio.sleep(5)
            await status_msg.delete()
        except Exception as e:
            await self.transport.send(channel, f"❌ Error during cleanup: {e}")

    @commands.command(name="list")
    @require_channel("npc-gallery")
    async def cmd_list(self, ctx, mode: str = None):
        """Cheat Code: Output character cards. Use '!list missing' for an avatar audit."""
        channel = getattr(ctx, "target_channel", ctx.channel)
        is_audit = (mode and mode.lower() in ["missing", "audit", "check"])

        try:
            characters = []
            if self.party_path.exists():
                party_data = json.loads(self.party_path.read_text(encoding='utf-8'))
                characters.extend(party_data.get("party", []))
            
            if self.npc_path.exists():
                npc_data = json.loads(self.npc_path.read_text(encoding='utf-8'))
                characters.extend(npc_data.get("npcs", []))
                
            if is_audit:
                notable = [c for c in characters if not c.get("avatar_url")]
                header_text = f"🕵️ **Avatar Audit: {len(notable)} characters missing images.** (Grouped by 5)"
            else:
                notable = [c for c in characters if c.get("description")]
                header_text = f"📜 **Batch Processing {len(notable)} Character Cards...**"
            
            if not notable:
                await self.transport.send(channel, "🏮 No matching characters found.")
                return
                
            await self.transport.send(channel, header_text)
            
            if is_audit: notable = notable[:5]

            for char in notable:
                name = char.get('name', 'Unknown')
                role = char.get('role', f"Level {char.get('level', '?')} {char.get('class', 'Hero')}")
                status = char.get('status', char.get('loyalty_status', 'Active'))
                if isinstance(status, dict): status = "Stabilized"
                
                bio = char.get('bio', char.get('background', char.get('secret', 'No further data.')))
                motivation = char.get('motivation', 'Unknown')
                description = char.get('description', 'No visual data provided.')
                
                is_party = 'combat_profile' in char
                if is_party:
                    cp = char.get('combat_profile', {})
                    msg = (f"👤 **Character Card: {name}**\n"
                           f"*{char.get('race')} {char.get('class')} (Level {char.get('level')})*\n\n"
                           f"✨ **Background:** {char.get('background')}\n"
                           f"🌿 **Visuals:** {description}\n"
                           f"🌱 **Motivation:** {motivation}\n"
                           f"💭 **Bio:** {bio}\n\n"
                           f"⚔️ **Combat:** AC {cp.get('ac')} | HP {cp.get('hp')} | Init +{cp.get('initiative_bonus')}")
                else:
                    msg = (f"👤 **NPC Card: {name}**\n"
                           f"*{role}*\n\n"
                           f"**Status:** {status}\n"
                           f"**Visuals:** {description}\n"
                           f"**Motivation:** {motivation}\n"
                           f"**Details:** {bio[:500]}")

                avatar = char.get('avatar_url')
                if avatar:
                    await self.transport.send(
                        channel, 
                        msg + f"\n\n{avatar}", 
                        identity_key="NPC", 
                        username=name, 
                        avatar_url=avatar
                    )
                else:
                    await self.transport.send(channel, msg, identity_key="NPC", username=name)
                
                await asyncio.sleep(1.25)

        except Exception as e:
            await self.transport.send(channel, f"❌ Error during batch list: {e}")

    @commands.command()
    async def hp(self, ctx, name: str, change: str):
        """Adjust character HP: !hp Kaelrath -10 or !hp Talmarr +5."""
        try:
            if not self.party_path.exists():
                await self.transport.send(ctx.channel, "❌ Error: Party state not found.")
                return
                
            data = json.loads(self.party_path.read_text(encoding='utf-8'))
            party = data.get("party", [])
            
            char = next((p for p in party if name.lower() in p['name'].lower()), None)
            if not char:
                await self.transport.send(ctx.channel, f"🔍 Character '{name}' not found in party.")
                return
                
            cp = char.get("combat_profile")
            if not cp:
                await self.transport.send(ctx.channel, f"❌ {char['name']} does not have a combat profile.")
                return
                
            try:
                val = int(change)
                old_hp = cp.get("hp", 0)
                new_hp = old_hp + val
                cp["hp"] = new_hp
                
                self.party_path.write_text(json.dumps(data, indent=4), encoding='utf-8')
                
                status_emoji = "🩸" if val < 0 else "💖"
                await self.transport.send(ctx.channel, f"{status_emoji} **HP Update: {char['name']}**\n`{old_hp}` -> `{new_hp}`")
                
            except ValueError:
                await self.transport.send(ctx.channel, "❌ Invalid format. Use: `!hp [name] [+/-amount]` (e.g., `!hp Kaelrath -5`)")
                
        except Exception as e:
            await self.transport.send(ctx.channel, f"❌ Error updating HP: {e}")

    @commands.command(name='dm')
    async def dm(self, ctx, char_name: str, *, message: str):
        """Send a secret message to an NPC/Party member to start a DM thread."""
        try:
            from core.storage import resolve_character
            match = resolve_character(char_name)
            
            if not match:
                await self.transport.send(ctx.channel, f"🔍 Hmm. The Chronicle has no record of '{char_name}'.")
                return

            char_display_name = match.get('name')
            char_id = match.get('id', 'NPC')
            char_topic = f"{char_display_name} [{char_id}]"
            
            # Send the message to a private server channel
            try:
                guild = ctx.guild
                if not guild:
                    await self.transport.send(ctx.channel, "❌ You must use this command inside the server, not in a DM.")
                    return

                # Create a clean channel name: dm-npcname-username
                user_clean = "".join(c for c in ctx.author.name if c.isalnum()).lower()
                char_clean = "".join(c for c in char_name if c.isalnum()).lower()
                channel_name = f"dm-{char_clean}-{user_clean}"

                # Check if it already exists
                dm_channel = discord.utils.get(guild.text_channels, name=channel_name)
                
                if dm_channel:
                     await ctx.message.add_reaction("✉️")
                     # Update topic just in case it was created by an older version
                     if dm_channel.topic != char_topic:
                         await dm_channel.edit(topic=char_topic)
                     await self.transport.send(ctx.channel, f"➡️ Thread resumed in {dm_channel.mention}!")
                else:
                     # Create the private channel
                     overwrites = {
                         guild.default_role: discord.PermissionOverwrite(read_messages=False),
                         ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                         guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_webhooks=True)
                     }
                     
                     # Check for a 'DMs' category, optional
                     category = discord.utils.get(guild.categories, name="DMs")
                     dm_channel = await guild.create_text_channel(
                         name=channel_name, 
                         overwrites=overwrites, 
                         category=category,
                         topic=char_topic
                     )
                     await self.transport.send(ctx.channel, f"✉️ Private comms established: {dm_channel.mention}")
                
                # Mock the interaction by sending the user's message to the new channel 
                await self.transport.send(
                    dm_channel,
                    f"*You secretly reached out to {char_display_name}:*\n> {message}",
                    username="DM System"
                )
                
                # Trigger the AI to respond in the channel
                from cogs.brain import IDENTITIES, parse_speaker_blocks
                client = self.bot.get_cog("BrainCog").brain_manager.get_client(dm_channel.id, npc_name=char_display_name)
                response_text = await asyncio.to_thread(
                    client.chat, 
                    f"{ctx.author.display_name} (To {char_name}): {message}"
                )
                
                blocks = parse_speaker_blocks(response_text, IDENTITIES, [])
                for idx, block in enumerate(blocks):
                    speaker = block["speaker"]
                    identity = dict(match) if char_name.lower() in speaker.lower() else block["identity"]
                    content = block["content"]
                    wait = (idx < len(blocks) - 1)
                    
                    if identity:
                        await self.transport.send(dm_channel, content, username=identity.get("name", speaker), wait=wait)
                    else:
                        await self.transport.send(dm_channel, content, username=speaker, wait=wait)
                        
            except discord.Forbidden:
                await self.transport.send(ctx.channel, f"❌ I don't have permission to create channels, {ctx.author.mention}!")
                
        except Exception as e:
            logger.error(f"DM Error: {e}", exc_info=True)
            await self.transport.send(ctx.channel, f"❌ A temporal anomaly disrupts the message... ({e})")

async def setup(bot):
    await bot.add_cog(CharactersCog(bot))

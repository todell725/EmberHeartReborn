import aiohttp
import asyncio
import json
import logging
import re
import discord
from discord import Webhook
from pathlib import Path
from core.config import IDENTITIES
from core.formatting import sanitize_text

logger = logging.getLogger("EH_Transport")

# Webhook cache persisted to disk so we survive bot restarts
_CACHE_PATH = Path(__file__).resolve().parent.parent / "state" / "WEBHOOK_CACHE.json"

class TransportAPI:
    """Unified API for sending messages to Discord via Webhooks or standard Fallbacks."""
    
    def __init__(self):
        self._cache = {}        # (channel_id) -> general webhook
        self._npc_cache = {}    # (channel_id, npc_slug) -> webhook URL
        self._load_npc_cache()

    # ─── NPC Webhook Registry (T3) ───────────────────────────────────────────

    def _npc_slug(self, npc_name: str) -> str:
        """Normalize NPC name to a safe webhook name slug."""
        slug = re.sub(r'[^a-zA-Z0-9 ]', '', npc_name).strip()
        return f"EH-{slug[:24]}"  # Discord webhook names max 80 chars; we keep it short

    def _load_npc_cache(self):
        """Load persisted webhook URLs from disk."""
        try:
            if _CACHE_PATH.exists():
                data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
                self._npc_cache = {tuple(k.split("|")): v for k, v in data.items()}
                logger.info(f"Loaded {len(self._npc_cache)} cached NPC webhooks.")
        except Exception as e:
            logger.warning(f"Could not load webhook cache: {e}")

    def _save_npc_cache(self):
        """Persist webhook URL cache to disk."""
        try:
            _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            serializable = {"|".join(k): v for k, v in self._npc_cache.items()}
            _CACHE_PATH.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not save webhook cache: {e}")

    async def _get_npc_webhook(self, channel, npc_name: str, session):
        """Get or create a dedicated webhook for a specific NPC in a channel.
        
        Respects Discord's 10-webhook limit by reusing the oldest EH- webhook
        if the channel is full.
        """
        # Normalize key using slug to prevent casing duplicates (Codex-3)
        npc_slug = self._npc_slug(npc_name)
        key = (str(channel.id), npc_slug)
        
        # Check in-memory cache first (URL-based)
        cached_url = self._npc_cache.get(key)
        if cached_url:
            try:
                wh = Webhook.from_url(cached_url, session=session)
                return wh
            except Exception:
                # URL might be stale; remove from cache and recreate
                del self._npc_cache[key]
        
        slug = self._npc_slug(npc_name)
        
        try:
            existing_hooks = await channel.webhooks()
            
            # Check if our named webhook already exists
            wh = next((w for w in existing_hooks if w.name == slug), None)
            if wh:
                self._npc_cache[key] = wh.url
                self._save_npc_cache()
                return wh
            
            # Guard: if at or near the 10-webhook limit, reuse the oldest EH- hook
            eh_hooks = [w for w in existing_hooks if w.name and w.name.startswith("EH-")]
            if len(existing_hooks) >= 8 and eh_hooks:
                oldest = sorted(eh_hooks, key=lambda w: w.id)[0]
                await oldest.edit(name=slug, reason=f"NPC slot reused for {npc_name}")
                wh = oldest
            else:
                wh = await channel.create_webhook(name=slug, reason=f"NPC webhook for {npc_name}")
            
            self._npc_cache[key] = wh.url
            self._save_npc_cache()
            logger.info(f"Created NPC webhook '{slug}' in #{channel.name}")
            return wh
            
        except discord.Forbidden:
            logger.warning(f"No Manage Webhooks permission in #{channel.name}. NPC webhooks unavailable.")
            return None
        except Exception as e:
            logger.warning(f"Could not get NPC webhook for '{npc_name}' in #{channel.name}: {e}")
            return None

    async def send_as_npc(self, channel, npc_name: str, content: str, avatar_url: str = None, wait: bool = False):
        """Send a message to a channel impersonating a specific NPC.
        
        Uses a dedicated per-NPC webhook with their locked name and avatar.
        Falls back to standard send with bold name prefix if webhooks fail.
        """
        content = sanitize_text(content)
        if not content:
            return
        
        # Resolve avatar from IDENTITIES if not provided
        if not avatar_url:
            identity = IDENTITIES.get(npc_name)
            if not identity:
                # Try fuzzy match
                match = next((k for k in IDENTITIES if isinstance(k, str) and k.lower() == npc_name.lower()), None)
                if match:
                    identity = IDENTITIES[match]
            if identity:
                avatar_url = identity.get("avatar")
        
        async with aiohttp.ClientSession() as session:
            wh = await self._get_npc_webhook(channel, npc_name, session)
            if wh:
                try:
                    await self._send_chunked_webhook(wh, content, npc_name, avatar_url, wait=wait)
                    return
                except discord.errors.NotFound: # Webhook deleted
                    logger.warning(f"NPC webhook {wh.url} for '{npc_name}' not found. Clearing from cache and retrying.")
                    key = (str(channel.id), self._npc_slug(npc_name))
                    if key in self._npc_cache:
                        del self._npc_cache[key]
                        self._save_npc_cache()
                    # Try again after clearing cache
                    wh = await self._get_npc_webhook(channel, npc_name, session)
                    if wh:
                        try:
                            await self._send_chunked_webhook(wh, content, npc_name, avatar_url, wait=wait)
                            return
                        except Exception as e:
                            logger.warning(f"NPC webhook send failed on retry for '{npc_name}': {e}. Using standard fallback.")
                    else:
                        logger.warning(f"Could not re-create NPC webhook for '{npc_name}'. Using standard fallback.")
                except Exception as e:
                    logger.warning(f"NPC webhook send failed for '{npc_name}': {e}. Using standard fallback.")
            
            # Fallback: standard channel send with bold name
            await self._send_chunked_standard(channel, content, username=npc_name)

    # ─── General Webhook (legacy, used by DM bot) ─────────────────────────────

    async def _get_webhook(self, channel, session):
         """Get or create a general 'EmberHeart DM' webhook for the target channel."""
         if channel.id in self._cache:
             return self._cache[channel.id]
         
         try:
             whs = await channel.webhooks()
             wh = next((w for w in whs if w.name == "EmberHeart DM"), None)
             
             if not wh:
                 wh = await channel.create_webhook(name="EmberHeart DM", reason="Dynamic NPC Impersonation")
             
             self._cache[channel.id] = wh
             return wh
         except Exception as e:
             logger.warning(f"Failed to manage webhook for {channel.name}: {e}")
             return None

    async def send(self, channel, content: str, identity_key: str = "DM", wait: bool = False, username: str = None, avatar_url: str = None):
         """
         Send a message via dynamic webhook, falling back to standard send on failure.
         Automatically chunks messages longer than 1900 characters.
         """
         content = sanitize_text(content)
         
         async with aiohttp.ClientSession() as session:
             webhook = await self._get_webhook(channel, session)
             
             # Presets based on identity registry
             identity = IDENTITIES.get(identity_key, IDENTITIES["DM"])
             final_name = username or identity["name"]
             final_avatar = avatar_url or identity["avatar"]
             
             # Robust Fallback: If we have a username but the avatar is the Weaver (or missing), 
             # try to find a better avatar from the registry using the name.
             dm_avatar_base = IDENTITIES["DM"]["avatar"].split('?')[0]
             current_avatar_base = (final_avatar or "").split('?')[0]
             
             if final_name and identity_key != "DM" and (not final_avatar or current_avatar_base == dm_avatar_base):
                 match = next((k for k in IDENTITIES if isinstance(k, str) and k.lower() == final_name.lower()), None)
                 if match and IDENTITIES[match].get("avatar"):
                     final_avatar = IDENTITIES[match]["avatar"]

             if not webhook:
                 return await self._send_chunked_standard(channel, content, final_name)

             try:
                 logger.debug(f"[WEBHOOK] Routing to {getattr(channel, 'name', 'DM')} as {final_name}")
                 return await self._send_chunked_webhook(webhook, content, final_name, final_avatar, wait)
             except discord.errors.NotFound: # Webhook deleted
                 logger.warning(f"General Webhook {webhook.url} returned 404. Clearing from cache and retrying.")
                 if channel.id in self._cache:
                     del self._cache[channel.id]
                 # Try again after clearing cache
                 webhook = await self._get_webhook(channel, session)
                 if webhook:
                     try:
                         return await self._send_chunked_webhook(webhook, content, final_name, final_avatar, wait)
                     except Exception as e:
                         logger.warning(f"General Webhook send failed on retry: {e}. Using standard fallback.")
                 else:
                     logger.warning(f"Could not re-create General Webhook. Using standard fallback.")
                 return await self._send_chunked_standard(channel, content, final_name)
             except Exception:
                 return await self._send_chunked_standard(channel, content, final_name)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _send_chunked_webhook(self, webhook, content, username, avatar_url, wait):
        """Helper to handle webhook limits."""
        MAX_LENGTH = 1900
        if len(content) <= MAX_LENGTH:
             return await webhook.send(content=content, username=username, avatar_url=avatar_url, wait=wait)
        
        chunks = self._chunk_text(content, MAX_LENGTH)
        last_msg = None
        for chunk in chunks:
             if chunk:
                 last_msg = await webhook.send(content=chunk, username=username, avatar_url=avatar_url, wait=True)
                 await asyncio.sleep(0.5)
        return last_msg

    async def _send_chunked_standard(self, channel, content, username=None):
        """Helper to handle standard message limits. Prepends character name for DMs."""
        if isinstance(channel, discord.DMChannel) and username and username != "DM":
             content = f"**{username}:**\n{content}"

        MAX_LENGTH = 1900
        if len(content) <= MAX_LENGTH:
            return await channel.send(content)
            
        chunks = self._chunk_text(content, MAX_LENGTH)
        last_msg = None
        for chunk in chunks:
            if chunk:
                 last_msg = await channel.send(chunk)
                 await asyncio.sleep(0.5)
        return last_msg

    def _chunk_text(self, text, max_len):
        """Splits text cleanly on newlines."""
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_idx = text.rfind('\n', 0, max_len)
            if split_idx == -1: 
                 split_idx = max_len
            chunks.append(text[:split_idx].strip())
            text = text[split_idx:].strip()
        return chunks

# Singleton instance
transport = TransportAPI()

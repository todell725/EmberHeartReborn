import aiohttp
import asyncio
import logging
import discord
from discord import Webhook
from core.config import IDENTITIES
from core.formatting import sanitize_text

logger = logging.getLogger("EH_Transport")

class TransportAPI:
    """Unified API for sending messages to Discord via Webhooks or standard Fallbacks."""
    
    def __init__(self):
        self._cache = {}

    async def _get_webhook(self, channel, session):
         """Get or create a webhook for the target channel."""
         if channel.id in self._cache:
             return self._cache[channel.id]
         
         try:
             # Look for existing
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

             if not webhook:
                 # Fallback: Can't use webhooks here (e.g. DM channels or lacking permissions)
                 return await self._send_chunked_standard(channel, content)

             try:
                 logger.debug(f"[WEBHOOK] Routing to {channel.name} as {final_name}")
                 return await self._send_chunked_webhook(webhook, content, final_name, final_avatar, wait)
             except Exception as e:
                 logger.error(f"Webhook send failed: {e}. Falling back to standard send.")
                 return await self._send_chunked_standard(channel, content)

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
                 await asyncio.sleep(0.5) # Prevent ratelimits
        return last_msg

    async def _send_chunked_standard(self, channel, content):
        """Helper to handle standard message limits."""
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
            # Try to split on newline
            split_idx = text.rfind('\n', 0, max_len)
            if split_idx == -1: 
                 split_idx = max_len # Hard split if no newline
            chunks.append(text[:split_idx].strip())
            text = text[split_idx:].strip()
        return chunks

# Singleton instance
transport = TransportAPI()

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import re

# Setup root path
ROOT = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(ROOT))

import discord
from discord.ext import commands

async def diagnostic_on_message():
    print("--- START DIAGNOSTIC ---")
    
    # Mock bot
    bot = MagicMock()
    bot.user = MagicMock(name="BotUser")
    bot.user.name = "EmberHeart"
    bot.command_prefix = "!"
    
    # Mock Cog
    from cogs.brain import BrainCog
    cog = BrainCog(bot)
    
    # Mock Message
    message = MagicMock()
    message.author = MagicMock(name="Todd")
    message.author.name = "todd"
    message.author.display_name = "Todd"
    message.author.bot = False
    message.webhook_id = None
    message.content = "What's the status of the kingdom?"
    message.clean_content = "What's the status of the kingdom?"
    message.mentions = []
    
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "campaign-chat"
    channel.id = 12345
    message.channel = channel
    
    # Mock typing
    channel.typing.return_value.__aenter__ = AsyncMock()
    channel.typing.return_value.__aexit__ = AsyncMock()
    
    # Mock Brain Manager
    client_mock = MagicMock()
    cog.brain_manager.get_client = MagicMock(return_value=client_mock)
    
    # Simulate a typical AI response that might be problematic
    # Maybe it uses the user's name?
    client_mock.chat.return_value = "**King Kaelrath**: You see the starships above." 
    
    import core.transport
    sent_messages = []
    async def mock_send(chan, content, **kwargs):
        sent_messages.append({"content": content, "kwargs": kwargs})
        print(f"DEBUG: Sent -> {content[:50]}... (to {kwargs.get('username', 'DM')})")

    core.transport.transport.send = mock_send
    
    # Log internal steps
    print(f"Channel Name: {channel.name}")
    print(f"Whitelisted: {any(name in channel.name for name in ['npc-chat', 'party-chat', 'game-feed', 'campaign-chat', 'rumors-chat', 'off-topic', 'weaver-archives'])}")
    
    # Execute listener
    try:
        await cog.on_message(message)
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

    print(f"Sent Message Count: {len(sent_messages)}")
    if not sent_messages:
        print("ALERT: No messages sent!")
        
    print("--- END DIAGNOSTIC ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(diagnostic_on_message())

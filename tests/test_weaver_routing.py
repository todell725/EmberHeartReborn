import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Setup root path
ROOT = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(ROOT))

import discord
from discord.ext import commands

async def test_weaver_routing():
    print("Testing Weaver Routing Logic...")
    
    # Mock bot
    bot = MagicMock()
    bot.user = MagicMock(name="BotUser")
    bot.command_prefix = "!"
    
    # Mock Cog
    from cogs.brain import BrainCog
    cog = BrainCog(bot)
    
    # Mock Message in weaver-archives
    message = MagicMock()
    message.author = MagicMock(name="Todd")
    message.author.name = "todd"
    message.author.display_name = "Todd"
    message.webhook_id = None
    message.content = "yo weaver!"
    message.clean_content = "yo weaver!"
    message.mentions = []
    
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "weaver-archives"
    channel.id = 12345
    message.channel = channel
    
    # Mock typing context manager
    channel.typing.return_value.__aenter__ = AsyncMock()
    channel.typing.return_value.__aexit__ = AsyncMock()
    
    # Mock Brain Manager and Client
    client_mock = MagicMock()
    cog.brain_manager.get_client = MagicMock(return_value=client_mock)
    client_mock.chat.return_value = "[The Chronicle Weaver]: Greetings, Kaelrath."
    
    # We need to mock 'transport' which is imported in BrainCog
    import core.transport
    core.transport.transport.send = AsyncMock()
    
    # Run the listener
    await cog.on_message(message)
    
    # Verify client.apply_weaver_mode was called
    print(f"Apply Weaver Mode Called: {client_mock.apply_weaver_mode.called}")
    assert client_mock.apply_weaver_mode.called, "apply_weaver_mode should be called in weaver-archives"
    
    # Verify routing worked (didn't return early)
    assert cog.brain_manager.get_client.called, "get_client should be called if routing passed"
    print("✅ Weaver Routing and Mode Activation verified.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_weaver_routing())

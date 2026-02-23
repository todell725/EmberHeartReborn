import sys
import os
import logging
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import discord

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s: %(message)s')

# Add project root to sys.path
project_root = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(project_root))

from cogs.brain import BrainCog
from core.config import IDENTITIES

async def run_diagnostic():
    print("--- [OFF-TOPIC DIAGNOSTIC START] ---")
    bot = MagicMock()
    cog = BrainCog(bot)
    
    # Mock message
    message = AsyncMock(spec=discord.Message)
    message.author = MagicMock(spec=discord.Member)
    message.author.bot = False
    message.author.name = "lamorte725" # Owner ID
    message.author.display_name = "King Kaelrath"
    message.author.id = 12345
    message.content = "What's going on in the tavern?"
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.name = "off-topic"
    message.channel.id = 111222333
    message.mentions = []
    
    # Bypass typing
    message.channel.typing.return_value.__aenter__ = AsyncMock()
    message.channel.typing.return_value.__aexit__ = AsyncMock()
    
    # Test Scenario 1: DM Only Response
    print("\nScenario 1: DM Only Response")
    mock_client = MagicMock()
    mock_client.chat.return_value = "**DM**: \"The fireplace crackles.\""
    cog.brain_manager.get_client = MagicMock(return_value=mock_client)
    await cog.on_message(message)

    # Test Scenario 2: Hallucinated User + Character (Dangerous)
    print("\nScenario 2: AI hallucinates King Kaelrath + NPC")
    mock_client.chat.return_value = "**King Kaelrath**: \"I'll have a drink.\"\n**Ilyra**: \"I'll join you.\""
    await cog.on_message(message)

    # Test Scenario 3: Mixed Narration and Talk
    print("\nScenario 3: DM Narration + Character")
    mock_client.chat.return_value = "**DM**: \"The barkeep nods.\"\n**Barkeep**: \"What can I get you?\""
    await cog.on_message(message)

    print("\n--- [DIAGNOSTIC COMPLETE] ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_diagnostic())

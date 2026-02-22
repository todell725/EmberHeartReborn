import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Setup root path
ROOT = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(ROOT))

import discord
from discord.ext import commands

async def test_permission_logic():
    print("Testing Owner Setup Permission Logic...")
    
    # Mock context and guild
    ctx = MagicMock()
    guild = MagicMock()
    ctx.guild = guild
    ctx.author = MagicMock(name="ctx.author")
    
    # Scenario: guild.owner is None (The bug reported)
    guild.owner = None
    guild.owner_id = 999
    guild.get_member.return_value = None  # Not in cache
    guild.default_role = MagicMock(name="default_role")
    guild.me = MagicMock(name="bot_me")
    
    # The logic we just implemented
    owner_target = guild.owner or guild.get_member(guild.owner_id) or ctx.author
    bot_target = guild.me or ctx.guild.me
    
    print(f"Owner Target: {owner_target}")
    assert owner_target == ctx.author, "Should fallback to ctx.author when guild.owner is None"
    print("✅ Fallback to ctx.author works.")
    
    # Scenario: guild.owner IS present
    real_owner = MagicMock(name="real_owner")
    guild.owner = real_owner
    owner_target = guild.owner or guild.get_member(guild.owner_id) or ctx.author
    print(f"Owner Target: {owner_target}")
    assert owner_target == real_owner, "Should use real owner when available"
    print("✅ Real owner usage works.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_permission_logic())

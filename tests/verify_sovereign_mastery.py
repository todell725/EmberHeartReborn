import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta

# Setup paths
ROOT = Path(r"z:\DnD\EmberHeartReborn")
sys.path.append(str(ROOT))

async def test_sovereign_mastery():
    print("--- Testing Sovereign Mastery (Phase 15) ---")
    
    from engines.slayer_engine import SlayerEngine
    from engines.combat_engine import CombatTracker
    from cogs.slayer import SlayerCog
    from cogs.owner import OwnerCog
    
    # 1. Test CombatTracker Targeted XP
    print("\nTest 1: Targeted XP in CombatTracker")
    tracker = CombatTracker()
    # Mocking character state loading/saving
    import core.storage
    original_load = core.storage.load_all_character_states
    original_save = core.storage.save_character_state
    
    core.storage.load_all_character_states = lambda: [
        {"id": "PC-01", "name": "Kaelrath", "experience_points": 0, "level": 1},
        {"id": "PC-02", "name": "Talmarr", "experience_points": 0, "level": 1}
    ]
    core.storage.save_character_state = MagicMock()
    
    tracker.add_party_xp(100, target_ids=["PC-01"])
    
    # Verify save_character_state was called only for PC-01
    saved_ids = [call.args[0] for call in core.storage.save_character_state.call_args_list]
    if "PC-01" in saved_ids and "PC-02" not in saved_ids:
        print("  [PASS] XP awarded exclusively to target.")
    else:
        print(f"  [FAIL] Targeted XP failed. Saved IDs: {saved_ids}")

    # 2. Test Slayer TTK Scaling
    print("\nTest 2: Solo Slayer TTK Scaling")
    engine = SlayerEngine()
    engine._db = [{"task_id": "TEST", "monster_name": "Ghost", "idle_mechanics": {"time_to_kill_sec": 100}}]
    
    # Start solo task
    engine.start_task(123, "TEST", solo=True)
    active = engine.get_active(123)
    
    if active.get('solo') == True:
        print("  [PASS] Solo flag stored in engine.")
    else:
        print("  [FAIL] Solo flag missing from engine.")

    # 3. Test Owner Skip Cap Removal
    print("\nTest 3: Owner Skip Cap Removal")
    owner = OwnerCog(MagicMock())
    ctx = MagicMock()
    ctx.channel.id = 123
    owner.slayer_engine.active_tasks[123] = {"start_time": datetime.now()}
    owner.transport = AsyncMock()
    
    await owner.owner_skip.callback(owner, ctx, 48.0) # Skip 48 hours
    elapsed_delta = datetime.now() - owner.slayer_engine.active_tasks[123]['start_time']
    if elapsed_delta.total_seconds() >= 48 * 3600:
        print("  [PASS] Skipped 48 hours without cap.")
    else:
        print(f"  [FAIL] Skip capped? Total skipped: {elapsed_delta.total_seconds() / 3600}h")

    # Restore originals
    core.storage.load_all_character_states = original_load
    core.storage.save_character_state = original_save

if __name__ == "__main__":
    asyncio.run(test_sovereign_mastery())

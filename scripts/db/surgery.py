import sys
from pathlib import Path
import json

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

try:
    # We need to import the engine from the same file the bot uses
    sys.path.insert(0, str(ROOT_DIR / "EmberHeart" / "discord"))
    import eh_discord
    engine = eh_discord.quest_engine
    
    print(f"Engine Type: {type(engine)}")
    print(f"Engine Completed Set: {engine.completed} (Type: {type(engine.completed)})")
    
    # Check json module
    print(f"JSON Module: {json}")
    print(f"JSON Dumps: {json.dumps}")
    
    # Test serialization
    test_list = ["SQ-01"]
    print(f"Test Dump: {json.dumps(test_list)}")
    
    # Check if we can add a string and dump
    engine.completed.add("DIAGNOSTIC_TEST")
    print(f"Dump after add: {json.dumps(list(engine.completed))}")
    
except Exception as e:
    import traceback
    traceback.print_exc()

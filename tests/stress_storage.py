import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from core.storage import save_json, DB_DIR

async def mock_write(task_id):
    data = {"task_id": task_id, "content": "concurrency test"}
    print(f"Task {task_id} starting...")
    try:
        # Run in thread since save_json is synchronous
        await asyncio.to_thread(save_json, "CONCURRENCY_TEST.json", data)
        print(f"✅ Task {task_id} succeeded")
    except Exception as e:
        print(f"❌ Task {task_id} failed: {e}")

async def main():
    print(f"Starting stress test on {DB_DIR / 'CONCURRENCY_TEST.json'}")
    tasks = [mock_write(i) for i in range(20)]
    await asyncio.gather(*tasks)
    print("\nStress test complete.")

if __name__ == "__main__":
    asyncio.run(main())

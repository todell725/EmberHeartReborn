import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.storage import save_json, DB_DIR

def test_atomic_writes():
    test_file = "test_atomic.json"
    data = {"test": 123}
    
    # 1. Normal save
    save_json(test_file, data)
    path = DB_DIR / test_file
    assert path.exists()
    assert json.loads(path.read_text()) == data
    
    # 2. Check for leftover .tmp files
    tmp_files = list(DB_DIR.glob(f"{test_file}.*.tmp"))
    assert len(tmp_files) == 0, f"Found leaked tmp files: {tmp_files}"
    
    # 3. Simulate failure during write (mocking json.dump to raise)
    # This is tricky without mocking, but if we pass non-serializable data:
    try:
        save_json(test_file, {"non_serializable": lambda x: x})
    except:
        pass
    
    # 4. Check for leftover .tmp files again (B-4 cleanup check)
    tmp_files = list(DB_DIR.glob("*.tmp"))
    assert len(tmp_files) == 0, f"Found leaked tmp files after crash: {tmp_files}"
    
    print("Atomic write test PASSED")

if __name__ == "__main__":
    test_atomic_writes()

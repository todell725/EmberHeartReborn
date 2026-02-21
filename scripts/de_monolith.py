#!/usr/bin/env python3
"""
EmberHeart: Quest De-Monolith Tool
Reads the legacy SIDE_QUESTS_DB.json and extracts each quest into an individual 
JSON file in the docs/quests/ directory.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeMonolith")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_SOURCE = ROOT_DIR / "EmberHeart" / "docs" / "SIDE_QUESTS_DB.json"
TARGET_DIR = ROOT_DIR / "EmberHeartReborn" / "docs" / "quests"

def clean_filename(name: str) -> str:
    """Removes invalid characters for a Windows/Linux filename."""
    import re
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_difficulty_folder(quest: dict) -> Path:
    diff = quest.get("difficulty", "Unknown")
    # Clean the difficulty string as some might be long or weird
    diff = diff.split(" ")[0].capitalize()  # E.g., "Hard (Level 5)" -> "Hard"
    
    valid_dirs = ["Easy", "Medium", "Hard", "Epic", "Elite", "Legendary"]
    if diff not in valid_dirs:
        diff = "Uncategorized"
        
    folder = TARGET_DIR / diff
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def run():
    if not DB_SOURCE.exists():
        logger.error(f"Source DB not found at: {DB_SOURCE}")
        return

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Loading legacy database from {DB_SOURCE}...")
    
    try:
        data = json.loads(DB_SOURCE.read_text(encoding='utf-8'))
        quests = data if isinstance(data, list) else data.get("quests", [])
        
        if not quests:
            logger.warning("No quests found in the database. (Is the format correct?)")
            return
            
        logger.info(f"Found {len(quests)} quests. Beginning extraction...")
        
        extracted = 0
        written_ids = set()
        
        for q in quests:
            qid = q.get("id")
            if not qid:
                logger.warning(f"Quest missing ID, skipping: {str(q)[:100]}...")
                continue
                
            if qid in written_ids:
                logger.warning(f"Duplicate ID found during extraction: {qid}. Overwriting older payload.")
            
            # Determine folder by difficulty
            folder = get_difficulty_folder(q)
            
            # Safe filename: use ID. Make sure it's valid.
            safe_id = clean_filename(qid)
            file_path = folder / f"{safe_id}.json"
            
            # Write out
            file_path.write_text(json.dumps(q, indent=4), encoding='utf-8')
            written_ids.add(qid)
            extracted += 1

        logger.info(f"✅ De-monolith complete. {extracted} quests extracted to {TARGET_DIR}.")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)

if __name__ == "__main__":
    run()

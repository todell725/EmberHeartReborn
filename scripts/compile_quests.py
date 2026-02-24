#!/usr/bin/env python3
"""
EmberHeart: Quest Compiler Tool
Reads all modular quest files from docs/quests/**/*.json and compiles them
into docs/SIDE_QUESTS_DB.json for the game engine.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QuestCompiler")

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT_DIR / "docs" / "quests"
OUTPUT_DB = ROOT_DIR / "docs" / "SIDE_QUESTS_DB.json"


def run():
    if not SOURCE_DIR.exists():
        logger.error(f"Source directory not found at: {SOURCE_DIR}")
        return False

    logger.info(f"Scanning for modular quests in {SOURCE_DIR}...")

    compiled_quests = []
    seen_ids = set()
    errors = 0

    # Glob all JSON files recursively
    for filepath in SOURCE_DIR.rglob("*.json"):
        try:
            quest_data = json.loads(filepath.read_text(encoding="utf-8"))

            # Validation Step 1: Must be a dictionary (a single quest)
            if not isinstance(quest_data, dict):
                logger.error(f"[{filepath.name}] Root must be a dictionary. Skipping.")
                errors += 1
                continue

            # Validation Step 2: Must have an ID
            qid = quest_data.get("id")
            if not qid:
                logger.error(f"[{filepath.name}] Missing 'id' field. Skipping.")
                errors += 1
                continue

            # Validation Step 3: Check for ID collisions
            qid_upper = str(qid).upper()
            if qid_upper in seen_ids:
                logger.error(f"[{filepath.name}] FATAL: Duplicate 'id' found ({qid}). Another file already claimed this ID.")
                errors += 1
                continue

            seen_ids.add(qid_upper)
            compiled_quests.append(quest_data)

        except json.JSONDecodeError as e:
            logger.error(f"[{filepath.name}] Invalid JSON Syntax: {e}")
            errors += 1
        except Exception as e:
            logger.error(f"[{filepath.name}] Unexpected error: {e}")
            errors += 1

    if errors > 0:
        logger.error(f"Compilation aborted due to {errors} validation errors. Fix the source JSON files and try again.")
        return False

    # Validation Step 4: Circular Dependencies (Lightweight pass)
    # Ensure prerequisites point to valid quests that are in this compile batch
    for q in compiled_quests:
        prereqs = q.get("prerequisites", {})
        if isinstance(prereqs, dict):
            required = prereqs.get("quests_completed", [])
            for r_id in required:
                if str(r_id).upper() not in seen_ids:
                    logger.warning(f"[{q.get('id')}] Prerequisite '{r_id}' not found in current compiled set. (Could be an old ID or a typo).")

    # Order the output deterministically (by ID) so git diffs stay clean
    compiled_quests.sort(key=lambda x: str(x.get("id", "")))

    logger.info(f"Validation successful. Compiling {len(compiled_quests)} quests...")

    OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DB.write_text(json.dumps(compiled_quests, indent=4), encoding="utf-8")

    logger.info(f"✅ Compilation complete. Database written to {OUTPUT_DB.name}")
    return True


if __name__ == "__main__":
    run()

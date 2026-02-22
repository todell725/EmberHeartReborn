import json
import logging
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from core.config import ROOT_DIR, DB_DIR

logger = logging.getLogger("EH_Slayer")

class SlayerEngine:
    def __init__(self):
        self.db_path = ROOT_DIR / "EmberHeartReborn" / "docs" / "IDLE_SLAYER_DB.json"
        self.active_path = DB_DIR / "SLAYER_ACTIVE.json"
        self._db = self._load_db()
        self.active_tasks: Dict[int, dict] = self._load_active()

    def _load_db(self) -> List[dict]:
        if not self.db_path.exists():
            logger.warning(f"Slayer DB not found: {self.db_path}")
            return []
        try:
            raw = self.db_path.read_text(encoding='utf-8')
            data = json.loads(raw)
            logger.info(f"Loaded {len(data)} slayer tasks from {self.db_path.name}")
            return data
        except Exception as e:
            logger.error(f"Failed to load slayer tasks: {e}")
            return []

    def _load_active(self) -> Dict[int, dict]:
        if not self.active_path.exists():
            return {}
        try:
            data = json.loads(self.active_path.read_text(encoding='utf-8'))
            processed = {}
            for cid, task in data.items():
                task['start_time'] = datetime.fromisoformat(task['start_time'])
                processed[int(cid)] = task
            return processed
        except:
            return {}

    def _save_active(self):
        try:
            formatted = {}
            for cid, task in self.active_tasks.items():
                task_copy = dict(task)
                task_copy['start_time'] = task_copy['start_time'].isoformat()
                formatted[str(cid)] = task_copy
            self.active_path.write_text(json.dumps(formatted, indent=4), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save active slayer tasks: {e}")

    def get_task(self, task_id: str):
        for task in self._db:
            if task['task_id'].upper() == task_id.upper():
                return task
        return None

    def list_tasks(self, min_level: int = 0):
        if min_level > 0:
            return [t for t in self._db if t['requirements']['min_level'] <= min_level]
        return self._db

    def start_task(self, channel_id: int, task_id: str):
        task = self.get_task(task_id)
        if not task:
            return None
        self.active_tasks[channel_id] = {
            "task_id": task_id.upper(),
            "start_time": datetime.now()
        }
        self._save_active()
        return task

    def get_active(self, channel_id: int):
        return self.active_tasks.get(channel_id)

    def stop_task(self, channel_id: int):
        if channel_id in self.active_tasks:
            del self.active_tasks[channel_id]
            self._save_active()

    def roll_loot(self, drop_table: list, max_drops: int, kills: int = 1) -> List[str]:
        all_drops = []
        for _ in range(kills):
            drops_this_kill = 0
            available = list(drop_table)
            random.shuffle(available)
            for d in available:
                if drops_this_kill >= max_drops:
                    break
                if random.random() <= d['chance']:
                    all_drops.append(d['item'])
                    drops_this_kill += 1
        return all_drops

    def get_party_level(self) -> int:
        try:
            from core.storage import load_all_character_states
            all_states = load_all_character_states()
            # Party = PC- prefixed
            levels = [s.get('level', 1) for s in all_states if s.get('id', '').startswith('PC-')]
            return max(levels) if levels else 1
        except:
            return 1

    def skip_time(self, channel_id: int, hours: float):
        if channel_id in self.active_tasks:
            from datetime import timedelta
            self.active_tasks[channel_id]['start_time'] -= timedelta(hours=hours)
            self._save_active()
            return True
        return False

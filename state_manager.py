import json
import os
from datetime import datetime
from typing import List, Dict, Any

STATE_FILE = "state.json"


class StateManager:
    def __init__(self, filepath: str = STATE_FILE):
        self.filepath = filepath
        self.data: Dict[str, Any] = {"commented_topics": []}
        self._commented_ids = set()
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = {"commented_topics": []}
        self._commented_ids = {
            item["topic_id"] for item in self.data.get("commented_topics", [])
        }

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def has_commented(self, topic_id: int) -> bool:
        return topic_id in self._commented_ids

    def record_comment(self, topic_id: int):
        if topic_id in self._commented_ids:
            return
        self.data.setdefault("commented_topics", []).append({
            "topic_id": topic_id,
            "commented_at": datetime.now().isoformat(),
        })
        self._commented_ids.add(topic_id)
        self.save()

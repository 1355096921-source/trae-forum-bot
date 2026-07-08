import json
import os
from typing import List, Set

SKIP_LIST_FILE = "skip_list.json"


class SkipListManager:
    def __init__(self, filepath: str = SKIP_LIST_FILE):
        self.filepath = filepath
        self.skip_ids: Set[int] = set()
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            ids = data.get("skip_topic_ids", [])
            self.skip_ids = set(int(x) for x in ids if isinstance(x, int) or str(x).isdigit())
        except json.JSONDecodeError as e:
            print(f"警告: 黑名单文件 {self.filepath} 解析失败 (JSON语法错误): {e}")
            print("      黑名单功能暂时失效，请检查文件格式")
            self.skip_ids = set()
        except (IOError, ValueError) as e:
            print(f"警告: 黑名单文件 {self.filepath} 读取失败: {e}")
            self.skip_ids = set()

    def save(self):
        data = {"skip_topic_ids": sorted(self.skip_ids)}
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_skipped(self, topic_id: int) -> bool:
        return topic_id in self.skip_ids

    def add(self, topic_id: int):
        self.skip_ids.add(topic_id)
        self.save()

    def remove(self, topic_id: int):
        self.skip_ids.discard(topic_id)
        self.save()

import json
import os
from typing import Set

USER_BLACKLIST_FILE = "user_blacklist.json"


class UserBlacklistManager:
    def __init__(self, filepath: str = USER_BLACKLIST_FILE):
        self.filepath = filepath
        self.blacklisted_usernames: Set[str] = set()
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            names = data.get("blacklisted_usernames", [])
            self.blacklisted_usernames = set(str(x).strip() for x in names if str(x).strip())
        except json.JSONDecodeError as e:
            print(f"警告: 用户黑名单文件 {self.filepath} 解析失败 (JSON语法错误): {e}")
            print("      用户黑名单功能暂时失效，请检查文件格式")
            self.blacklisted_usernames = set()
        except (IOError, ValueError) as e:
            print(f"警告: 用户黑名单文件 {self.filepath} 读取失败: {e}")
            self.blacklisted_usernames = set()

    def save(self):
        data = {"blacklisted_usernames": sorted(self.blacklisted_usernames)}
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_blacklisted(self, username: str) -> bool:
        return str(username).strip() in self.blacklisted_usernames

    def add(self, username: str):
        username = str(username).strip()
        if username and username not in self.blacklisted_usernames:
            self.blacklisted_usernames.add(username)
            self.save()
            return True
        return False

    def remove(self, username: str):
        username = str(username).strip()
        self.blacklisted_usernames.discard(username)
        self.save()

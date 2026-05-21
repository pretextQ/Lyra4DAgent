"""本地 JSON 存储。

简单的 JSON 文件持久化，用于保存优化历史记录。
"""

import json
import os
from lyra4d.utils.tools import generate_id, get_timestamp


class LocalDB:
    """基于 JSON 文件的简单存储。"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, "history.json")
        os.makedirs(data_dir, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read(self) -> list[dict]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: list[dict]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self, record: dict) -> str:
        """保存一条记录，返回记录 ID。"""
        record_id = generate_id()
        record["id"] = record_id
        record["created_at"] = get_timestamp()

        records = self._read()
        records.append(record)
        self._write(records)
        return record_id

    def get_all(self) -> list[dict]:
        """获取所有记录。"""
        return self._read()

    def get_by_id(self, record_id: str) -> dict | None:
        """根据 ID 获取单条记录。"""
        records = self._read()
        for r in records:
            if r.get("id") == record_id:
                return r
        return None


_db: LocalDB | None = None


def get_db() -> LocalDB:
    """获取数据库单例。"""
    global _db
    if _db is None:
        _db = LocalDB()
    return _db

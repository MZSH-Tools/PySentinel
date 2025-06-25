from __future__ import annotations
from typing import Dict

class TargetEntry:
    """目标软件数据模型"""
    def __init__(self, name: str, path: str = "", minutes: int = 10):
        self.Name: str = name
        self.Path: str = path
        self.Minutes: int = minutes

    @classmethod
    def FromDict(cls, data: Dict) -> "TargetEntry":
        return cls(data["name"], data.get("path", ""), data.get("minutes", 10))

    def ToDict(self) -> Dict:
        return {"name": self.Name, "path": self.Path, "minutes": self.Minutes}

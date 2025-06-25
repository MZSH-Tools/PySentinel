import json, os
from pathlib import Path
from typing import List, Dict
from .TargetEntry import TargetEntry

CONFIG_DIR = Path(os.getenv("APPDATA") if os.name == "nt" else Path.home()/".PySentinel")
CONFIG_PATH = CONFIG_DIR / "config.json"

class ConfigManager:
    """负责加载/保存配置"""
    @staticmethod
    def Load() -> Dict:
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            return {"targets": [], "exportDir": ""}
        except Exception:
            return {"targets": [], "exportDir": ""}

    @staticmethod
    def Save(targets: List[TargetEntry], exportDir: str) -> None:
        data = {
            "targets": [t.ToDict() for t in targets],
            "exportDir": exportDir,
        }
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

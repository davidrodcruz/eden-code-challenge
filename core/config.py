import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()
        self._root_dir = Path(__file__).parent.parent

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    def get_team_config(self, team: str) -> dict[str, Any]:
        config_path = self._root_dir / "tests" / "webui" / "teams" / team / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return self._apply_env_overrides(config)

    def _apply_env_overrides(self, config: dict) -> dict:
        for key, value in list(config.items()):
            env_key = f"EDEN_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                config[key] = self._coerce(env_value)
        return config

    @staticmethod
    def _coerce(value: str) -> Any:
        lowered = value.lower()
        if lowered in ("true", "false"):
            return lowered == "true"
        try:
            return int(value)
        except ValueError:
            return value

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)


config = Config()

import json
from pathlib import Path
from typing import Dict, Any
from functools import reduce

def get_defaults() -> Dict[str, Any]:
    return {
        "asbplayer": {
            "server_url": "http://127.0.0.1:8766"
        },
        "downloads": {
            "downloads_path": str(Path.home() / ".local/cache/sasayaku")
        }
    }


def deep_merge(base: dict, update: dict) -> dict:
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config() -> Dict[str, Any]:
    config = get_defaults()
    paths = [
        Path.cwd() / "config.json",
        Path.home() / ".config" / "sasayaku" / "config.json"
    ]
    paths = [ p for p in paths if p.exists() ]

    if not paths:
        print("Info: No config.json found in PWD or ~/.config/sasayaku.")
        return config

    for path in paths:
        with open(path, 'r') as f:
            loaded_config = json.load(f)
            config = deep_merge(config, loaded_config)
        break

    return config


# Config singleton instance
_CONFIG = load_config()

def CONFIG(path: str, default=None):
    """Fetches a config from path, i.e. 'asbplayer.server_url' """
    try:
        return reduce(
            lambda d, k: d.get(k) if isinstance(d, dict) else None,
            path.split('.'), _CONFIG
        ) or default
    except (AttributeError, TypeError):
        return default

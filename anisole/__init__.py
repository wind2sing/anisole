import json
from pathlib import Path

import toml

BASE_PATH = Path.home() / ".anisole"
BASE_PATH.mkdir(parents=True, exist_ok=True)

CONFIG_FP = BASE_PATH / "anisole.toml"
CONFIG_FP.touch(exist_ok=True)

with open(CONFIG_FP, "r") as f:
    CONFIG = toml.load(CONFIG_FP) or {}
    CONFIG[
        "User-Agent"
    ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36"


TOKEN_FP = BASE_PATH / "token.json"
TOKEN = {}
if TOKEN_FP.exists():
    try:
        with open(TOKEN_FP, "r") as f:
            TOKEN = json.load(f)
    except json.JSONDecodeError:
        pass


def save_config(config):
    with open(CONFIG_FP, "w") as cf:
        toml.dump(CONFIG, cf)

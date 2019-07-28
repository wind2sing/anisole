from pathlib import Path
import toml

BASE_PATH = Path.home() / ".anisole"
BASE_PATH.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = BASE_PATH / "anisole.toml"
CONFIG_FILE.touch(exist_ok=True)

with open(CONFIG_FILE, "r") as f:
    CONFIG = toml.load(CONFIG_FILE)


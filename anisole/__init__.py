from pathlib import Path
import toml

BASE_PATH = Path.home() / ".anisole"
BASE_PATH.mkdir(parents=True, exist_ok=True)

CONFIG_FP = BASE_PATH / "anisole.toml"
CONFIG_FP.touch(exist_ok=True)

with open(CONFIG_FP, "r") as f:
    CONFIG = toml.load(CONFIG_FP)




def save_config(config):
    with open(CONFIG_FP, "w") as cf:
        toml.dump(CONFIG, cf)

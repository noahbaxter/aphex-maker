import tomllib
from pathlib import Path

CONFIG_FILENAME = "config.toml"


def load_config() -> dict:
    # Walk up from cwd looking for config.toml
    path = Path.cwd()
    while True:
        candidate = path / CONFIG_FILENAME
        if candidate.exists():
            with open(candidate, "rb") as f:
                return tomllib.load(f)
        if path.parent == path:
            break
        path = path.parent
    return {}


def get_synth_config() -> dict:
    return load_config().get("synth", {})


def get_prep_config() -> dict:
    return load_config().get("prep", {})

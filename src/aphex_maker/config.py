import tomllib
from importlib.resources import files
from pathlib import Path

CONFIG_FILENAME = "config.toml"


def load_config(config_path: str | None = None) -> dict:
    if config_path:
        p = Path(config_path)
        if p.exists():
            with open(p, "rb") as f:
                return tomllib.load(f)
        # Try as preset name
        preset = files("aphex_maker.presets").joinpath(f"{config_path}.toml")
        if preset.is_file():
            with open(str(preset), "rb") as f:
                return tomllib.load(f)
        raise FileNotFoundError(f"config not found: {config_path}")
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


def get_synth_config(config_path: str | None = None) -> dict:
    return load_config(config_path).get("synth", {})


def get_prep_config(config_path: str | None = None) -> dict:
    return load_config(config_path).get("prep", {})

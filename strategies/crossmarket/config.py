"""The single source of truth for every tunable of the study; it computes nothing."""

from pathlib import Path

import yaml

FILE = Path(__file__).with_name("config.yaml")


def load(overrides: list[str] | None = None) -> dict:
    """Read config.yaml and apply dotted-key overrides.

    Args:
        overrides: Strings like "null.draws=20000", dotted key then value. Values are parsed
            as YAML, so 0.05, true and [1, 2] all arrive as the right type.

    Returns:
        The whole config. Every number the study uses comes from here; a value that is not in
        this dict is a value nobody can change from the panel, which is why none exist.
    """
    cfg = yaml.safe_load(FILE.read_text(encoding="utf-8"))
    for item in overrides or []:
        key, value = item.split("=", 1)
        node = cfg
        *path, leaf = key.split(".")
        for step in path:
            node = node[step]
        node[leaf] = yaml.safe_load(value)
    return cfg


def flatten(cfg: dict) -> dict:
    """The config as one level of dotted keys, which is what the drawer and the cache use.

    Args:
        cfg: What load() returned.

    Returns:
        {"null.draws": 5000, ...}. The cache fingerprints this, so a result computed under
        one setting cannot be read back as an answer to another.
    """
    return {f"{section}.{key}": value
            for section, block in cfg.items() for key, value in block.items()}

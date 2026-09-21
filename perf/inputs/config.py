"""The single source of truth for what the catalogue measures and what it calls a regression."""

from pathlib import Path

import yaml

FILE = Path(__file__).parents[1] / "config.yaml"


def load(overrides: list[str] | None = None) -> dict:
    """Read config.yaml and apply command-line overrides.

    Args:
        overrides: Strings like "harness.repeats=1", dotted key then value. Values are
            parsed as YAML, so 0.05, true and [1, 2] all arrive as the right type.

    Returns:
        The whole config.
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

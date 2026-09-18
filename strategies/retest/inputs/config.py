"""The single source of truth for every tunable of the study; it computes nothing."""

from pathlib import Path

import yaml

FILE = Path(__file__).parents[1] / "config.yaml"


def load(overrides: list[str] | None = None) -> dict:
    """Read config.yaml and apply command-line overrides.

    Args:
        overrides: Strings like "gates.min_pf=1.2", dotted key then value. Values are parsed
            as YAML, so 0.05, true and [1, 2] all arrive as the right type.

    Returns:
        The whole config. Every number the study uses comes from here; a value that is not
        in this dict is a value nobody can change from a UI, which is why none exist.
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
    """The config as one level of dotted keys, which is what the drawer and the manifest use.

    Args:
        cfg: What load() returned.

    Returns:
        {"gates.min_pf": 1.1, ...}. A nested dict is unreadable in a form and unstable as a
        manifest key, and both need to name a single knob.
    """
    out = {}
    for section, body in cfg.items():
        if isinstance(body, dict):
            out.update({f"{section}.{key}": value for key, value in body.items()})
        else:
            out[section] = body
    return out

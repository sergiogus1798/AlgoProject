"""The study's knobs, and the batch it is run on."""

from pathlib import Path

import yaml

from core.paths import ROOT

CONFIG = ROOT / "strategies" / "parameterCloud" / "config.yaml"


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds, each override parsed as YAML so numbers stay numbers.
    """
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for item in overrides:
        dotted, raw = item.split("=", 1)
        section, key = dotted.split(".", 1)
        cfg[section][key] = yaml.safe_load(raw)
    return cfg

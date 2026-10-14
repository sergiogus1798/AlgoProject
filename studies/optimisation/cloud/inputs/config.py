"""The study's knobs."""

from typing import Any
from pathlib import Path

from core.study import config as study_config
from engines.variants import filters
from ledger import thresholds

CONFIG = Path(__file__).parents[1] / "config.yaml"


def config(overrides: list[str]) -> dict[str, Any]:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them; each keeps
            the type of the value it replaces (core.study.config).

    Returns:
        What config.yaml holds, each `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares, plus `floor_is_per_param`: the inside trade floor
        the WFC uses (`engines/variants/config.yaml#panel`), so the two read one cloud.
    """
    cfg = thresholds.fill(study_config.load(CONFIG, []))
    cfg["floor_is_per_param"] = filters.knobs()["floor_is_per_param"]
    return study_config.apply(cfg, overrides)

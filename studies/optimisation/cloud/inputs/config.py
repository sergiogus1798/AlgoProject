"""The study's knobs, and the batch it is run on."""

from pathlib import Path

from core.study import config as study_config
from ledger import thresholds

CONFIG = Path(__file__).parents[1] / "config.yaml"


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them; each keeps
            the type of the value it replaces (core.study.config).

    Returns:
        What config.yaml holds, each `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares.
    """
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)

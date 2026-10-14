"""Read this study's config.yaml, beside the batch-reading knobs it shares with the CSCV."""

from typing import Any
from pathlib import Path

from core.study import config as study_config
from ledger import thresholds

HERE = Path(__file__).resolve().parent.parent
SHARED = HERE.parents[2] / "engines" / "variants" / "config.yaml"


def load(overrides: list[str] | None = None) -> dict[str, Any]:
    """The study's tunables, the panel's floors included.

    Args:
        overrides: "section.key=value" strings; each keeps the type of the value it replaces
            (core.study.config), whichever of the two files the key lives in.

    Returns:
        One dict: engines/variants/config.yaml, then this study's own config.yaml over it,
        every `ledger:<key>` replaced by the number ledger/thresholds.yaml declares.
    """
    cfg = thresholds.fill(
        {**study_config.load(SHARED, []), **study_config.load(HERE / "config.yaml", [])}
    )
    return study_config.apply(cfg, overrides or [])

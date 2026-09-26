"""Read this study's config.yaml, beside the batch-reading knobs it shares with the WFC."""

from pathlib import Path

from core.study import config as study_config
from ledger import thresholds

HERE = Path(__file__).resolve().parent.parent
SHARED = HERE.parents[2] / "engines" / "variants" / "config.yaml"


def load(overrides: list[str] | None = None) -> dict:
    """The study's tunables, the shared trade floor and split included.

    Args:
        overrides: "section.key=value" strings; each keeps the type of the value it replaces
            (core.study.config), whichever of the two files the key lives in.

    Returns:
        One dict: engines/variants/config.yaml, then this study's own config.yaml over it,
        each `ledger:<key>` replaced by the number `ledger/thresholds.yaml` declares.
    """
    cfg = thresholds.fill({**study_config.load(SHARED, []),
                           **study_config.load(HERE / "config.yaml", [])})
    return study_config.apply(cfg, overrides or [])

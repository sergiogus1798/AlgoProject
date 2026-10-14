"""Read this study's config.yaml, beside the panel floors it shares with the WFC and the CSCV."""

from typing import Any
from pathlib import Path

from core.study import config as study_config
from ledger import thresholds

HERE = Path(__file__).resolve().parent.parent
SHARED = HERE.parents[2] / "engines" / "variants" / "config.yaml"


def load(overrides: list[str] | None = None) -> dict[str, Any]:
    """The study's tunables, the panel's floors included.

    Args:
        overrides: "section.key=value" strings; each keeps the type of the value it replaces.

    Returns:
        One dict: the `panel` section of engines/variants/config.yaml, then this study's own
        config.yaml, every `ledger:<key>` replaced by the number ledger/thresholds.yaml declares.
    """
    cfg = thresholds.fill(
        {
            "panel": study_config.load(SHARED, [])["panel"],
            **study_config.load(HERE / "config.yaml", []),
        }
    )
    return study_config.apply(cfg, overrides or [])

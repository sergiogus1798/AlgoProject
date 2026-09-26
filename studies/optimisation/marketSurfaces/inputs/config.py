"""Read this study's config.yaml, beside the trade floor it shares with the WFC and the CSCV."""

from pathlib import Path

from core.study import config as study_config

HERE = Path(__file__).resolve().parent.parent
SHARED = HERE.parents[2] / "engines" / "variants" / "config.yaml"


def load(overrides: list[str] | None = None) -> dict:
    """The study's tunables, the shared trade floor included.

    Args:
        overrides: "key=value" strings; each keeps the type of the value it replaces.

    Returns:
        One dict: `min_trades` from engines/variants/config.yaml, then this study's own
        config.yaml over it. The WFC's `split_mode` is left behind on purpose: a surface is
        read per segment, never across a split.
    """
    shared = study_config.load(SHARED, [])
    cfg = {"min_trades": shared["min_trades"],
           **study_config.load(HERE / "config.yaml", [])}
    return study_config.apply(cfg, overrides or [])

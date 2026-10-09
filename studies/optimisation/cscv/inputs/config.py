"""Read this study's config.yaml, its `ledger:` references filled."""

from pathlib import Path

from core.study import config as study_config
from ledger import thresholds

HERE = Path(__file__).resolve().parent.parent


def load(overrides: list[str] | None = None) -> dict:
    """The study's tunables.

    Args:
        overrides: "section.key=value" strings; each keeps the type of the value it replaces
            (core.study.config).

    Returns:
        config.yaml with every `ledger:<key>` replaced by the number ledger/thresholds.yaml
        declares, then the overrides.
    """
    cfg = thresholds.fill(study_config.load(HERE / "config.yaml", []))
    return study_config.apply(cfg, overrides or [])

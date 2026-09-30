"""The engine's knobs: config.yaml with the ledger's thresholds filled and any override applied."""

from pathlib import Path

from core.study import config as study_config
from ledger import thresholds

FILE = Path(__file__).parents[1] / "config.yaml"
PAIR_THRESHOLDS = ("pearson", "spearman", "co_loss", "tail", "rolling_whole", "rolling_recent")


def load(overrides: list[str] | None = None) -> dict:
    """Every knob, `ledger:` placeholders filled, then `section.key=value` overrides applied.

    Returns:
        The config, plus `relaxed`: each pair threshold an override moved away from the
        ledger's value, {name: value in force}; empty for a run at the owner's thresholds.
    """
    cfg = study_config.apply(thresholds.fill(study_config.load(FILE, [])), overrides or [])
    cfg["relaxed"] = {k: cfg["pairs"][k] for k in PAIR_THRESHOLDS
                      if cfg["pairs"][k] != thresholds.value(f"portfolio.pairs.{k}")}
    return cfg

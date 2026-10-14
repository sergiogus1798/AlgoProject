"""The engine's knobs: config.yaml with the ledger's thresholds filled and any override applied."""

from pathlib import Path
from typing import Any

from core.study import config as study_config
from ledger import thresholds

FILE = Path(__file__).parents[1] / "config.yaml"
PAIR_THRESHOLDS = ("pearson", "spearman", "co_loss", "tail", "rolling_whole", "rolling_recent")


def load(overrides: list[str] | None = None) -> dict[str, Any]:
    """Every knob, `ledger:` placeholders filled, then `section.key=value` overrides applied.

    Returns:
        The config, plus `relaxed`: each pair threshold and each verdict threshold
        (`real.null_draws`, `real.null_percentile`) an override moved away from the ledger's
        value, {name: value in force}, and `pseudo_oos2_from` when a test run set it; empty
        for a run at the owner's thresholds on the policy's calendar.
    """
    cfg = study_config.apply(thresholds.fill(study_config.load(FILE, [])), overrides or [])
    if cfg["weights"]["method"] != "equal":
        raise SystemExit(f"weights.method={cfg['weights']['method']}: solo «equal» puede elegirse (PLAN §5.4: otro "
                         "método pasa antes el walk-forward de pesos, construct.wf, y lo selecciona el dueño)")
    cfg["relaxed"] = {k: cfg["pairs"][k] for k in PAIR_THRESHOLDS
                      if cfg["pairs"][k] != thresholds.value(f"portfolio.pairs.{k}")}
    cfg["relaxed"].update({f"real.{k}": cfg["real"][k] for k in ("null_draws", "null_percentile")
                           if cfg["real"][k] != thresholds.value(f"portfolio.verdict.{k}")})
    if cfg["calendar"]["pseudo_oos2_from"]:
        cfg["relaxed"]["pseudo_oos2_from"] = str(cfg["calendar"]["pseudo_oos2_from"])
    return cfg

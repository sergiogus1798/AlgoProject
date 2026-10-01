"""One WFM export's whole reading: what the windows allow, the correlation, and the drift."""

from pathlib import Path

import pandas as pd

from core import assetdata
from studies.optimisation.wfm.inputs import export
from studies.optimisation.wfm.measure import correlation, drift, gaterule
from studies.optimisation.wfm.model import windows
from studies.optimisation.wfm.verdict import call


def read(directory: Path, settings: dict, only: str | None = None) -> dict:
    """Everything the study concludes about one export.

    Args:
        directory: The export's `wfm/` folder.
        settings: The parsed `config.yaml`.
        only: One strategy's name, to correlate, score and bootstrap that one alone.

    Returns:
        The window shapes, the per-cell correlations, the drift tables, and one verdict
        per strategy. `render` formats it and recomputes nothing. With `only`, every
        per-strategy number is the one the whole export gives it: the window shapes and
        the drift's parameter spread stay the export's, because the population run reads
        them across strategies.
    """
    read_cfg, measure_cfg = settings["read"], settings["measure"]
    metric = read_cfg["metric"]
    correlation.MIN_STEPS = measure_cfg["min_steps"]

    everything = export.steps(directory, read_cfg["drop_future"])
    steps = everything[everything["strategy"] == only] if only else everything
    chosen = export.chosen(directory)
    shapes = windows.shape(everything)
    cells = correlation.per_cell(steps, metric)
    moves = drift.per_step(chosen)
    drift_summary = drift.summary(moves, chosen).set_index("strategy")
    warning = windows.length_warning(shapes, metric)

    # The pass/fail matrix (feedback §8.3, encargo 37): every condition SQX judged each cell
    # by, with the rule the strategy carries; an older export falls back to `_build.yaml`.
    wfm_doctrine = assetdata.doctrine()["wfm"]
    matrix = export.cells(directory)
    checked = export.conditions(directory)
    if checked is None:
        checked = gaterule.legacy(matrix, wfm_doctrine["conditions"])
    checked = checked[checked["strategy"] == only] if only else checked
    rules = export.rules(directory)
    if "threshold_pct" not in rules:
        rules = rules.assign(threshold_pct=wfm_doctrine["threshold_pct"],
                             rows=wfm_doctrine["grid_passing_size"],
                             cols=wfm_doctrine["grid_passing_size"],
                             min_squares=wfm_doctrine["min_squares"])
    objectives = export.objectives(directory)

    verdicts = {}
    for strategy in cells["strategy"].unique():
        got = correlation.pooled(cells[cells["strategy"] == strategy],
                                 measure_cfg["confidence"], measure_cfg["n_resamples"],
                                 measure_cfg["seed"])
        verdicts[strategy] = call.call(got, drift_summary.loc[strategy].to_dict(),
                                       settings["verdict"])

    trades = export.trades(directory)
    return {"source": str(directory), "metric": metric,
            "shapes": shapes, "independence": windows.independence(shapes),
            "cells": cells, "verdicts": verdicts, "warning": warning,
            "drift": drift_summary.reset_index(), "stability": drift.stability(chosen),
            "by_runs": correlation.by_axis(cells, "runs"),
            "by_oos": correlation.by_axis(cells, "oos_pct"),
            "companions": companions(steps, cells, read_cfg, measure_cfg),
            "checked": checked, "scored": gaterule.score(checked),
            "rules": rules[["threshold_pct", "rows", "cols", "min_squares"]],
            "sqx_failed": rules["sqx_failed"].to_dict() if "sqx_failed" in rules else {},
            "objectives": objectives,
            "trades": trades if not only else trades[trades["strategy"] == only]}


def companions(steps: pd.DataFrame, cells: pd.DataFrame, read_cfg: dict,
               measure_cfg: dict) -> pd.DataFrame:
    """The same correlation on the other metrics, as a check that the verdict is not one.

    Args:
        steps: Output of `inputs.export.steps`.
        cells: Output of `measure.correlation.per_cell` for the main metric.
        read_cfg: The `read` block of `config.yaml`.
        measure_cfg: The `measure` block.

    Returns:
        One row per (strategy, metric) with the pooled correlation and its interval.

        A verdict that only holds on the metric it was read on is a property of that
        metric. This is the cheapest way to find that out, and it costs one more groupby.
    """
    rows = []
    for metric in [read_cfg["metric"]] + read_cfg["companion_metrics"]:
        per = correlation.per_cell(steps, metric)
        for strategy in cells["strategy"].unique():
            got = correlation.pooled(per[per["strategy"] == strategy],
                                     measure_cfg["confidence"],
                                     measure_cfg["n_resamples"], measure_cfg["seed"])
            rows.append({"strategy": strategy, "metric": metric, "rho": got["rho"],
                         "low": got["low"], "high": got["high"],
                         "share_negative": got["share_negative"]})
    return pd.DataFrame(rows)

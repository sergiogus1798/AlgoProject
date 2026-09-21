"""One WFM export's whole reading: what the windows allow, the correlation, and the drift."""

from pathlib import Path

import pandas as pd

from strategies.walkForwardMatrix.inputs import export
from strategies.walkForwardMatrix.measure import correlation, drift
from strategies.walkForwardMatrix.model import windows
from strategies.walkForwardMatrix.verdict import call


def read(directory: Path, settings: dict) -> dict:
    """Everything the study concludes about one export.

    Args:
        directory: The export's `wfm/` folder.
        settings: The parsed `config.yaml`.

    Returns:
        The window shapes, the per-cell correlations, the drift tables, and one verdict
        per strategy. `render` formats it and recomputes nothing.
    """
    read_cfg, measure_cfg = settings["read"], settings["measure"]
    metric = read_cfg["metric"]
    correlation.MIN_STEPS = measure_cfg["min_steps"]

    steps = export.steps(directory, read_cfg["drop_future"])
    chosen = export.chosen(directory)
    shapes = windows.shape(steps)
    cells = correlation.per_cell(steps, metric)
    moves = drift.per_step(chosen)
    drift_summary = drift.summary(moves, chosen).set_index("strategy")
    warning = windows.length_warning(shapes, metric)

    verdicts = {}
    for strategy in cells["strategy"].unique():
        got = correlation.pooled(cells[cells["strategy"] == strategy],
                                 measure_cfg["confidence"], measure_cfg["n_resamples"],
                                 measure_cfg["seed"])
        verdicts[strategy] = call.call(got, drift_summary.loc[strategy].to_dict(),
                                       settings["verdict"])

    return {"source": str(directory), "metric": metric,
            "shapes": shapes, "independence": windows.independence(shapes),
            "cells": cells, "verdicts": verdicts, "warning": warning,
            "drift": drift_summary.reset_index(), "stability": drift.stability(chosen),
            "by_runs": correlation.by_axis(cells, "runs"),
            "by_oos": correlation.by_axis(cells, "oos_pct"),
            "companions": companions(steps, cells, read_cfg, measure_cfg)}


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

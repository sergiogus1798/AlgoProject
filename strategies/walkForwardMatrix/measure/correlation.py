"""Does what optimises well predict what does well afterwards? Per cell, then pooled honestly."""

import numpy as np
import pandas as pd
from scipy import stats

MIN_STEPS = 5


def per_cell(steps: pd.DataFrame, metric: str) -> pd.DataFrame:
    """One walk-forward correlation per matrix cell.

    Args:
        steps: Output of `inputs.export.steps`, future steps already dropped.
        metric: Bare metric name; `is_` and `oos_` are prefixed here.

    Returns:
        One row per (strategy, runs, oos_pct) with at least MIN_STEPS usable steps: the
        Spearman correlation between the chosen configuration's in-sample result and the
        out-of-sample result it then produced.

        This is the unit of observation. A cell's run windows are disjoint, so its steps
        are separate draws in time; cells re-split the same history, so they are not.
    """
    rows = []
    for key, cell in steps.groupby(["strategy", "runs", "oos_pct"]):
        pair = cell[[f"is_{metric}", f"oos_{metric}"]].dropna()
        if len(pair) < MIN_STEPS:
            continue
        rho = stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1]).statistic
        rows.append({"strategy": key[0], "runs": key[1], "oos_pct": key[2],
                     "n_steps": len(pair), "rho": float(rho)})
    return pd.DataFrame(rows)


def pooled(cells: pd.DataFrame, confidence: float = 0.95,
           n_resamples: int = 9999, seed: int = 0) -> dict:
    """One figure per strategy, with an interval that treats cells as the unit.

    Args:
        cells: Output of `per_cell`.
        confidence: Coverage of the interval.
        n_resamples: Bootstrap draws.
        seed: Fixes the draw.

    Returns:
        The Fisher-z mean of the cell correlations and a bootstrap interval over **cells,
        not steps**.

        Pooling the steps instead would give an interval several times narrower and it
        would be wrong: the 30 cells are 30 re-splits of one history. Even this interval
        is optimistic -- resampling cells treats them as exchangeable when they share
        their underlying data -- so it is a floor on the uncertainty, not a measure of it.
        Fisher-z because correlations do not average linearly.
    """
    rho = cells["rho"].clip(-0.999, 0.999).to_numpy()
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, rho.size, size=(n_resamples, rho.size))
    spread = np.tanh(np.arctanh(rho)[draws].mean(axis=1))
    tail = (1 - confidence) / 2
    return {"cells": int(rho.size), "steps": int(cells["n_steps"].sum()),
            "rho": float(np.tanh(np.arctanh(rho).mean())),
            "low": float(np.quantile(spread, tail)),
            "high": float(np.quantile(spread, 1 - tail)),
            "share_negative": float((rho < 0).mean())}


def by_axis(cells: pd.DataFrame, axis: str) -> pd.DataFrame:
    """How the correlation moves along one axis of the matrix.

    Args:
        cells: Output of `per_cell`.
        axis: `runs` or `oos_pct`.

    Returns:
        Mean, spread and count per level of that axis. Read it against
        `model.windows.length_warning`: the `runs` axis changes the window length, so a
        trend along it on a length-sensitive metric is partly mechanical. And each level
        holds only a handful of cells drawn from the same history, so the spread is
        descriptive, not an error bar.
    """
    return cells.groupby(axis)["rho"].agg(["mean", "std", "count"]).reset_index()

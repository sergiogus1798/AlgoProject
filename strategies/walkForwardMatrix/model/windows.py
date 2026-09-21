"""What the matrix's windows allow you to claim: what overlaps what, and how many observations."""

import numpy as np
import pandas as pd

YEAR = 365.25 * 24 * 3600


def shape(steps: pd.DataFrame) -> pd.DataFrame:
    """Window lengths and overlap, per cell.

    Args:
        steps: Output of `inputs.export.steps`.

    Returns:
        One row per (strategy, runs, oos_pct): the length of each window in years, the
        share of the optimisation window shared with the previous step, and whether any
        two run windows overlap.

        Measured 2026-09-10 on cell 6x20 of `Strategy 1.19.29`: the optimisation windows
        are 8.2 years long and consecutive ones share **6.5 of them, 79 %**, while the run
        windows are disjoint and consecutive. That asymmetry decides every inference in
        this study, so it is measured per cell rather than assumed.
    """
    rows = []
    for key, cell in steps.groupby(["strategy", "runs", "oos_pct"]):
        cell = cell.sort_values("index")
        opt = (cell["optimize_to"] - cell["optimize_from"]).dt.total_seconds()
        run = (cell["run_to"] - cell["run_from"]).dt.total_seconds()
        shared = (cell["optimize_to"].to_numpy()[:-1]
                  - cell["optimize_from"].to_numpy()[1:]) / np.timedelta64(1, "s")
        overlap = int((cell["run_from"].to_numpy()[1:]
                       < cell["run_to"].to_numpy()[:-1]).sum())
        rows.append({"strategy": key[0], "runs": key[1], "oos_pct": key[2],
                     "n_steps": len(cell), "is_years": opt.mean() / YEAR,
                     "oos_years": run.mean() / YEAR,
                     "is_overlap": float(shared.mean() / opt.to_numpy()[:-1].mean()),
                     "oos_overlaps": overlap,
                     "covers_from": cell["run_from"].min(),
                     "covers_to": cell["run_to"].max()})
    return pd.DataFrame(rows)


def independence(shapes: pd.DataFrame) -> dict:
    """What may be pooled, stated as numbers rather than assumed.

    Args:
        shapes: Output of `shape`.

    Returns:
        The unit of observation and why, with the figures behind it.

        Two facts decide it. **Within a cell the run windows are disjoint**, so a cell's
        steps are separate draws in time and a correlation over them is honest at n =
        steps. **Across cells the same history is re-split**, so 30 cells are 30 views of
        one dataset, not 30 observations: pooling their steps into a single correlation
        would report an interval several times narrower than the data supports.

        The optimisation windows overlap heavily either way, so the in-sample side of
        every pair is autocorrelated. That does not bias the correlation, but it is why
        the cell-level figures move together and why their spread is not a standard error.
    """
    span = (shapes["covers_to"].max() - shapes["covers_from"].min()).days / 365.25
    return {"unit": "cell",
            "cells": int(len(shapes)),
            "steps_total": int(shapes["n_steps"].sum()),
            "oos_overlaps_within_cell": int(shapes["oos_overlaps"].sum()),
            "is_overlap_mean": float(shapes["is_overlap"].mean()),
            "history_years": float(span),
            "is_years_range": (float(shapes["is_years"].min()),
                               float(shapes["is_years"].max())),
            "oos_years_range": (float(shapes["oos_years"].min()),
                                float(shapes["oos_years"].max()))}


def length_warning(shapes: pd.DataFrame, metric: str,
                   biased: tuple[str, ...] = ("ReturnDDRatio", "CalmarRatio?", "NetProfit",
                                              "CAGR", "Drawdown", "RecoveryFactor")) -> str:
    """Whether comparing cells on this metric is contaminated by window length.

    Args:
        shapes: Output of `shape`.
        metric: The metric the study is read on.
        biased: Metrics that are not invariant to the length of the window.

    Returns:
        An empty string when the comparison is safe, otherwise the sentence the report
        must carry.

        Total return grows with the horizon and maximum drawdown with its square root, so
        Ret/DD and its relatives grow with window length. The matrix varies that length on
        purpose -- more runs means shorter windows -- so a trend across the `runs` axis on
        one of these metrics is partly the axis itself.
    """
    lo, hi = shapes["is_years"].min(), shapes["is_years"].max()
    if metric not in biased or hi / lo < 1.05:
        return ""
    return (f"`{metric}` no es invariante a la longitud de ventana, y la matriz varía esa "
            f"longitud a propósito: las ventanas de optimización van de {lo:.1f} a "
            f"{hi:.1f} años ({hi / lo:.2f}×). Cualquier tendencia a lo largo del eje "
            f"`runs` es en parte el propio eje.")

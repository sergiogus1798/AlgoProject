"""The shape of each cell's windows: their lengths, their overlap and the dates its runs cover."""

from typing import Any, cast

import numpy as np
import pandas as pd

YEAR = 365.25 * 24 * 3600


def shape(steps: pd.DataFrame) -> pd.DataFrame:
    """Window lengths and overlap, per cell.

    Args:
        steps: Output of `inputs.export.steps`.

    Returns:
        One row per cell — `strategy`, `result` (SQX's name for it), `runs`, `oos_pct`: the
        length of each window in years, the share of the optimisation window shared with
        the previous step, whether any two run windows overlap, and `covers_from` /
        `covers_to`, the first and last date its out-of-sample runs reach.

        Measured 2026-09-10 on cell 6x20 of `Strategy 1.19.29`: the optimisation windows
        are 8.2 years long and consecutive ones share **6.5 of them, 79 %**, while the run
        windows are disjoint and consecutive.
    """
    rows = []
    for key, cell in cast(Any, steps.groupby(["strategy", "result", "runs", "oos_pct"], observed=True)):
        cell = cell.sort_values("index")
        opt = (cell["optimize_to"] - cell["optimize_from"]).dt.total_seconds()
        run = (cell["run_to"] - cell["run_from"]).dt.total_seconds()
        shared = (cell["optimize_to"].to_numpy()[:-1]
                  - cell["optimize_from"].to_numpy()[1:]) / np.timedelta64(1, "s")
        overlap = int((cell["run_from"].to_numpy()[1:]
                       < cell["run_to"].to_numpy()[:-1]).sum())
        rows.append({"strategy": key[0], "result": key[1], "runs": key[2], "oos_pct": key[3],
                     "n_steps": len(cell), "is_years": opt.mean() / YEAR,
                     "oos_years": run.mean() / YEAR,
                     "is_overlap": float(shared.mean() / opt.to_numpy()[:-1].mean()),
                     "oos_overlaps": overlap,
                     "covers_from": cell["run_from"].min(),
                     "covers_to": cell["run_to"].max()})
    return pd.DataFrame(rows)

"""SQX's own Walk-Forward Matrix pass/fail rule, over the conditions the export checked.

Decoded from `SQTradingLib.jar` (`knowhow/conditions/wfm-acceptance.md`): a cell's robustness
score is the percentage of *active* conditions it meets; it passes at `threshold_pct`. The
strategy passes if some `rows x cols` rectangle of cells holds `min_squares` or more passes.
Since 2026-10-01 `export_wfm.py` writes every condition per cell (`conditions.parquet`,
`core.wfmobjectives`) with the rule the strategy ran with. The rule is annotated, never a
judge: the cells are near copies of each other and most of their out-of-sample is data the
selection already saw (`oos_only` removes the part that is plainly in-sample).
"""

from typing import TypedDict

import numpy as np
import pandas as pd

OPS = {">": np.greater, "<": np.less, "<=": np.less_equal, ">=": np.greater_equal}
KEYS = ["strategy", "result", "oos_pct", "runs"]


def score(conditions: pd.DataFrame) -> pd.DataFrame:
    """One row per cell: how many conditions it meets, and its robustness score.

    Args:
        conditions: `inputs.export.conditions()`, one row per cell and condition.

    Returns:
        `KEYS` plus `met`, `active` and `score_pct` (`round(met / active * 100)`, half up as
        SQX's `SQUtils.round`).
    """
    out = (
        conditions.groupby(KEYS, observed=True)["met"]
        .agg(met="sum", active="size")
        .reset_index()
    )
    out["score_pct"] = np.floor(out["met"] / out["active"] * 100 + 0.5).astype(int)
    return out


def oos_only(conditions: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """The conditions with every `score` recomputed on the stitched out-of-sample runs alone.

    Args:
        conditions: `inputs.export.conditions()`.
        cells: `inputs.export.cells()`: `all_<metric>` and `oos_<metric>` per cell.

    Returns:
        `conditions` with `value` and `met` replaced on the `score` family. SQX's score is
        the cell's WHOLE result — its first optimisation window included — over the original
        backtest's; the first window is in-sample by construction, so the score is rescaled
        by oos / all of the same metric. 🔬 2026-10-07, 300 cells of the reference run: the
        condition holds in 71 % of them as SQX computes it and in 34 % out of sample only.
    """
    out = conditions.merge(cells, on=KEYS, how="left", suffixes=("", "_cell"))
    score = (out["family"] == "score").to_numpy()
    value = out["value"].to_numpy(float).copy()
    for metric in out.loc[score, "metric"].unique():
        rows = score & (out["metric"] == metric).to_numpy()
        value[rows] *= (
            out.loc[rows, f"oos_{metric}"] / out.loc[rows, f"all_{metric}"]
        ).to_numpy()
    met = out["met"].to_numpy().copy()
    for op in out.loc[score, "op"].unique():
        rows = score & (out["op"] == op).to_numpy()
        met[rows] = OPS[op](value[rows], out.loc[rows, "threshold"].to_numpy())
    return conditions.assign(value=value, met=met)


class Area(TypedDict):
    """The best rectangle of passed cells: whether it holds enough, how many, corner and centre."""

    passed: bool
    count: int
    corner: tuple[int, int] | None
    centre: tuple[int, int]


def area(
    passed: np.ndarray, scores: np.ndarray, rows: int, cols: int, min_squares: int
) -> Area:
    """SQX's `findBestGroupOfPassedCombinations`, its tie-break and its centre included.

    Args:
        passed: matrix rows (runs) x columns (oos_pct), True where a cell passed.
        scores: Same shape, each cell's `score_pct`.
        rows, cols: The rectangle, `robCombRows x robCombCols`.
        min_squares: How many passes it needs to hold.

    Returns:
        `passed`, `count` (passes in the best rectangle), `corner` (its top-left (i, j),
        None when it does not fit) and `centre` ((i, j) of the recommended cell: the
        rectangle's `(size - 1) // 2` offset — SQX's «recommended combination», which
        nothing here shows: its parameters are optimised on oos2). The first
        best rectangle in row-major order wins a tie. When it does not fit, SQX takes the
        best-scoring single cell and counts it as one, passed or not.
    """
    n_rows, n_cols = passed.shape
    if rows > n_rows or cols > n_cols:
        # SQX walks its result list, which runs down the runs axis first.
        j, i = divmod(int(np.argmax(scores.T)), n_rows)
        return {
            "passed": 1 >= min_squares,
            "count": 1,
            "corner": None,
            "centre": (i, j),
        }
    best, corner = -1, (0, 0)
    for i in range(n_rows - rows + 1):
        for j in range(n_cols - cols + 1):
            count = int(passed[i : i + rows, j : j + cols].sum())
            if count > best:
                best, corner = count, (i, j)
    return {
        "passed": best >= min_squares,
        "count": best,
        "corner": corner,
        "centre": (corner[0] + (rows - 1) // 2, corner[1] + (cols - 1) // 2),
    }

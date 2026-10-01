"""SQX's own Walk-Forward Matrix pass/fail rule, over the conditions the export checked.

Decoded from `SQTradingLib.jar` (`knowhow/conditions/wfm-acceptance.md`): a cell's robustness
score is the percentage of *active* conditions it meets; it passes at `threshold_pct`. The
strategy passes if some `rows x cols` rectangle of cells holds `min_squares` or more passes.
Since 2026-10-01 `export_wfm.py` writes every condition per cell (`conditions.parquet`,
`core.wfmobjectives`) with the rule the strategy ran with; an export older than that holds
only the `oos` family, and `legacy` scores those against `_build.yaml`, saying so.
"""

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
    out = conditions.groupby(KEYS, observed=True)["met"].agg(met="sum", active="size").reset_index()
    out["score_pct"] = np.floor(out["met"] / out["active"] * 100 + 0.5).astype(int)
    return out


def legacy(cells: pd.DataFrame, doctrine: list[dict]) -> pd.DataFrame:
    """An export from before 2026-10-01: the `oos` conditions of `_build.yaml` only.

    Args:
        cells: `inputs.export.cells()`.
        doctrine: The `wfm.conditions` list of `assets/_build.yaml`.

    Returns:
        The shape `inputs.export.conditions()` has, holding 2 of the 10 conditions. With
        fewer active conditions the same `threshold_pct` is easier to clear than in SQX:
        the caller says so.
    """
    rows = [cells[KEYS].assign(condition=i, family="oos", metric=c["metric"], op=c["op"],
                               threshold=c["value"], value=cells[f"oos_{c['metric']}"],
                               met=OPS[c["op"]](cells[f"oos_{c['metric']}"], c["value"]))
            for i, c in enumerate(doctrine) if c["read"] == "oos"]
    return pd.concat(rows, ignore_index=True)


def area(passed: np.ndarray, scores: np.ndarray, rows: int, cols: int,
         min_squares: int) -> dict:
    """SQX's `findBestGroupOfPassedCombinations`, its tie-break and its centre included.

    Args:
        passed: matrix rows (runs) x columns (oos_pct), True where a cell passed.
        scores: Same shape, each cell's `score_pct`.
        rows, cols: The rectangle, `robCombRows x robCombCols`.
        min_squares: How many passes it needs to hold.

    Returns:
        `passed`, `count` (passes in the best rectangle), `corner` (its top-left (i, j),
        None when it does not fit) and `centre` ((i, j) of the recommended cell: the
        rectangle's `(size - 1) // 2` offset — SQX's «recommended combination»). The first
        best rectangle in row-major order wins a tie. When it does not fit, SQX takes the
        best-scoring single cell and counts it as one, passed or not.
    """
    n_rows, n_cols = passed.shape
    if rows > n_rows or cols > n_cols:
        # SQX walks its result list, which runs down the runs axis first.
        j, i = divmod(int(np.argmax(scores.T)), n_rows)
        return {"passed": 1 >= min_squares, "count": 1, "corner": None, "centre": (i, j)}
    best, corner = -1, (0, 0)
    for i in range(n_rows - rows + 1):
        for j in range(n_cols - cols + 1):
            count = int(passed[i:i + rows, j:j + cols].sum())
            if count > best:
                best, corner = count, (i, j)
    return {"passed": best >= min_squares, "count": best, "corner": corner,
            "centre": (corner[0] + (rows - 1) // 2, corner[1] + (cols - 1) // 2)}

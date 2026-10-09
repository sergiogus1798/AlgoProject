"""The detail nobody loads to decide: each market's surface, two parameters at a time, in ranks."""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from core.study import result as envelope
from studies.optimisation.marketSurfaces.contract import words as w

PREFIX = "param_"
LEVELS = [20, 40, 60, 80]


def grid(params: pd.DataFrame, x: str, y: str, values: np.ndarray, keep: np.ndarray,
         mother: str, title: str) -> dict:
    """One market's surface on one pair of parameters.

    Args:
        params: Variants down, one `param_*` column each.
        x, y: The two columns shown.
        values: The market's gross excess, one per variant.
        keep: The market's common set.
        mother: The mother's `variant_id`, marked when she is in the common set.

    Returns:
        A `grid` block: the median percentile rank (0 worst, 100 best) of the variants at
        each pair of levels; an empty cell holds no variant.
    """
    rank = 100 * (rankdata(values[keep]) - 1) / max(keep.sum() - 1, 1)
    cells = params[keep].assign(rank=rank).pivot_table(index=y, columns=x, values="rank", aggfunc="median")
    rows, cols = [str(v) for v in cells.index], [str(v) for v in cells.columns]
    mine = {"row": str(params.at[mother, y]), "col": str(params.at[mother, x]), "label": "madre"}
    return {"kind": "grid", "title": title, "rows": rows, "cols": cols,
            "values": [[None if np.isnan(v) else float(v) for v in row] for row in cells.to_numpy(float)],
            "scale": "discrete", "levels": LEVELS, "labels": None, "note": w.GRID_NOTE,
            "mark": mine if mine["row"] in rows and mine["col"] in cols else None,
            "select": {"par": f"{x.removeprefix(PREFIX)} × {y.removeprefix(PREFIX)}"}}


def tab(params: pd.DataFrame, totals: dict[str, np.ndarray], ok: dict[str, np.ndarray],
        mother: str, names: dict[str, str]) -> dict:
    """Every pair of live parameters on every market with a common set.

    Args:
        params: `inputs.batch.variants`' `params`.
        totals, ok: `one.measure`'s: market -> gross excess per variant, and its common set.
        mother: The mother's `variant_id`.
        names: Market -> how the reader sees it.

    Returns:
        A tab with one selector, the pair; one grid per market under each option.
    """
    live = [c for c in params.columns if params[c].nunique() > 1]
    found = [grid(params, x, y, totals[m], ok[m], mother, names[m])
             for x, y in combinations(live, 2) for m in totals if ok[m].sum() > 1]
    pairs = list(dict.fromkeys(b["select"]["par"] for b in found))
    return envelope.tab("rejillas", "Una superficie por mercado", found, note=w.GRID_NOTE,
                        selectors=[{"key": "par", "label": "Par de parámetros", "options": pairs,
                                    "default": pairs[0]}] if pairs else None)

"""A2/A3 heat maps: the metric over every pair of the most sensitive parameters, theta-zero marked."""

from itertools import combinations

import numpy as np
import pandas as pd

BINS = 6    # cells per axis: 458 variants over 36 cells is ~13 a cell; finer leaves most empty
TOP = 4     # parameters paired, ranked by Sobol total: 4 give 6 grids, 5 would give 10


def _axis(values: pd.Series, origin: float) -> tuple[pd.Series, list[str], str]:
    """One parameter cut into at most BINS equal-width cells.

    Args:
        values: The parameter, one per variant.
        origin: Theta-zero's value of it.

    Returns:
        The cell label of every variant, the labels in ascending order, and the label of the
        cell holding theta-zero.
    """
    cut = values if values.nunique() <= BINS else pd.cut(values, BINS)
    text = lambda v: f"{v.left:.3g}–{v.right:.3g}" if isinstance(v, pd.Interval) else f"{v:g}"
    labels = [text(v) for v in sorted(cut.unique())]
    out = cut.map(text).astype(str)
    return out, labels, text(cut[values == origin].iloc[0])


def pairs(frame: pd.DataFrame, params: list[str], values: np.ndarray, total: np.ndarray,
          metric: str) -> list[dict]:
    """One grid per pair among the TOP parameters by Sobol total.

    Args:
        frame: The cloud's metric panel, with `origin` and the `param_` columns.
        params: The live parameters, in the order `total` is in.
        values: The metric, one per row of `frame`.
        total: Sobol total index of each of `params`.
        metric: The metric's name as the owner reads it.

    Returns:
        `grid` blocks, red to green, sharing one colour range so they compare; each cell is
        the median of the variants that fall in it and the chosen point is marked θ₀.
    """
    top = [params[i] for i in np.argsort(total)[::-1][:TOP]]
    origin = frame[frame["origin"]].iloc[0]
    axes = {p: _axis(frame[p], origin[p]) for p in top}
    cells = {}
    for x, y in combinations(top, 2):
        both = pd.DataFrame({"x": axes[x][0], "y": axes[y][0], "v": values})
        cells[x, y] = both.pivot_table(index="y", columns="x", values="v", aggfunc="median") \
            .reindex(index=axes[y][1], columns=axes[x][1])
    lo = min(np.nanmin(c.to_numpy()) for c in cells.values())
    hi = max(np.nanmax(c.to_numpy()) for c in cells.values())
    return [{"kind": "grid", "title": f"{y[6:]} contra {x[6:]}", "rows": axes[y][1],
             "cols": axes[x][1], "values": c.to_numpy(dtype=float).tolist(), "labels": None,
             "scale": "sequential", "levels": None, "scale_range": [lo, hi] if lo < hi else None,
             "mark": {"row": axes[y][2], "col": axes[x][2], "label": "θ₀"}, "region": None,
             "note": f"Mediana de {metric} de las variantes de cada celda; gris, sin variantes. "
                     f"Los ejes se parten en {BINS} tramos iguales. Misma escala de color en "
                     f"todos los mapas; θ₀ es el punto elegido."}
            for (x, y), c in cells.items()]

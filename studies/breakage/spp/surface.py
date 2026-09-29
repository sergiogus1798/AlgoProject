"""Two parameters at a time: the metric's median on every cell of their grid, and its top decile."""

from itertools import combinations

import numpy as np
import pandas as pd

from studies.breakage.spp.inputs.export import without_original


def label(value: float) -> str:
    """How a level is written on an axis and in the mark, so the two always agree."""
    return f"{value:g}"


def cell_rank(values: np.ndarray, value: float) -> float:
    """Per cent of the grid's filled cells that sit below `value`; 100 is the best cell."""
    filled = values[~np.isnan(values)]
    return 100 * float((filled < value).mean()) if value == value else float("nan")


def pairs(result: dict, top_share: float) -> list[dict]:
    """Every ordered pair of parameters as a surface of the verdict metric.

    Args:
        result: What `run.read` returned: `grid`, `parameters`, `metric`, `original`.
        top_share: The share of cells that is the plateau; 0.10 is the top decile
            (owner, 2026-09-27).

    Returns:
        One dict per ordered pair (x, y), x != y: `x`, `y`, `surface` (y levels down, x
        levels across, the median over every tuple that used that cell, NaN where none
        did), `cut` (the plateau's floor), and θ₀'s cell: its value, how many tuples fill
        it, its rank among the cells, whether it is on the plateau, and its coordinates.
        (y, x) is the transpose of (x, y), so each unordered pair is aggregated once.

        θ₀ itself is left out of every median and kept on the axes. 🔬 On the three USDJPY
        M30 SPPs (2026-09-27) θ₀'s cell held θ₀ alone on every pair with `BBerDeviation1`:
        the SPP never sampled its level again, so the cell was the in-sample pick's own
        score and θ₀ read "on the plateau" by construction. Without it the cell says what
        the neighbours say, or stays empty.
    """
    metric, origin = result["metric"], result["original"]
    grid = without_original(result["grid"])
    axes = {n: sorted(result["grid"][n].unique()) for n in result["parameters"]}
    out = []
    for a, b in combinations(result["parameters"], 2):
        surface = (grid.pivot_table(index=b, columns=a, values=metric, aggfunc="median")
                   .reindex(index=axes[b], columns=axes[a]))
        filled = grid.groupby([b, a]).size()
        for x, y, s in ((a, b, surface), (b, a, surface.T)):
            values = s.to_numpy(dtype=float)
            cut = float(np.nanquantile(values, 1 - top_share))
            mine = float(s.loc[origin[y], origin[x]])
            n = int(filled.get((origin[b], origin[a]), 0))
            quartiles = [float(np.nanquantile(values, q)) for q in (0.25, 0.5, 0.75)]
            out.append({"x": x, "y": y, "surface": s, "cut": cut, "levels": quartiles + [cut],
                        "origin": {"x": origin[x], "y": origin[y], "value": mine, "n": n,
                                   "rank": cell_rank(values, mine), "plateau": bool(mine >= cut)}})
    return out


def origin_table(found: list[dict]) -> pd.DataFrame:
    """θ₀ on each unordered pair: its cell, the plateau's floor and whether it is on it."""
    seen = [p for p in found if p["x"] < p["y"]]
    return pd.DataFrame([{"eje X": p["x"], "eje Y": p["y"], "θ₀": p["origin"]["value"],
                          "tuplas en su celda": p["origin"]["n"],
                          "suelo de meseta": p["cut"], "rango de θ₀ (%)": p["origin"]["rank"],
                          "en meseta": ("sin vecinos" if not p["origin"]["n"] else
                                        "sí" if p["origin"]["plateau"] else "no")}
                         for p in seen])

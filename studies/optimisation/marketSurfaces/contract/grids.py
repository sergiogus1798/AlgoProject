"""Two parameters at a time on every market, one colour scale, and the consensus of their top deciles."""

from itertools import permutations

import numpy as np
import pandas as pd

from core.study import result
from studies.optimisation.marketSurfaces.contract.tabs import selector, short

PREFIX = "param_"


def label(value: float) -> str:
    """How a level is written on an axis and in the mark, so the two always agree."""
    return f"{value:g}"


def surface(one: pd.DataFrame, x: str, y: str, axes: dict) -> pd.DataFrame:
    """One market's cells on the (x, y) grid: the median over every variant that used them."""
    return (one.pivot_table(index=y, columns=x, values="value", aggfunc="median")
            .reindex(index=axes[y], columns=axes[x]))


def top(values: np.ndarray, share: float) -> np.ndarray:
    """Which cells sit in the grid's top share, NaN where the cell is empty."""
    cut = np.nanquantile(values, 1 - share)
    return np.where(np.isnan(values), np.nan, values >= cut)


def _grid(title: str, s: pd.DataFrame, values: list, mark: dict, note: str,
          select: dict, **scale: object) -> dict:
    """A `grid` block on the axes of `s`, θ₀ marked."""
    return {"kind": "grid", "title": title, "rows": [label(v) for v in s.index],
            "cols": [label(v) for v in s.columns], "values": values, "labels": None,
            "mark": mark, "note": note, "select": select, **scale}


def pair(cells: pd.DataFrame, segment: str, x: str, y: str, axes: dict, order: list[str],
         theta: pd.Series, share: float) -> list[dict]:
    """Every market's grid on one pair and segment, then their consensus.

    Args:
        cells: Usable cells with the variants' parameters joined, bare names.
        segment: One segment read.
        x, y: The two parameters, x across and y down.
        axes: Every level each parameter takes in the batch, so all markets share axes.
        order: Market order, the main one first.
        theta: The mother's parameters, marked as θ₀.
        share: The top share that counts as plateau.

    Returns:
        One `grid` per market, sharing `scale_range`, and the consensus `grid`: in how
        many markets each cell is in that market's top share, levels 0..N.
    """
    mark = {"row": label(theta[y]), "col": label(theta[x]), "label": "θ₀"}
    one = cells[cells["segment"] == segment]
    grids = {m: surface(one[one["market"] == m], x, y, axes) for m in order}
    stack = np.stack([g.to_numpy(dtype=float) for g in grids.values()])
    span = [float(np.nanmin(stack)), float(np.nanmax(stack))]
    tag = {"segment": segment, "x": x, "y": y}
    out = [_grid(f"{short(m)} — {segment}: {y} contra {x}", g, g.to_numpy(dtype=float).tolist(),
                 mark, "Mediana del beneficio neto de las variantes de cada celda en este "
                 "mercado. La misma escala de color en todos los mercados de esta pareja y "
                 "tramo.", {**tag, "market": short(m)}, scale="sequential", levels=None,
                 scale_range=span) for m, g in grids.items()]
    hits = np.stack([top(v, share) for v in stack])
    count = np.where(np.isnan(hits).all(axis=0), np.nan, np.nansum(hits, axis=0))
    s = grids[order[0]]
    mine = count[s.index.get_loc(theta[y]), s.columns.get_loc(theta[x])]
    said = ("θ₀ no tiene variantes en su celda en ningún mercado." if np.isnan(mine) else
            f"La celda de θ₀ está en el decil superior en {int(mine)} de {len(order)} mercados.")
    out.append(_grid(f"Consenso — {segment}: {y} contra {x}", s, count.tolist(), mark,
                     f"En cuántos de los {len(order)} mercados cada celda está en el "
                     f"{100 * share:g} % superior de las celdas de ese mercado. {said}",
                     tag, scale="discrete", levels=list(range(len(order) + 1)),
                     scale_range=None))
    return out


def missing(params: pd.DataFrame, origin: str) -> str | None:
    """Why the pair grids cannot be drawn for this batch, or None when they can.

    Args:
        params: What `inputs.surfaces.parameters` returned.
        origin: The mother's `variant_id`.

    Returns:
        A Spanish sentence for the result's warnings: fewer than two parameters leave no
        pair, and without the mother there is no θ₀ to mark.
    """
    if len([c for c in params.columns if c.startswith(PREFIX)]) < 2:
        return "El lote tiene menos de dos parámetros: no hay rejillas por pareja ni consenso."
    if origin not in set(params["variant_id"]):
        return (f"La madre ({origin}) no está en metrics.parquet: sin θ₀ no se dibujan las "
                f"rejillas por pareja ni el consenso.")
    return None


def tabs(cells: pd.DataFrame, params: pd.DataFrame, segments: list[str], order: list[str],
         origin: str, share: float) -> list[dict]:
    """The per-market grids and the consensus map, over every ordered pair of parameters.

    Args:
        cells: `inputs.surfaces.long`, usable cells only.
        params: `variant_id` and the batch's `param_*` columns, one row per variant.
        segments: The segments read.
        order: Market order, the main one first.
        origin: The mother's `variant_id`: θ₀.
        share: `top_share`, the plateau: the top decile (owner, 2026-09-27).

    Returns:
        Two tabs, «rejillas» (a grid per market, segment and pair) and «consenso». Every
        ordered pair (x, y), x != y, is emitted: the window picks one on two drop-downs.
    """
    params = params.set_index("variant_id").rename(columns=lambda c: c[len(PREFIX):])
    names = list(params.columns)
    axes = {n: sorted(params[n].unique()) for n in names}
    # θ₀ stays on the axes and out of the medians: its own score in its own cell would
    # vouch for itself, and on the main market's build it is the in-sample pick.
    joined = cells[cells["variant_id"] != origin].join(params, on="variant_id")
    blocks = [b for segment in segments for x, y in permutations(names, 2)
              for b in pair(joined, segment, x, y, axes, order, params.loc[origin], share)]
    axis = [{"key": "x", "label": "Eje X", "options": names, "default": names[0]},
            {"key": "y", "label": "Eje Y", "options": names, "default": names[1]}]
    markets = {"key": "market", "label": "Mercado", "options": [short(m) for m in order],
               "default": short(order[0])}
    return [result.tab("rejillas", "Superficies por pareja de parámetros",
                       [b for b in blocks if "market" in b["select"]],
                       [markets, selector(segments), *axis],
                       "Elige mercado, tramo y un parámetro para cada eje. Cada celda es la "
                       "mediana del beneficio neto de las variantes que usaron esa pareja de "
                       "niveles, sin contar a la madre; θ₀, sus parámetros, va marcado. Todos los "
                       "mercados de una pareja y tramo comparten escala de color: el nivel "
                       "depende del coste (provisional), la forma es lo que se compara."),
            result.tab("consenso", "Mapa de consenso",
                       [b for b in blocks if "market" not in b["select"]],
                       [selector(segments), *axis],
                       f"Resume todas las superficies en una: cuántos mercados ponen cada "
                       f"celda en su decil superior (la meseta, {100 * share:g} % de arriba "
                       f"de sus celdas). Una región que viaja se ve como una mancha alta y "
                       f"continua; θ₀ debería caer dentro.")]

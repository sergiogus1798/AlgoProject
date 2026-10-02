"""Two parameters at a time on every market, one colour scale, the plateau region marked."""

from itertools import permutations

import numpy as np
import pandas as pd

from core.study import blocks, result
from studies.optimisation.marketSurfaces.contract.tabs import selector, short
from studies.optimisation.marketSurfaces.measure import region as regionmod

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
          select: dict, region: list[dict] | None = None, **scale: object) -> dict:
    """A `grid` block on the axes of `s`, θ₀ marked."""
    return {"kind": "grid", "title": title, "rows": [label(v) for v in s.index],
            "cols": [label(v) for v in s.columns], "values": values, "labels": None,
            "mark": mark, "note": note, "select": select, "region": region, **scale}


def markets(cells: pd.DataFrame, segment: str, x: str, y: str, axes: dict, order: list[str],
           theta: pd.Series, radius: int, metric_label: str) -> list[dict]:
    """Every market's grid on one pair, segment and metric, the plateau box marked.

    Args:
        cells: Usable cells of ONE metric, with the variants' parameters joined, bare names.
        segment: One segment read.
        x, y: The two parameters, x across and y down.
        axes: Every level each parameter takes in the batch, so all markets share axes.
        order: Market order, the main one first.
        theta: The mother's parameters, marked as θ₀.
        radius: `region_radius`: level steps still counted as the plateau, on the two shown
            parameters — an L∞ ball's projection onto any two of its axes is the L∞ ball of
            the same radius there, so the box needs no lookup into the full plateau's own
            variant set (`measure.region.box`).
        metric_label: What this call's `cells["value"]` holds, e.g. "Net Profit".

    Returns:
        One `grid` per market, sharing `scale_range`, the plateau detected on the main
        asset outlined on every one of them — the same box, never each market's own.
    """
    mark = {"row": label(theta[y]), "col": label(theta[x]), "label": "θ₀"}
    one = cells[cells["segment"] == segment]
    grids = {m: surface(one[one["market"] == m], x, y, axes) for m in order}
    stack = np.stack([g.to_numpy(dtype=float) for g in grids.values()])
    lo, hi = float(np.nanmin(stack)), float(np.nanmax(stack))
    span = [lo, hi] if lo < hi else None      # a flat surface everywhere has no range to share
    s = grids[order[0]]
    box = regionmod.box(s.index.get_loc(theta[y]), s.columns.get_loc(theta[x]),
                        len(s.index), len(s.columns), radius, list(s.index), list(s.columns))
    box = [{"row": label(c["row"]), "col": label(c["col"])} for c in box]
    tag = {"segment": segment, "x": x, "y": y, "metric": metric_label}
    return [_grid(f"{short(m)} — {segment}: {y} contra {x} ({metric_label})", g,
                  g.to_numpy(dtype=float).tolist(), mark,
                  "Mediana de la variante de cada celda en este mercado, sin contar a la "
                  "madre. La misma escala de color en todos los mercados de esta pareja, "
                  "tramo y métrica; el recuadro es la meseta detectada en el mercado "
                  "principal, calcada aquí — nunca el mejor decil propio de este mercado.",
                  {**tag, "market": short(m)}, box, scale="sequential", levels=None,
                  scale_range=span) for m, g in grids.items()]


def consensus(cells: pd.DataFrame, segment: str, x: str, y: str, axes: dict, order: list[str],
             theta: pd.Series, share: float) -> dict:
    """In how many markets a pair's cell is in that market's own top share.

    Args, Returns: as `markets`, but one block: the pre-existing consensus map (owner,
    2026-09-27), kept beside the fixed-region redesign rather than removed — it answers a
    different question (does a good cell travel on its OWN terms) from the region table
    (does the MAIN asset's plateau travel). Always on `config.yaml`'s primary metric.
    """
    mark = {"row": label(theta[y]), "col": label(theta[x]), "label": "θ₀"}
    one = cells[cells["segment"] == segment]
    grids = {m: surface(one[one["market"] == m], x, y, axes) for m in order}
    stack = np.stack([g.to_numpy(dtype=float) for g in grids.values()])
    hits = np.stack([top(v, share) for v in stack])
    count = np.where(np.isnan(hits).all(axis=0), np.nan, np.nansum(hits, axis=0))
    s = grids[order[0]]
    mine = count[s.index.get_loc(theta[y]), s.columns.get_loc(theta[x])]
    said = ("θ₀ no tiene variantes en su celda en ningún mercado." if np.isnan(mine) else
            f"La celda de θ₀ está en el decil superior en {int(mine)} de {len(order)} mercados.")
    return _grid(f"Consenso — {segment}: {y} contra {x}", s, count.tolist(), mark,
                f"En cuántos de los {len(order)} mercados cada celda está en el "
                f"{100 * share:g} % superior de las celdas de ese mercado (su propio top, no "
                f"la meseta fija del principal). {said}",
                {"segment": segment, "x": x, "y": y}, scale="discrete",
                levels=list(range(len(order) + 1)), scale_range=None)


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


def region_table(cells_by_metric: dict[str, pd.DataFrame], plateau: frozenset,
                 segments: list[str], order: list[str], radius: int, delta: float) -> dict:
    """Each market's performance inside the main asset's plateau against outside it.

    Args:
        cells_by_metric: Label to usable cells, for every metric the heatmaps show.
        plateau: What `measure.region.plateau` returned: the mother's own neighbourhood.
        segments: The segments read.
        order: Market order, the main one first.
        radius, delta: `region_radius`/`region_delta`, for the note.

    Returns:
        The «región» tab: one table per metric, a segment selector.
    """
    out = []
    for label_, cells in cells_by_metric.items():
        rows = regionmod.inside_outside(cells, plateau, order, segments)
        for segment in segments:
            one = rows[rows["segment"] == segment].assign(market=lambda f: f["market"].map(short))
            out.append({**blocks.table(
                f"Dentro de la meseta contra fuera — {segment} ({label_})",
                one[["market", "inside_median", "inside_n", "outside_median", "outside_n",
                    "overall_median", "overall_n"]].rename(columns={
                        "market": "mercado", "inside_median": "dentro (mediana)",
                        "inside_n": "dentro (n)", "outside_median": "fuera (mediana)",
                        "outside_n": "fuera (n)", "overall_median": "todas (mediana)",
                        "overall_n": "todas (n)"}),
                f"«Dentro» son las {len(plateau)} variantes de la meseta detectada en el "
                f"mercado principal (a {radius} escalones de la madre en todos los "
                f"parámetros a la vez, sin bajar de {delta:g} de su resultado allí), "
                "trasladada tal cual a este mercado — nunca el top propio de este mercado."),
                "select": {"segment": segment, "metric": label_}})
    return result.tab("region", "Dentro de la meseta del principal", out,
                      [selector(segments),
                       {"key": "metric", "label": "Métrica", "options": list(cells_by_metric),
                        "default": next(iter(cells_by_metric))}],
                      "¿La meseta de parámetros que funciona en el mercado principal sigue "
                      "funcionando, igual de bien, en los otros? La región es fija — la "
                      "misma para todos los mercados — así que una diferencia aquí es del "
                      "mercado, no de dónde se puso el corte.")


def tabs(cells: pd.DataFrame, label: str, alt_cells: pd.DataFrame, alt_label: str,
         params: pd.DataFrame, segments: list[str], order: list[str], origin: str,
         share: float, plateau: frozenset, radius: int, delta: float) -> list[dict]:
    """The per-market grids (two metrics), the consensus map, and the region table.

    Args:
        cells: `inputs.surfaces.long`, usable cells of `config.yaml`'s primary metric.
        label: What `cells["value"]` holds, e.g. "Net Profit".
        alt_cells: The same, of `region_metric` — precomputed so the metric selector needs
            no second run (CONTRACT §1 «selectors»).
        alt_label: What `alt_cells["value"]` holds, e.g. "Profit Factor".
        params: `variant_id` and the batch's `param_*` columns, one row per variant.
        segments: The segments read.
        order: Market order, the main one first.
        origin: The mother's `variant_id`: θ₀.
        share: `top_share`, the consensus map's own plateau (owner, 2026-09-27) — unrelated
            to `plateau`, the region carried over from the main asset.
        plateau: What `measure.region.plateau` returned.
        radius, delta: `region_radius`/`region_delta`.

    Returns:
        Three tabs: «rejillas» (a grid per market, segment, pair and metric, the region
        boxed), «consenso» (unchanged), «región» (the inside/outside table). Every ordered
        pair (x, y), x != y, is emitted: the window picks one on two drop-downs.
    """
    idx = params.set_index("variant_id").rename(columns=lambda c: c[len(PREFIX):])
    names = list(idx.columns)
    axes = {n: sorted(idx[n].unique()) for n in names}
    theta = idx.loc[origin]
    # θ₀ stays on the axes and out of the medians: its own score in its own cell would
    # vouch for itself, and on the main market's build it is the in-sample pick.
    primary = cells[cells["variant_id"] != origin].join(idx, on="variant_id")
    alt = alt_cells[alt_cells["variant_id"] != origin].join(idx, on="variant_id")
    grid_blocks, cons_blocks = [], []
    for segment in segments:
        for x, y in permutations(names, 2):
            grid_blocks += markets(primary, segment, x, y, axes, order, theta, radius, label)
            grid_blocks += markets(alt, segment, x, y, axes, order, theta, radius, alt_label)
            cons_blocks.append(consensus(primary, segment, x, y, axes, order, theta, share))
    axis = [{"key": "x", "label": "Eje X", "options": names, "default": names[0]},
            {"key": "y", "label": "Eje Y", "options": names, "default": names[1]}]
    market_sel = {"key": "market", "label": "Mercado", "options": [short(m) for m in order],
                 "default": short(order[0])}
    metric_sel = {"key": "metric", "label": "Métrica",
                 "options": [label, alt_label], "default": label}
    return [result.tab("rejillas", "Superficies por pareja de parámetros", grid_blocks,
                       [market_sel, metric_sel, selector(segments), *axis],
                       "Elige mercado, métrica, tramo y un parámetro para cada eje. Cada celda "
                       "es la mediana de las variantes que usaron esa pareja de niveles, sin "
                       "contar a la madre; θ₀ va marcado y el recuadro es la meseta detectada "
                       "en el mercado principal, calcada en todos — nunca el mejor decil propio "
                       "de cada mercado (eso es el mapa de consenso). Todos los mercados de una "
                       "pareja, tramo y métrica comparten escala de color: el nivel depende del "
                       "coste (provisional), la forma es lo que se compara."),
            result.tab("consenso", "Mapa de consenso", cons_blocks, [selector(segments), *axis],
                       f"Resume todas las superficies en una: cuántos mercados ponen cada "
                       f"celda en su decil superior (la meseta, {100 * share:g} % de arriba "
                       f"de sus celdas). Una región que viaja se ve como una mancha alta y "
                       f"continua; θ₀ debería caer dentro. Es un mapa distinto del recuadro de "
                       f"«rejillas»: aquí cada mercado se compara contra sí mismo."),
            region_table({label: cells, alt_label: alt_cells}, plateau, segments, order,
                        radius, delta)]

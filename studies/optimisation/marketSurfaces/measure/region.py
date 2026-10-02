"""The plateau detected on the main asset, carried over to every other market (owner, 2026-09-30 §8.5).

"The region" is never each market's own top share: it is computed once, on the main asset's
own build segment, and the same variant set is then looked up on every other market. A point
belongs to it when it is both close to the mother in every parameter at once (the same
level-step box `studies.optimisation.cloud.model.neighbourhood` uses for A1) and close to the
mother's own performance there (the same "company" test `cloud.measure.ensemble.members` uses
for its plateau, C1) — reimplemented here rather than imported, since a helper only two
studies need is not shared yet (`studies/CLAUDE.md`).
"""

import pandas as pd

PARAM = "param_"


def levels(params: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    """Each variant's position on the grid, counted in level steps rather than in units.

    Args:
        params: Indexed by `variant_id`, one `param_*` column per parameter (bare names).
        names: Which columns to place, in a fixed order.

    Returns:
        An integer frame, same index. A parameter's levels are the distinct values the
        batch actually fabricated, so "one step away" means the next point that exists.
    """
    return pd.DataFrame({n: pd.factorize(params[n].to_numpy(), sort=True)[0] for n in names},
                        index=params.index)


def plateau(params: pd.DataFrame, cells: pd.DataFrame, origin: str, main: str,
           radius: int, delta: float) -> frozenset:
    """The mother's plateau on the main asset's build segment: near in every parameter,
    and no worse than a shortfall of its own score there.

    Args:
        params: `inputs.surfaces.parameters`: `variant_id` and every `param_*` column.
        cells: `inputs.surfaces.long`, the metric the region is judged on (whichever
            `config.yaml`'s own `metric` names — the region is defined once, independent of
            which metric a heatmap goes on to show).
        origin: The mother's `variant_id`.
        main: The main feed's name, as `cells["market"]` spells it.
        radius: Level steps still counted as a neighbour, on every parameter at once
            (Chebyshev) — mirrors `cloud.config.neighbourhood.radius`.
        delta: Relative shortfall off the mother's own score still counted as company —
            mirrors `cloud.config.neighbourhood.delta`.

    Returns:
        Variant ids, the mother included. Empty when the mother is missing from the main
        market's build segment (no θ₀, no plateau) or has fewer than two parameters.
    """
    names = [c for c in params.columns if c.startswith(PARAM)]
    if len(names) < 2 or origin not in set(params["variant_id"]):
        return frozenset()
    lv = levels(params.set_index("variant_id")[names], names)
    near = (lv.sub(lv.loc[origin], axis=1).abs() <= radius).all(axis=1)
    build = (cells[(cells["market"] == main) & (cells["segment"] == "build")]
            .set_index("variant_id")["value"])
    if origin not in build.index:
        return frozenset()
    reference = float(build.loc[origin])
    good = build.reindex(lv.index) >= reference - delta * abs(reference)
    return frozenset(lv.index[near & good.fillna(False)])


def box(theta_row: int, theta_col: int, n_rows: int, n_cols: int, radius: int,
       rows: list[str], cols: list[str]) -> list[dict]:
    """The 2D projection of the N-dimensional plateau box onto one shown pair of parameters.

    Args:
        theta_row, theta_col: Index of θ₀ on the grid's own axes (level steps, not values).
        n_rows, n_cols: How many levels each shown parameter has.
        radius: Level steps still counted as a neighbour — the same number `plateau` used;
            an L∞ ball's projection onto any two of its axes is the L∞ ball of the same
            radius on those two, so this needs no lookup into `plateau`'s own variant set.
        rows, cols: The grid's own axis labels, to name the cells `blocks.grid["region"]` wants.

    Returns:
        `[{"row", "col"}, ...]`, one per cell inside the box — the contract's `region` key.
    """
    return [{"row": rows[i], "col": cols[j]}
            for i in range(n_rows) if abs(i - theta_row) <= radius
            for j in range(n_cols) if abs(j - theta_col) <= radius]


def inside_outside(cells: pd.DataFrame, region: frozenset, order: list[str],
                   segments: list[str]) -> pd.DataFrame:
    """Each market's performance inside the region against outside it and overall.

    Args:
        cells: `inputs.surfaces.long`, usable cells of whichever metric is being read.
        region: What `plateau` returned.
        order: Market order, the main one first.
        segments: The segments read.

    Returns:
        One row per (market, segment): median and count inside, outside and overall. A
        market absent from `region`'s own market (never happens: region is variant ids,
        shared by construction) still gets its own three numbers, since performance is
        looked up per market.
    """
    rows = []
    for segment in segments:
        one = cells[(cells["segment"] == segment) & cells["usable"]]
        for market in order:
            g = one[one["market"] == market]
            ins = g[g["variant_id"].isin(region)]["value"]
            out = g[~g["variant_id"].isin(region)]["value"]
            rows.append({"market": market, "segment": segment,
                        "inside_median": ins.median() if len(ins) else None, "inside_n": len(ins),
                        "outside_median": out.median() if len(out) else None, "outside_n": len(out),
                        "overall_median": g["value"].median() if len(g) else None,
                        "overall_n": len(g)})
    return pd.DataFrame(rows)

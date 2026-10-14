"""The equity charts and the per-mother tagging: one block per mother, the window's «Madre» picks it."""

from collections.abc import Callable
from typing import Any, cast

import numpy as np
import pandas as pd

from core import tradestore
from studies.transfer.crossTF import cells

CURVE_POINTS = 50


def _np(label: str, curve: list[float]) -> str:
    """A curve's legend text: its name and its Net Profit (a cumulative P/L ends on it)."""
    return f"{label} · Net Profit {curve[-1]:,.0f}".replace(",", ".")


def per_mother(make: Callable[[pd.DataFrame], dict], table: pd.DataFrame, mothers: list[str]) -> list[dict]:
    """One block per mother, each tagged `select: mother` so the window's «Madre» picks it.

    Args:
        make: Builds a block from one mother's rows of `table`.
        table: A frame with a `mother` column.
        mothers: Every mother, in the selector's order.

    Returns:
        The blocks, one per mother that has rows.
    """
    out = []
    for m in mothers:
        rows = table[table["mother"] == m]
        if len(rows):
            block = make(cast(pd.DataFrame, rows).reset_index(drop=True))
            out.append({**block, "select": {**block.get("select", {}), "mother": m}})
    return out


def blocks(plan: pd.DataFrame, packed: pd.DataFrame) -> list[dict]:
    """Two lines charts per mother, Net Profit in each legend: baseline against its unscaled siblings, and against its
    escaladas (feedback §5, "primero equities"). Tagged `mother`, so the window offers a
    selector instead of drawing every mother's lines on top of each other.

    Args:
        plan: What `inputs.plan` returned.
        packed: What `inputs.trades`/`inputs.gather` returned.

    Returns:
        `lines` blocks, two per mother that has a baseline long enough to draw, none for one
        that traded fewer than two times.
    """
    grid_x = [round(float(p) * 100, 1) for p in np.linspace(0.0, 1.0, CURVE_POINTS)]
    out = []
    for mother, rows_m in plan.groupby("mother", sort=True):
        base_row = rows_m[rows_m["role"] == "baseline"].iloc[0]
        base = cells.curve(tradestore.block(packed, base_row.strategy, base_row.block),
                           CURVE_POINTS)
        if base is None:
            continue
        for role, label, extra in (("unscaled", "sin escalar", []),
                                   ("scaled", "escaladas", [("control", "Control", "reference")])):
            series = [{"label": _np(f"Baseline {base_row.timeframe}", base), "values": base, "role": "real"}]
            for row in cast(Any, rows_m[rows_m["role"] == role].itertuples()):
                c = cells.curve(tradestore.block(packed, row.strategy, row.block), CURVE_POINTS)
                if c is not None:
                    series.append({"label": _np(row.timeframe, c), "values": c, "role": "sim"})
            target = rows_m[rows_m["role"] == "scaled"].set_index("strategy")["timeframe"]
            for extra_role, extra_label, extra_kind in extra:
                for row in cast(Any, rows_m[rows_m["role"] == extra_role].itertuples()):
                    c = cells.curve(tradestore.block(packed, row.strategy, row.block),
                                    CURVE_POINTS)
                    if c is not None:
                        series.append({"label": _np(f"{extra_label} {row.timeframe} (hermana {target.get(row.strategy, '?')})", c),
                                      "values": c, "role": extra_kind})
            if len(series) > 1:
                out.append({"kind": "lines", "title": f"Equity {label}: baseline y la misma estrategia en otros timeframes",
                           "unit": "USD", "x": grid_x, "series": series,
                           "auto_dash_negative": True, "zero_shade": True,
                           "select": {"mother": mother},
                           "note": "Eje X: avance de 0 a 100, no número de operación — las "
                                   "hermanas de otro timeframe no tienen el mismo número de "
                                   "operaciones que la baseline."})
    return out

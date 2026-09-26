"""How much of the spread is actually embedded in the fill price — measured, never assumed.

BLOCKER found in review, 2026-09-26: a single `SPREAD_SHARE = 0.5` applied to every feed was
wrong even for feeds it was never checked against (`knowhow/export/fill-and-pricing.md` itself
says silver and Brent show a ZERO entry offset on the same export gold shows 0.05 on). Measured
here instead of assumed: on `USDJPY_DukasM1_the5ers` the entry offset is 0.002 against a 0.001
declared spread (ratio 2.0, not 0.5); on `XAUUSD_DukasM1_Infinox` it is 1.5-1.6, not 0.5 either —
neither matches the number the old constant borrowed from a different gold dataset. The fill
convention is a property of the feed and the historical task that ran it, not a universal SQX
constant, so it is measured from the same bars and trades every report call already has.
"""

import numpy as np
import pandas as pd

from core.barstore import read as read_bars
from core.paths import bar_source

DIRECTION = {"Buy": 1, "Sell": -1}
MIN_TRADES = 30   # a segment with fewer than this has no median worth trusting


def measure(trades: pd.DataFrame, feed: str, timeframe: str) -> dict:
    """The real spread cost embedded in the fill price, per sample segment.

    Args:
        trades: One harvest's trades, carrying `sample` ("IS"/"OOS").
        feed: SQX feed, e.g. "XAUUSD_DukasM1_Infinox".
        timeframe: The bars the strategies were priced on, e.g. "M30".

    Returns:
        {"IS": price, "OOS": price, ...}: the median entry offset against the bar's own
        Open, in price units, one per sample segment — this IS the round-trip spread cost
        in price units, measured, not derived from any declared configuration.

    Raises:
        SystemExit: No bar library entry for this feed (nothing to measure against), or a
        segment with fewer than MIN_TRADES trades (no median worth trusting). Silence here
        is exactly what let a wrong constant reconcile perfectly while pricing every trade
        wrong; refusing is the fix.
    """
    if not bar_source(feed).exists():
        raise SystemExit(f"edgeCost: no hay barras para {feed!r} en la librería — no se puede "
                         "medir el coste de spread real; no se asume ninguna cifra")
    bars = read_bars(feed, timeframe)
    entry = bars.index.searchsorted(trades["Open time"].to_numpy())
    bar_open = bars["Open"].to_numpy()[entry]
    direction = trades["Type"].astype(str).map(DIRECTION).to_numpy()
    offset = (trades["Open price"].to_numpy() - bar_open) * direction

    out = {}
    for sample, idx in trades.groupby("sample", observed=True).indices.items():
        if len(idx) < MIN_TRADES:
            raise SystemExit(f"edgeCost: sólo {len(idx)} trades en {feed!r}/{sample}, menos de "
                             f"{MIN_TRADES} — no hay medida de spread fiable para ese tramo")
        out[sample] = float(np.median(offset[idx]))
    return out

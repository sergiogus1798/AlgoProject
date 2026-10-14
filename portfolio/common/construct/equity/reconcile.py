"""The rebuild checked against SQX's own daily curve: each day's lowest equity, day by day."""

from typing import TypedDict

import pandas as pd


def low_equity(days: pd.DataFrame) -> pd.Series:
    """Each server day's lowest equity as SQX's curve samples it, from a `days.server_days` table.

    🔬 SQX marks the day's low only while a position is open: a day that ends flat after an
    exit shows the worst wick before it, never the realised level after it (an H1 exit at the
    second bar of the session, 10 of 10 gap days on USA500 H1, 2026-10-06). A flat day shows
    the previous close. `days["low"]` is the economic low and stays for the funded rules.
    """
    close = days["closed"].cumsum() + days["float_end"]
    return close.shift(fill_value=0.0) + days["low_open"].fillna(0.0)


class Reconciled(TypedDict):
    """A rebuilt curve against SQX's: days compared, share exact, the gaps and the verdict."""

    n_days: int
    exact: float
    max_gap: float
    p99_gap: float
    verdict: str


def curve(rebuilt: pd.Series, sqx: pd.Series, tolerance: float, min_share: float) -> Reconciled:
    """Day-by-day agreement of two lowest-equity curves of one leg, over the days both cover.

    Args:
        rebuilt: `low_equity` of the leg's rebuild on the feed's own clock.
        sqx: The same leg's `low` from `sqxcurve`.
        tolerance: Account currency within which a day counts as exact.
        min_share: Share of exact days that licenses the rebuild.

    Returns:
        `n_days`, `exact` (share within tolerance), `max_gap`, `p99_gap` and `verdict` — "ok"
        when `exact` ≥ `min_share`, else "out".
    """
    common = rebuilt.index.intersection(sqx.index)
    gap = (rebuilt.loc[common] - sqx.loc[common]).abs()
    exact = float((gap <= tolerance).mean())
    return {"n_days": int(len(common)), "exact": exact, "max_gap": float(gap.max()),
            "p99_gap": float(gap.quantile(0.99)),
            "verdict": "ok" if exact >= min_share else "out"}

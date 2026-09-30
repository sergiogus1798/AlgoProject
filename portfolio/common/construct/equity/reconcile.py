"""The rebuild checked against SQX's own daily curve: each day's lowest equity, day by day."""

import pandas as pd


def low_equity(days: pd.DataFrame) -> pd.Series:
    """Each server day's lowest equity since the path started, from a `days.server_days` table."""
    close = days["closed"].cumsum() + days["float_end"]
    return close.shift(fill_value=0.0) + days["low"]


def curve(rebuilt: pd.Series, sqx: pd.Series, tolerance: float, min_share: float) -> dict:
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

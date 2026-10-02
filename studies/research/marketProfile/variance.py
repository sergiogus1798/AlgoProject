"""Lo-MacKinlay's variance ratio per asset and timeframe on build, with its sign year by year."""

import numpy as np
import pandas as pd

from studies.research.marketProfile import inputs

HORIZONS = (8, 32)     # bars: a typical hold of the map's measures, and four times it
LEAST = 20             # a year needs this many horizons of bars to be read


def ratio(close: np.ndarray, q: int) -> float:
    """VR(q) of a log close series; NaN when it is shorter than LEAST horizons."""
    steps = np.diff(close)
    if steps.size <= q * LEAST:
        return np.nan
    return float(np.var(close[q:] - close[:-q]) / (q * np.var(steps)))


def table(symbols: list[str], timeframes: list[str]) -> pd.DataFrame:
    """One row per asset, timeframe and horizon.

    Returns:
        `vr` over the whole build segment, `years` read, `years_below_1` (rolling sign: the
        build years in which the ratio is under one), `vr_min` and `vr_max` across years.
    """
    rows = []
    for symbol in symbols:
        m1 = inputs.minute_bars(symbol, 0)
        for timeframe in timeframes:
            bars = inputs.bars(m1, timeframe)
            close, year = np.log(bars["Close"].to_numpy()), bars.index.year.to_numpy()
            for q in HORIZONS:
                per = [v for v in (ratio(close[year == y], q) for y in np.unique(year))
                       if np.isfinite(v)]
                rows.append({"symbol": symbol, "timeframe": timeframe, "q": q,
                             "vr": ratio(close, q), "years": len(per),
                             "years_below_1": int(sum(v < 1 for v in per)),
                             "vr_min": min(per), "vr_max": max(per)})
    return pd.DataFrame(rows)

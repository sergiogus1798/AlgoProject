"""The spread as measured: per minute, per day beside Dukascopy's volatility, per year, per hour."""

import numpy as np
import pandas as pd

BPS = 1e4
QUANTILES = (0.5, 0.75, 0.9, 0.95, 0.99)


def relative(m: pd.DataFrame) -> pd.Series:
    """Each minute's opening spread as a fraction of its bid: what a market order there pays."""
    return m["spread_open"] / m["bid_open"]


def days(m: pd.DataFrame, vol: pd.DataFrame, min_minutes: int) -> pd.DataFrame:
    """One row per full Darwinex day, joined to that day's Dukascopy volatility.

    Args:
        m: `inputs.minutes()`.
        vol: `inputs.volatility()`.
        min_minutes: Days quoting fewer minutes are dropped (holidays, half days).

    Returns:
        Indexed by day: `rel` the mean relative spread over the day's minutes, `spread` the
        mean spread in price, `minutes`, and `rv`, `price` from Dukascopy.
    """
    day = m.index.normalize()
    got = pd.DataFrame({"rel": relative(m).groupby(day).mean(),
                        "spread": m["spread_open"].groupby(day).mean(),
                        "minutes": m["n"].groupby(day).size()})
    got = got[got["minutes"] >= min_minutes].join(vol, how="inner")
    return got[got["rv"] > 0]


def yearly(m: pd.DataFrame, tick: float) -> pd.DataFrame:
    """The spread by calendar year, in points of `assets/`'s tick and in basis points of price."""
    rel, pts = relative(m) * BPS, m["spread_open"] / tick
    year = m.index.year
    return pd.DataFrame({"puntos mediana": pts.groupby(year).median(),
                         "puntos media": pts.groupby(year).mean(),
                         "pb mediana": rel.groupby(year).median(),
                         "pb media": rel.groupby(year).mean(),
                         "precio mediano": m["bid_open"].groupby(year).median(),
                         "minutos": m["n"].groupby(year).size()})


def hours(m: pd.DataFrame) -> pd.Series:
    """Each hour of the day's mean relative spread over the whole day's: the intraday shape.

    Returns:
        24 multipliers indexed by the feed clock's hour. The modelled day is spread over its
        hours with them, so a trade at the rollover is charged the rollover's spread.
    """
    rel = relative(m)
    return rel.groupby(m.index.hour).mean() / rel.mean()


def week_grid(m: pd.DataFrame) -> pd.DataFrame:
    """Mean relative spread in basis points by weekday (rows) and hour (columns)."""
    rel = relative(m) * BPS
    return rel.groupby([m.index.dayofweek, m.index.hour]).mean().unstack()


def quantiles(values: pd.Series) -> dict:
    """The median to the 99th percentile and the mean, one entry each."""
    got = {f"p{int(q * 100)}": float(values.quantile(q)) for q in QUANTILES}
    return {**got, "media": float(values.mean())}


def at(m: pd.DataFrame, when: pd.Series, near_minutes: int) -> pd.Series:
    """The spread a market order placed at each instant found: the first tick at or after it.

    Args:
        m: `inputs.minutes()`.
        when: Instants on the feed clock.
        near_minutes: Farther than this from the instant, the minute found is not that
            order's: NaN is returned and the caller models it.

    Returns:
        Spread in price per instant, aligned on `when`'s index.
    """
    index = m.index.to_numpy()
    pos = np.minimum(index.searchsorted(when.to_numpy()), len(index) - 1)
    near = (index[pos] - when.to_numpy()) <= np.timedelta64(near_minutes, "m")
    near &= index[pos] >= when.to_numpy()
    return pd.Series(np.where(near, m["spread_open"].to_numpy()[pos], np.nan), when.index)

"""The t of a strategy's mean trade, plain or net of the market's own drift over each hold."""

import numpy as np
import pandas as pd

from engines.market.calibrate import atr

# The calendar windows a drift may be measured over: months spanned and the letter of the label.
# Nothing shorter than a quarter: as the window nears a trade's hold its drift IS the trade's move.
WINDOWS = {"year": (12, ""), "semester": (6, "H"), "quarter": (3, "Q")}
NONE = np.empty(0, dtype=np.intp)  # a window the span holds no bar of
# The drift term's variants: (one move per calendar window, the blind trade for the mean bar).
VARIANTS = {"a": (False, False), "b": (True, False), "c": (False, True), "d": (True, True)}


def mean_move(bars: pd.DataFrame, windows: dict) -> dict[str, float]:
    """The market's mean bar-to-bar close change over each sample's window.

    Args:
        bars: One row per bar, indexed by open time, with `Close`.
        windows: {sample: (first, last)} as strings a DatetimeIndex slices by, e.g.
            {"IS": ("2008", "2017"), "OOS": ("2018", "2022")}.

    Returns:
        {sample: mean change in price units per bar}.
    """
    change = bars["Close"].diff()
    return {sample: float(change[first:last].mean()) for sample, (first, last) in windows.items()}


def drift(trades: pd.DataFrame, bars: pd.DataFrame, move: dict, point_value: float) -> np.ndarray:
    """What the market's drift alone paid each trade for being in it, at the trade's own size.

    Args:
        trades: `Open time`, `Close time`, `Type`, `Size` and `sample`.
        bars: The bars of the strategy's own timeframe, indexed by open time.
        move: What mean_move() returned.
        point_value: Account currency per 1.0 of price per 1.0 lot.

    Returns:
        Per trade, direction x mean move of its sample x bars held x size x point value: the
        mean term `core.significance.footprint` gives a same-footprint random trader.
    """
    grid = bars.index.to_numpy()
    held = (np.searchsorted(grid, trades["Close time"].to_numpy(), side="right")
            - np.searchsorted(grid, trades["Open time"].to_numpy(), side="right"))
    side = np.where(trades["Type"].astype(str) == "Sell", -1.0, 1.0)
    return side * pd.Series(trades["sample"]).map(move).to_numpy() * held * trades["Size"].to_numpy() \
        * point_value


def t(trades: pd.DataFrame, value: str) -> pd.DataFrame:
    """The t of the mean of one per-trade column, per strategy.

    Args:
        trades: One sample's trades, already in time order within each `identity`.
        value: The column to test, in account currency.

    Returns:
        Indexed by identity: `n`, `iid` (mean / sd x sqrt(n)) and `ar1`, the same t at the
        AR(1) effective n(1 - rho) / (1 + rho), capped at n so that negative autocorrelation
        cannot manufacture observations, and floored at 2.
    """
    by = trades.groupby("identity", sort=False)[value]
    n = by.size()
    x = (trades[value] - by.transform("mean")).to_numpy()
    keys = trades["identity"].to_numpy()
    lagged = np.where(np.r_[False, keys[1:] == keys[:-1]], x * np.r_[0.0, x[:-1]], 0.0)
    sums = pd.DataFrame({"g0": x * x, "g1": lagged}).groupby(keys, sort=False).sum().reindex(n.index)
    rho = sums["g1"] / sums["g0"]
    effective = pd.Series(np.minimum(n * (1 - rho) / (1 + rho), n)).clip(lower=2)
    iid = by.mean() / by.std(ddof=1) * np.sqrt(n)
    return pd.DataFrame({"n": n, "iid": iid, "ar1": iid * np.sqrt(effective / n)})


def calendar(time: pd.Series | pd.DatetimeIndex, window: str) -> np.ndarray:
    """The calendar window each stamp falls in.

    Args:
        time: Datetimes.
        window: A key of `WINDOWS`; anything else is refused.

    Returns:
        One label per stamp: "2020", "2020H1" or "2020Q3".
    """
    assert window in WINDOWS, f"drift window {window!r}: year, semester or quarter, nothing shorter"
    months, letter = WINDOWS[window]
    stamps = pd.Series(pd.DatetimeIndex(time)).dt
    year = stamps.year.astype(str)
    part = ((stamps.month - 1) // months + 1).astype(str)
    return np.asarray(year + letter + part if letter else year)


def drift_term(trades: pd.DataFrame, bars: pd.DataFrame, span: tuple[str, str], window: str,
               variant: str, point_value: float) -> tuple[np.ndarray, np.ndarray]:
    """What the market paid each trade for being in it, under one of the four drift terms.

    Args:
        trades: One sample's trades: `Open time`, `Close time`, `Type` and `Size`.
        bars: The bars of the strategy's own timeframe, the whole file, indexed by open time.
        span: (first, last) of the sample, as strings a DatetimeIndex slices by.
        window: A key of `WINDOWS`.
        variant: A key of `VARIANTS`. `a` is drift() with one mean move for the whole span;
            `b` the same with one mean move per calendar window, each trade taking that of
            the window it opened in; `c` side x size x point value x W(h), W(h) the mean of
            open[j + h] - open[j] over every bar j of the span weighted by 1 / ATR at j —
            what a trade of that hold earns entered blind and sized as the doctrine sizes;
            `d` is `c` with W(h) taken over the bars of the trade's own window.
        point_value: Account currency per 1.0 of price per 1.0 lot.

    Returns:
        (drift per trade in account currency, each trade's window label). `a` and `b` assume
        every bar held was a mean bar, which leaves a break-even trader sized by 1 / ATR a
        remainder of opposite sign for longs and shorts; `c` and `d` do not.

        The drift is the span's (or the window's) BENCHMARK: it averages bars after each
        trade's entry, so it is what the excess is measured against, never information a
        decision could have used.
    """
    per_window, blind = VARIANTS[variant]
    label = calendar(pd.Series(trades["Open time"]), window)
    inside = np.arange(len(bars))[bars.index.slice_indexer(*span)]
    pool = calendar(pd.DatetimeIndex(bars.index[inside]), window) if per_window else np.full(len(inside), "")
    mine = trades.assign(sample=label if per_window else "")
    if not blind:
        move = bars["Close"].diff().iloc[inside].groupby(pool).mean().to_dict()
        return drift(mine, bars, move, point_value), label
    opened, grid = bars["Open"].to_numpy(), bars.index.to_numpy()
    weight = 1.0 / np.r_[np.nan, atr(bars)[:-1]]
    weight[~np.isfinite(weight)] = 0.0
    held = (np.searchsorted(grid, trades["Close time"].to_numpy(), side="right")
            - np.searchsorted(grid, trades["Open time"].to_numpy(), side="right"))
    keys = pd.MultiIndex.from_arrays([mine["sample"].to_numpy(), held])
    moved, bars_of = {}, pd.Series(inside).groupby(pool).indices
    for group, hold in keys.unique():
        at = inside[bars_of.get(group, NONE)]
        at = at[at + hold < len(opened)]
        moved[group, hold] = (((opened[at + hold] - opened[at]) * weight[at]).sum()
                              / weight[at].sum())
    side = np.where(trades["Type"].astype(str) == "Sell", -1.0, 1.0)
    return (side * trades["Size"].to_numpy() * point_value
            * pd.Series(moved).reindex(keys).to_numpy(), label)


def skew_kurt_t(s: np.ndarray, n: np.ndarray, skew: np.ndarray, kurt: np.ndarray) -> np.ndarray:
    """The t of a mean with the Probabilistic Sharpe Ratio's standard error.

    Args:
        s: Mean over standard deviation, the deviation taken over n (not n - 1).
        n: Observations.
        skew: Third standardised moment; 0 when symmetric.
        kurt: Fourth standardised moment; 3 for a normal.

    Returns:
        s x sqrt(n - 1) over sqrt(1 - skew x s + (kurt - 1) / 4 x s^2). The numerator alone is
        the usual mean / sd(n - 1) x sqrt(n); a loss tail (negative skew) on a positive mean
        lowers it. The radicand cannot go negative: kurt >= skew^2 + 1 for any sample.
    """
    return s * np.sqrt(n - 1) / np.sqrt(1 - skew * s + (kurt - 1) / 4 * s * s)


def t_skew_kurt(trades: pd.DataFrame, value: str) -> pd.DataFrame:
    """t() with its standard error corrected for the column's own skewness and kurtosis.

    Args:
        trades: One sample's trades, already in time order within each `identity`.
        value: The column to test, in account currency.

    Returns:
        t()'s frame: `n`, `iid` — skew_kurt_t() of the column's own moments — and `ar1`, that
        one at t()'s AR(1) effective n.
    """
    plain = t(trades, value)
    by = trades.groupby("identity", sort=False)[value]
    x = trades[value] - by.transform("mean")
    m = (pd.DataFrame({k: x ** k for k in (2, 3, 4)})
         .groupby(trades["identity"].to_numpy(), sort=False).mean().reindex(plain.index))
    iid = skew_kurt_t(by.mean() / np.sqrt(m[2]), plain["n"].to_numpy(), m[3] / m[2] ** 1.5,
                      m[4] / m[2] ** 2)
    return plain.assign(iid=iid, ar1=iid * plain["ar1"] / plain["iid"])

"""The one definition of Sharpe, drawdown, profit factor and years that every step, the window and MT5 share."""

from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

TRADING_DAYS = 252  # SQX's SharpeRatio: weekday rows x sqrt(252)
YEAR_DAYS = 365.25
FLAT = 1e-12  # a deviation at or below this share of the largest |value| is float noise


def sharpe(
    returns: npt.ArrayLike,
    periods_per_year: float,
    axis: int = -1,
) -> Any:  # float for one series, ndarray for several
    """Mean over sample deviation (ddof=1), annualised by sqrt(periods_per_year).

    Args:
        returns: One return per period along `axis`; any number of series on the other axes.
        periods_per_year: 252 for SQX's daily rows, 52 for weekly, 1 for a per-period
            (per-trade, per-day unannualised) ratio. Always explicit: the scale is the trap.

    Returns:
        A float for one series, an array for several. NaN with fewer than two returns or a
        flat series (deviation 0 up to float noise): there is no ratio, and an infinite one
        would rank as the best of all.
    """
    x = np.asarray(returns, dtype=np.float64)
    shape = np.delete(x.shape, axis % x.ndim) if x.ndim else ()
    if x.ndim == 0 or x.shape[axis] < 2:
        out = np.full(shape, np.nan)
    else:
        sd = x.std(axis=axis, ddof=1)
        flat = sd <= FLAT * np.abs(x).max(axis=axis)
        out = np.divide(
            x.mean(axis=axis), sd, out=np.full_like(sd, np.nan), where=~flat
        )
        out *= np.sqrt(periods_per_year)
    return float(out) if out.ndim == 0 else out


def weekday_pnl(pnl: npt.ArrayLike, closed: npt.ArrayLike) -> pd.Series:
    """P&L per trading day, Monday to Friday from the first close to the last, empty days at 0.

    Args:
        pnl: Account currency per trade.
        closed: Each trade's close time, same order as `pnl`.

    Returns:
        Indexed by day. A trade closing on a weekend counts on the next Monday. This is the
        series SQX's SharpeRatio reads; fixed sizing makes daily P&L and daily return the same
        series up to a constant, so `sharpe(weekday_pnl(...), TRADING_DAYS)` is the owner's
        "Sharpe total" either way.
    """
    day = pd.DatetimeIndex(closed).normalize() + pd.offsets.BDay(0)  # pyright: ignore[reportAttributeAccessIssue] -- pandas stubs omit DatetimeIndex.normalize
    daily = (
        pd.Series(np.asarray(pnl, dtype=np.float64), index=day).groupby(level=0).sum()
    )
    return daily.reindex(  # pyright: ignore[reportReturnType] -- Series.reindex is a Series
        pd.bdate_range(daily.index.min(), daily.index.max()), fill_value=0.0
    )


def cumulative(pnl: npt.ArrayLike, axis: int = -1) -> np.ndarray:
    """The cumulative P&L curve with its starting 0 in front, so the start counts as a peak."""
    x = np.asarray(pnl, dtype=np.float64)
    pad = [(0, 0)] * x.ndim
    pad[axis] = (1, 0)
    return np.cumsum(np.pad(x, pad), axis=axis)


def dd_money(
    curve: npt.ArrayLike, axis: int = -1
) -> Any:  # float for one, ndarray for several
    """Deepest fall of a curve below its running peak, in the curve's unit, positive.

    Args:
        curve: Equity or cumulative P&L along `axis`. The peak starts at the first value:
            a P&L curve that starts from 0 before its first trade passes `cumulative(pnl)`.

    Returns:
        A float for one curve, an array for several; 0 for an empty or never-falling curve.
    """
    x = np.asarray(curve, dtype=np.float64)
    if x.shape[axis] == 0:
        out = np.zeros(np.delete(x.shape, axis % x.ndim))
    else:
        out = (np.maximum.accumulate(x, axis=axis) - x).max(axis=axis)
    return float(out) if out.ndim == 0 else out


def dd_pct(
    curve: npt.ArrayLike, deposit: float, axis: int = -1
) -> Any:  # float for one, ndarray for several
    """Deepest fall of an account's balance below its running peak, in % of that peak.

    Args:
        curve: The balance (deposit + cumulative P&L) along `axis`, account currency.
        deposit: The account it started with; the peak starts there, so a first losing
            trade is a drawdown. Every account, prop-firm and MT5 figure uses this one.

    Returns:
        Percent, positive; a float for one curve, an array for several; 0 for an empty one.
    """
    x = np.asarray(curve, dtype=np.float64)
    if x.shape[axis] == 0:
        out = np.zeros(np.delete(x.shape, axis % x.ndim))
    else:
        peak = np.maximum(np.maximum.accumulate(x, axis=axis), deposit)
        out = ((peak - x) / peak).max(axis=axis) * 100.0
    return float(out) if out.ndim == 0 else out


def profit_factor(
    pnl: npt.ArrayLike, axis: int = -1
) -> Any:  # float for one, ndarray for several
    """Gross gain over gross loss of the trades along `axis`.

    Returns:
        inf with gains and no loss (a real statement, not a value to clip); NaN with no
        trade or nothing won nor lost; 0 with losses only. A JSON payload takes `finite`.
    """
    x = np.asarray(pnl, dtype=np.float64)
    gain = np.where(x > 0, x, 0.0).sum(axis=axis)
    loss = -np.where(x < 0, x, 0.0).sum(axis=axis)
    out = np.where(gain > 0, np.inf, np.nan)
    out = np.divide(gain, loss, out=np.asarray(out, dtype=np.float64), where=loss > 0)
    return float(out) if out.ndim == 0 else out


def finite(value: float) -> float | None:
    """A figure as a numeric column and JSON carry it: None for inf and NaN.

    A profit factor without a loss (inf) and one without trades (NaN) both become None, as
    every window column always had them; JSON has no infinity and a string breaks sorting.
    """
    return float(value) if np.isfinite(value) else None


def years(first: Any, last: Any) -> float:
    """Elapsed years between two instants, `(last - first).days / 365.25`.

    No `+1`: the span is the time elapsed between the first and the last observation, the
    same quantity whatever the clock time of the bounds; counting the last day as a whole
    extra day makes a one-day window 1/365 of a year long and a two-timestamp span depend
    on whether its bounds were written as dates or as times. One convention, everywhere.
    """
    return (pd.Timestamp(last) - pd.Timestamp(first)).days / YEAR_DAYS  # pyright: ignore[reportOperatorIssue,reportAttributeAccessIssue] -- NaT is not a bound here

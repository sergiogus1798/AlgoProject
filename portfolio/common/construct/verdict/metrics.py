"""Window-robust metrics of daily P&L paths: RAR, R-cubed, gain-to-pain, P(losing year), Sharpe."""

import numpy as np
import pandas as pd

NAMES = ("rar", "r_cubed", "gain_to_pain", "p_losing_year")
SIGN = {"rar": 1.0, "r_cubed": 1.0, "gain_to_pain": 1.0, "p_losing_year": -1.0}
LOSING_YEAR = ("calendar", "rolling")
YEAR_ROWS = 252     # trading rows in the rolling reading's year
TOP_DRAWDOWNS = 5   # Faith's R-cubed averages the five largest


def drawdowns(equity: np.ndarray, day: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Every drawdown episode of one cumulative P&L path, peak to recovery.

    Args:
        equity: Cumulative P&L per row; the path starts from 0 the day before the first row.
        day: The rows' dates as day ordinals.

    Returns:
        `depth` (peak minus the lowest point, same unit as `equity`) and `length` (calendar
        days from the peak to the first row back at it, or to the last row when it never
        recovers), one entry per episode in time order.
    """
    eq = np.concatenate([[0.0], equity])
    days = np.concatenate([[day[0] - 1], day])
    under = np.maximum.accumulate(eq) - eq
    edges = np.flatnonzero(np.diff(np.concatenate([[False], under > 0, [False]]).astype(np.int8)))
    starts, ends = edges[::2], edges[1::2]
    if starts.size == 0:
        return np.empty(0), np.empty(0)
    depth = np.maximum.reduceat(under, starts)
    length = days[np.minimum(ends, days.size - 1)] - days[starts - 1]
    return depth, length.astype(float)


def table(paths: np.ndarray, dates: pd.DatetimeIndex, losing_year: str) -> dict[str, np.ndarray]:
    """The four ranked metrics and the daily Sharpe of each path.

    RAR is the slope of a straight line fitted to the cumulative P&L, per year, in the paths'
    own unit (a fraction of the balance makes it RAR %/100): fixed risk on the initial balance
    does not compound, so the line is fitted to the equity itself and not to its logarithm.

    Args:
        paths: [P, D] daily P&L, no NaN.
        dates: The D rows' dates.
        losing_year: "calendar" (the share of calendar years that lose) or "rolling" (the
            share of every 252-row window that loses).

    Returns:
        `rar`; `r_cubed` (RAR over the five deepest drawdowns' mean depth times their mean
        length in years); `gain_to_pain` (mean annual profit over the mean of the N deepest
        drawdowns, N = years); `p_losing_year`; `sharpe` (per day, not annualised) -- each [P].
    """
    day = dates.values.astype("datetime64[D]").astype(np.int64)
    years = (day[-1] - day[0] + 1) / 365.25
    t = (day - day[0]) / 365.25
    equity = np.cumsum(paths, axis=1)
    centred = t - t.mean()
    rar = (equity - equity.mean(axis=1, keepdims=True)) @ centred / (centred @ centred)

    n_years = max(1, round(years))
    r_cubed, gain_to_pain = np.empty(len(paths)), np.empty(len(paths))
    for i, eq in enumerate(equity):
        depth, length = drawdowns(eq, day)
        order = np.argsort(-depth)
        top = order[:TOP_DRAWDOWNS]
        r_cubed[i] = rar[i] / (depth[top].mean() * length[top].mean() / 365.0)
        gain_to_pain[i] = (eq[-1] / years) / depth[order[:n_years]].mean()

    if losing_year == "calendar":
        yearly = pd.DataFrame(paths.T, index=dates.year).groupby(level=0).sum().to_numpy().T  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.year
    else:
        cum = np.concatenate([np.zeros((len(paths), 1)), equity], axis=1)
        yearly = cum[:, YEAR_ROWS:] - cum[:, :-YEAR_ROWS]
    return {"rar": rar, "r_cubed": r_cubed, "gain_to_pain": gain_to_pain,
            "p_losing_year": (yearly < 0).mean(axis=1),
            "sharpe": paths.mean(axis=1) / paths.std(axis=1, ddof=1)}

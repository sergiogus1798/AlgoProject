"""The numbers: what each side earned, what it risked, and what an hour of exposure bought."""

from typing import TypedDict, cast

import pandas as pd

from core import metrics
from studies.closing.exposure.occupancy import Occupancy


class Stats(TypedDict):
    """What one daily series is worth: net, return, CAGR, drawdown, volatility, Sharpe."""

    net: float
    return_pct: float
    cagr_pct: float
    maxdd_pct: float
    vol: float
    sharpe: float


class Dichotomy(TypedDict):
    """Return against the market time it took: per hour exposed, efficiency, ratios, hours off."""

    return_per_exposure_pct: float
    efficiency: float
    return_ratio: float
    dd_ratio: float
    hours_off: float


def stats(daily: pd.Series, equity: float) -> Stats:
    """What one daily profit-and-loss series is worth.

    Args:
        daily: Account currency per day, flat days present as zeros.
        equity: Account balance at the start of the window.

    Returns:
        `net` in account currency, `return_pct` on the starting balance, `cagr_pct`,
        `maxdd_pct` off the running peak of that same balance, `vol` as the daily standard
        deviation, and `sharpe` annualised at 252 days against a zero benchmark (NaN or infinite when
        the series is flat, std 0; the study only describes, nothing ranks on it).

        Every rate is per calendar day of the window, flat days included -- the honest
        denominator for "what did the account do", and the reason the study reports the
        per-hour-exposed rate separately instead of quietly swapping one for the other.
    """
    path = equity + daily.cumsum()
    index = cast(pd.DatetimeIndex, daily.index)
    years = metrics.years(index[0], index[-1])
    return {
        "net": float(daily.sum()),
        "return_pct": float(daily.sum() / equity * 100),
        "cagr_pct": float(((path.iloc[-1] / equity) ** (1 / years) - 1) * 100),
        "maxdd_pct": metrics.dd_pct(path.to_numpy(dtype=float), equity),
        "vol": float(daily.std(ddof=1)),
        "sharpe": metrics.sharpe(daily, metrics.TRADING_DAYS),
    }


def equity_start(trades: pd.DataFrame) -> float:
    """The account balance the sample started from.

    Args:
        trades: One strategy's trades on one sample, in SQX's own order.

    Returns:
        The balance before the first trade of the sample, recovered from the balance after
        it. The out-of-sample run continues the in-sample account, so this is not the
        initial deposit and must not be read as one.
    """
    first = trades.iloc[0]
    return float(first["Balance"] - first["Profit/Loss"])


def dichotomy(strategy: Stats, bench: Stats, exposure: Occupancy) -> Dichotomy:
    """The trade-off itself: return against the market time it took to get it.

    Args:
        strategy: What `stats` returned for the strategy.
        bench: What `stats` returned for the headline benchmark convention.
        exposure: What `occupancy.measure` returned.

    Returns:
        `return_per_exposure_pct`, the return the strategy would show if it were in the
        market all the time at the rate it manages while it is; `efficiency`, that figure
        as a multiple of buy and hold's, which is 1.0 for a strategy that is merely as
        productive per hour exposed as holding the thing; `dd_ratio`, its drawdown against
        the benchmark's; and `hours_off`, the hours a week it is not exposed to anything.

        ⚠️ `return_per_exposure_pct` is an extrapolation and is only that: nobody can hold
        thirty positions at once, and a strategy that waits for a setup would not find
        twenty-seven times as many of them. It measures the quality of the time spent, not
        a return anyone could have earned.
    """
    per_exposure = strategy["return_pct"] / exposure["share"]
    return {
        "return_per_exposure_pct": per_exposure,
        "efficiency": per_exposure / bench["return_pct"],
        "return_ratio": strategy["return_pct"] / bench["return_pct"],
        "dd_ratio": strategy["maxdd_pct"] / bench["maxdd_pct"],
        "hours_off": 24 * 7 - exposure["hours_per_week"],
    }

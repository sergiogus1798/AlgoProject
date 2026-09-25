"""Item 1: how few trades and how few periods the whole result rests on."""

import numpy as np
import pandas as pd


def metrics(pnl: np.ndarray) -> dict:
    """The three per-trade numbers every trimmed view is compared on.

    Args:
        pnl: Net P&L per trade, in account currency.

    Returns:
        Expectancy per trade, Sharpe per trade (not annualised -- these are trades, not
        days, and annualising would need a trade frequency that trimming changes), and
        profit factor. Profit factor is infinite for a set with no losses; that is the
        honest value and the renderer prints it as such.
    """
    losses = -pnl[pnl < 0].sum()
    return {"expectancy": float(pnl.mean()), "sharpe": float(pnl.mean() / pnl.std(ddof=1)),
            "profit_factor": float(pnl[pnl > 0].sum() / losses) if losses else np.inf}


def top_share(pnl: np.ndarray, q: float) -> float:
    """What share of the total profit the best q of trades produced.

    Args:
        pnl: Net P&L per trade.
        q: Fraction of trades, 0.01 for the best 1%.

    Returns:
        Their summed P&L over the total. Above 1.0 means the strategy loses money without
        them. A negative total makes this unreadable, and the caller checks that first.
    """
    n = max(1, int(round(len(pnl) * q)))
    return float(np.sort(pnl)[-n:].sum() / pnl.sum())


def trimmed(pnl: np.ndarray, counts: list[int]) -> pd.DataFrame:
    """The same metrics with the best N trades taken out, for several N.

    Args:
        pnl: Net P&L per trade.
        counts: How many of the best trades to remove, 0 included for the baseline.

    Returns:
        One row per N. Removing the best trades is not a fair backtest -- it is a
        sensitivity: it says how much of the result would survive if the few largest
        winners had not happened to land inside this history.
    """
    order = np.sort(pnl)
    return pd.DataFrame([{"removed": n, **metrics(order[:len(order) - n] if n else order)}
                         for n in counts]).set_index("removed")


def periods(trades: pd.DataFrame, pnl: np.ndarray, freq: str) -> pd.Series:
    """Profit per calendar period, by entry time.

    Args:
        trades: One strategy's trades.
        pnl: Net P&L per trade, aligned to them.
        freq: A pandas offset alias -- "ME" for months, "YE" for years.

    Returns:
        One sum per period. Attributed by **entry** time: a trade belongs to the period in
        which the decision was made, which is the thing being judged.
    """
    stamped = pd.Series(pnl, index=pd.DatetimeIndex(trades["Open time"]))
    return stamped.groupby(pd.Grouper(freq=freq)).sum()


def time_concentration(trades: pd.DataFrame, pnl: np.ndarray, best_months: int) -> dict:
    """How much of the result came from a handful of months, and from the best year.

    Args:
        trades: One strategy's trades.
        pnl: Net P&L per trade.
        best_months: How many top months to pool, 3 in the PDF.

    Returns:
        The share from the best months, the share from the best year, and the metrics
        recomputed with that year's trades removed. A result that disappears without one
        year is a result about that year.
    """
    monthly = periods(trades, pnl, "ME")
    yearly = periods(trades, pnl, "YE")
    best = yearly.idxmax().year
    kept = pnl[pd.DatetimeIndex(trades["Open time"]).year != best]
    return {"best_months": float(monthly.nlargest(best_months).sum() / monthly.sum()),
            "best_year": int(best), "best_year_share": float(yearly.max() / yearly.sum()),
            "without_best_year": metrics(kept), "n_without": int(kept.size),
            "monthly": monthly, "yearly": yearly}

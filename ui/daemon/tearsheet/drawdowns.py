"""Drawdown arithmetic on one sample's daily cumulative P&L: the distance below the running peak."""

import pandas as pd


def underwater(equity: pd.Series, capital: float | None) -> tuple[pd.Series, pd.Series | None]:
    """Distance below the running peak, in money and in % of the running peak of the account.

    Args:
        equity: Cumulative P&L per day, starting at 0, indexed by day.
        capital: The account the backtest started with; the P&L alone peaks at 0 on day
            one, so a percentage needs the balance (capital + P&L) underneath it.

    Returns:
        (money ≤ 0, percent ≤ 0 or None when the capital is unknown).
    """
    peak = equity.cummax()
    money = equity - peak
    return money, (None if capital is None else 100 * money / (capital + peak))

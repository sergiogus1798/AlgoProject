"""What a strategy's worst stretches cost, in units of its risk per trade (R)."""

import numpy as np
import pandas as pd


def table(daily: pd.DataFrame, trades: pd.DataFrame, risk: float, years: float) -> pd.DataFrame:
    """The losses a funded account would have had to sit through, on one sample.

    Args:
        daily: Daily change of SQX's equity, days x identity. SQX stores each day's LOWEST
            equity — closed P&L plus open positions at their worst M1 wick (OPEN.md #88) —
            so the changes are low to low, floating included, never close to close.
        trades: The same sample's trades, with `Profit/Loss` and `MAE ($)`.
        risk: 1R in account currency: the doctrine's fixed risk per trade.
        years: Length of the sample's window.

    Returns:
        Indexed by identity, all in R: `max_dd_r` (largest fall of that equity from its running
        high, positive), `worst_day_r` (worst change from one day's low to the next, negative),
        `worst_trade_mae_r` (worst floating loss any trade showed, negative),
        `net_per_year_r` (closed net per year) and `dd_over_net_year` (`max_dd_r` /
        `net_per_year_r`: the years of net the worst fall cost). With net <= 0 the fall is
        never repaid and the ratio is +inf — not NaN, which a rule would read as a missing
        fact — so any "<=" rule fails it; NaN only where a strategy has no equity or trades.
    """
    equity = daily.fillna(0.0).cumsum()
    by = trades.groupby("identity", sort=False)
    table = pd.DataFrame({"max_dd_r": (equity.cummax().clip(lower=0.0) - equity).max() / risk,
                          "worst_day_r": daily.min() / risk,
                          "worst_trade_mae_r": by["MAE ($)"].min() / risk,
                          "net_per_year_r": by["Profit/Loss"].sum() / years / risk})
    net = table["net_per_year_r"]
    ratio = (table["max_dd_r"] / net.where(net > 0)).where(net > 0, np.inf)
    return table.assign(dd_over_net_year=ratio.where(net.notna() & table["max_dd_r"].notna()))

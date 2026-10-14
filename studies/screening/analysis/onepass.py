"""R5c, R8 and R9b: edge against cost, the t without the best, and the typical bad MAE."""

from collections.abc import Callable

import pandas as pd

from studies.screening.analysis import tradelevel


def edge_mean(oos: pd.DataFrame) -> pd.Series:
    """Mean gross P/L over mean cost charged, per identity; 1 is break-even.

    Args:
        oos: The per-trade table of oos1: `identity`, `pnl` and `cost` (the repricer's).

    Returns:
        Mean (pnl + cost) / mean cost; inf or NaN where a strategy paid no cost.
    """
    by = oos.assign(gross=oos["pnl"] + oos["cost"]).groupby("identity", sort=False)
    return by["gross"].mean() / by["cost"].mean()


def t_cost(oos: pd.DataFrame, k: float, t: Callable) -> pd.Series:
    """R3's t after charging (k - 1) x each trade's cost on top of its excess.

    Args:
        oos: The per-trade table: `identity`, `excess`, `cost`, in time order per identity.
        k: Cost multiple; 1 gives R3's own t.
        t: `tradelevel.t` or `t_skew_kurt`, the one level 1a used.

    Returns:
        Indexed by identity: the AR(1) t.
    """
    return t(oos.assign(net=oos["excess"] - (k - 1) * oos["cost"]), "net")["ar1"]


def t_without(oos: pd.DataFrame, t: Callable, drop_trades: int, period: str) -> pd.DataFrame:
    """R3's t without the best calendar period and without the best trades, per identity.

    Args:
        oos: The per-trade table: `identity`, `open_time`, `excess`, in time order.
        t: `tradelevel.t` or `t_skew_kurt`.
        drop_trades: How many of the highest-excess trades the second column removes.
        period: A key of `tradelevel.WINDOWS`; the period of greatest total excess is removed.

    Returns:
        Indexed by identity: `t_sin_mejor_trimestre`, `t_sin_3_mejores` (named for the
        defaults); NaN where nothing is left to measure.
    """
    ident = oos["identity"]
    label = pd.Series(tradelevel.calendar(oos["open_time"], period), index=oos.index)
    total = oos.groupby([ident, label])["excess"].sum()
    best = total.groupby(level=0).idxmax().map(lambda i: i[1])
    rank = oos.groupby("identity", sort=False)["excess"].rank(method="first", ascending=False)
    return pd.DataFrame({
        "t_sin_mejor_trimestre": t(oos[label.to_numpy() != ident.map(best).to_numpy()],
                                   "excess")["ar1"],
        "t_sin_3_mejores": t(oos[rank > drop_trades], "excess")["ar1"]})


def mae_pct(trades: pd.DataFrame, risk: float, percentile: float) -> pd.Series:
    """The percentile of |MAE| / 1R over each identity's trades, positive.

    Args:
        trades: One sample's trades: `identity` and `MAE ($)`.
        risk: 1R in account currency.
        percentile: 0-100.
    """
    return (trades["MAE ($)"].abs() / risk).groupby(trades["identity"], sort=False).quantile(
        percentile / 100)

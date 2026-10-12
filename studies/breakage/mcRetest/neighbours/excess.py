"""Each neighbour's totals in one window: repriced profit, the drift it collected, and the excess."""

import pandas as pd

from engines.market import reprice
from engines.variants import excess
from studies.screening.analysis import resample

COLUMNS = ["excess", "profit", "drift", "trades"]


def totals(trades: pd.DataFrame, bars: pd.DataFrame, costs: reprice.Costs,
           span: tuple[str, str], drift: dict, feed: str | None = None) -> pd.DataFrame:
    """Per variant, what step 8's R3 measures per trade, summed over one window.

    Args:
        trades: One leg's trades on the main market, every variant of the batch: `variant_id`,
            `Type`, `Open time`, `Close time`, `Size`, and from an export `Close type` and
            `Close price`.
        bars: The strategies' own timeframe, the whole file, indexed by open time.
        costs: `reprice.costs` of the feed and this window's segment.
        span: (first, last) of the window, as strings a DatetimeIndex slices by.
        drift: The gate's `drift` block: `window` and `variant`.
        feed: As `reprice.located` takes it; None for trades on the bar grid by construction.

    Returns:
        Indexed by `variant_id`: `profit` (the common repricer's P/L), `drift` (what the market
        paid for being in), both from `engines.variants.excess.per_trade`, `excess` = profit -
        drift, and `trades`.
        A variant without a trade in the window has no row. Raises as `reprice.real` does.
    """
    return summed(excess.per_trade(trades, bars, costs, span, drift, feed))


def summed(per: pd.DataFrame) -> pd.DataFrame:
    """`totals`' sums over `engines.variants.excess.per_trade`'s rows, so a caller that also
    wants the trades themselves (`drawdowns`) prices them once."""
    out = per.groupby("variant_id").agg(profit=("profit", "sum"), drift=("drift", "sum"),
                                        trades=("profit", "size"))
    return out.assign(excess=out["profit"] - out["drift"])[COLUMNS]


def drawdowns(legs: list[pd.DataFrame], risk: float) -> pd.Series:
    """Each variant's maximum drawdown over several windows together, in R.

    Args:
        legs: One frame per window: `variant_id`, `Close time` and `profit` per trade.
        risk: 1R in account currency (`studies.screening.gate.inputs.market()["risk"]`: the
            doctrine's fixed risk per trade, the same for every neighbour).

    Returns:
        Indexed by `variant_id`: the deepest fall of the closed-trade curve from its running
        high (`studies.screening.analysis.resample.max_drawdown`, the curve starting at 0),
        trades in close-time order across the windows, over `risk`. A variant with no
        trade has no row.
    """
    trades = pd.concat(legs).sort_values("Close time", kind="stable")
    return trades.groupby("variant_id")["profit"].agg(
        lambda pnl: float(resample.max_drawdown(pnl.to_numpy()))) / risk

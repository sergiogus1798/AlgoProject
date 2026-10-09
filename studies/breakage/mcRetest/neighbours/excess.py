"""Each neighbour's totals in one window: repriced profit, the drift it collected, and the excess."""

import pandas as pd

from engines.market import reprice
from engines.variants import excess

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
    per = excess.per_trade(trades, bars, costs, span, drift, feed)
    out = per.groupby("variant_id").agg(profit=("profit", "sum"), drift=("drift", "sum"),
                                        trades=("profit", "size"))
    return out.assign(excess=out["profit"] - out["drift"])[COLUMNS]

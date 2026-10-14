"""Price oos1's trades at the common repricer, so the edge is read against the cost PAID.

One definition for step 8 and step 25 (encargo 44, P.2-3): only oos1, every trade repriced by
`engines.market.reprice` at the declared costs of the task (spread, slippage, commission, swap
by night) from raw bar opens — a stop-loss exit from SQX's own price — and the cost it returns
is the denominator.
"""

from typing import Any

import pandas as pd

from core import assetcheck, assetdata
from core.barstore import read as read_bars
from engines.market import reprice


def asset_for(feed: str) -> dict[str, Any]:
    """The asset file that prices this feed's costs.

    Args:
        feed: SQX symbol as the harvest's manifest names it, e.g. "XAUUSD_M1".

    Returns:
        `core.assetdata.load()`'s dict. Raises when no `assets/symbols/*.yaml` claims the feed.
    """
    symbol = assetdata.symbol_for(feed)
    if symbol is None:
        raise SystemExit(f"ningún fichero de assets/symbols/ declara el feed {feed!r}")
    return assetdata.load(symbol)


def price(
    trades: pd.DataFrame,
    bars: pd.DataFrame,
    declared: reprice.Costs,
    feed: str | None = None,
) -> pd.DataFrame:
    """Every trade repriced by the common repricer.

    Args:
        trades: One harvest's trades of ONE sample: `identity`, `Type`, `Open time`,
            `Close time`, `Size`, and from a harvest `Close type` and `Close price`.
        bars: The strategies' own timeframe, indexed by open time (`core.barstore.read`).
        declared: `reprice.costs()` of the segment these trades ran in.
        feed: SQX feed, to check a stamp off the bar grid against its M1 bars.

    Returns:
        One row per trade in the input's order: `identity`, `open_time`, `pnl`, `cost`, as
        `reprice.real` gives them — the gate's level 1a rule: a stop-loss exit at SQX's own
        price, every other from a bar open. Raises where it does.
    """
    priced = reprice.real(trades, bars, declared, feed)
    return pd.DataFrame(
        {
            "identity": trades["identity"].to_numpy(),
            "open_time": trades["Open time"].to_numpy(),
            "pnl": priced["pnl"].to_numpy(),
            "cost": priced["cost"].to_numpy(),
        }
    )


def per_trade(trades: pd.DataFrame, feed: str, timeframe: str) -> pd.DataFrame:
    """oos1's trades of a harvest, priced at the feed's oos1 costs.

    Args:
        trades: `inputs.trades()`, carrying `sample` ("IS"/"OOS"); only "OOS" is read.
        feed: SQX feed, e.g. "XAUUSD_M1".
        timeframe: The bars the strategies were priced on, e.g. "M30".

    Returns:
        `price()`'s table over the OOS rows.
    """
    oos = pd.DataFrame(trades[trades["sample"] == "OOS"])
    return price(oos, read_bars(feed, timeframe), reprice.costs(feed, "oos1"), feed)


def warnings(asset: dict) -> list[dict]:
    """What must be said about this asset's costs before trusting a money figure.

    Args:
        asset: `asset_for()`'s dict.

    Returns:
        One warning when a cost field is a stand-in (`core.assetcheck.provisional`).
    """
    stood_in = assetcheck.provisional(asset)
    return (
        [
            {
                "code": "provisional",
                "state": "watch",
                "text": f"{asset['symbol']}: {', '.join(stood_in)} son valores puestos por el "
                "dueño para desbloquear la autoría, no cifras pactadas con el bróker "
                "(assets/symbols/*.yaml). Todo coste de este resultado los hereda.",
            }
        ]
        if stood_in
        else []
    )

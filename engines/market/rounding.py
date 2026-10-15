"""Whether SQX rounds an asset's fills to the tick, measured on any trades export."""

from datetime import date
from typing import Any, cast

import pandas as pd

from core import assetdata
from engines.market import reprice
from engines.weekly import panel
from core import barstore
from ledger import thresholds

SEGMENT = {"OOS1": "oos1", "OOS2": "oos2"}  # export `Sample type` -> the card's segment


def measure(
    symbol: str,
    trades: pd.DataFrame,
    timeframe: str = "M1",
    segment: str | None = None,
) -> dict[str, Any]:
    """Which rounding reprices these trades closest to SQX's own NetProfit.

    Args:
        symbol: Asset name, e.g. "EURUSD"; its card gives the feed and the costs (the card's
            own `price_rounding` is not read).
        trades: An SQX trades export: `strategy`, `Type`, `Open time`, `Close time`, `Open
            price`, `Close price`, `Size`, `Close type`, `Profit/Loss`. One segment's trades.
        timeframe: The strategies' timeframe; M1 bars hold every stamp whatever it is, but a
            stop exit is checked against its bar's range, so a coarser one is wider.
        segment: "build", "oos1" or "oos2" (the costs); None reads the export's `Sample type`.

    Returns:
        {"tick": off-share rounding to the tick, "none": off-share unrounded, "n": strategies,
        "use": the lower one, None when equal, "why": one line}. Off-share is the share of
        strategies whose repriced net differs from SQX's by more than max(wfc.sqx_gap_tolerance,
        wfc.sqx_gap_relative x |NetProfit|).
    """
    feed = assetdata.load(symbol)["sqx_symbol"]
    seg = segment or SEGMENT.get(str(trades["Sample type"].iloc[0]).upper(), "build")
    got = trades.assign(variant_id=trades["strategy"].astype(str))
    net = cast(pd.Series, got.groupby("variant_id")["Profit/Loss"].sum())
    bars = barstore.read(feed, timeframe)
    span = (str(got["Open time"].min()), str(got["Close time"].max()))
    tol, rel = (
        float(cast(float, thresholds.value(f"wfc.sqx_gap_{k}")))
        for k in ("tolerance", "relative")
    )
    share: dict[str, float] = {}
    for name, rounds in (("tick", True), ("none", False)):
        per = panel.per_trade(
            got,
            bars,
            reprice.costs(feed, seg, rounds),
            span,
            {"window": "year", "variant": "a"},
            feed,
        )
        share[name] = panel.sqx_gap(per, net, tolerance=tol, relative=rel)[0]
    use = (
        None
        if share["tick"] == share["none"]
        else ("tick" if share["tick"] < share["none"] else "none")
    )
    return share | {
        "n": len(net),
        "use": use,
        "why": f"{date.today()}, {symbol} {seg}, n={len(net)}: off-share tick {share['tick']:.1%}, "
        f"none {share['none']:.1%}"
        + (f" -> {use}" if use else " -> indistinguishable"),
    }

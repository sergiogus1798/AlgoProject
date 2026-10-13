"""One archived strategy as the engine reads it — files only, nothing recomputed."""

from pathlib import Path

import pandas as pd

from core import sqxfile
from core.archive import manifest as archive_manifest
from core.archive import read as archive_read
from engines.market import calibrate


def load(identity: str, version: str) -> dict:
    """Read one archived strategy's trades, symbol, clock and point value.

    Args:
        identity: SHA-256 of the strategy's normalised XML.
        version: The archived version folder name.

    Returns:
        `identity`, `version`, `step` (the manifest's, e.g. "16.5"), `development`
        (`step < 26`, Q13), `symbol`, `feed`, `timeframe` (e.g. "M30"), `clock` and `commission` (the feed's
        zone and the card's per-segment figure, both frozen in the manifest), `trades` (`harvest/trades.parquet`, orderstocsv schema),
        `sqx_equity` (`harvest/equity.parquet`), `point_value` — measured on the trades that
        opened and closed the same day when there are any: an overnight trade's `Profit/Loss`
        carries its swap, which biased the fit by 0.34 % on NIKKEI225 (🔬 2026-10-05).
    """
    got = archive_read.load(identity, version)
    folder = Path(got["folder"])
    step = got["manifest"]["step"]
    symbol, timeframed = sqxfile.symbol(Path(got["sqx"]))
    clock, commission = archive_read.frozen(got["manifest"], identity)
    feed = archive_manifest.feed_of(Path(got["sqx"]))
    trades = pd.read_parquet(folder / "harvest" / "trades.parquet")
    same_day = trades[trades["Open time"].dt.normalize() == trades["Close time"].dt.normalize()]
    return {"identity": identity, "version": got["version"], "step": step,
            "development": float(step) < 26, "symbol": symbol, "feed": feed,
            "timeframe": timeframed.split("_LOM_")[-1],
            "clock": clock, "commission": commission, "trades": trades,
            "sqx_equity": pd.read_parquet(folder / "harvest" / "equity.parquet"),
            "point_value": calibrate.point_value(same_day if len(same_day) > 1 else trades)}

"""One archived strategy as the engine reads it — files only, nothing recomputed."""

from pathlib import Path

import pandas as pd

from core import sqxfile
from core.archive import read as archive_read
from engines.market import calibrate
from sqx.inspect import feeds


def load(identity: str, version: str) -> dict:
    """Read one archived strategy's trades, symbol, clock and point value.

    Args:
        identity: SHA-256 of the strategy's normalised XML.
        version: The archived version folder name.

    Returns:
        `identity`, `version`, `step` (the manifest's, e.g. "16.5"), `development`
        (`step < 26`, Q13), `symbol`, `feed`, `clock` (the feed's zone, `sqx.inspect.feeds`),
        `trades` (`harvest/trades.parquet`, orderstocsv schema), `sqx_equity`
        (`harvest/equity.parquet`), `point_value` (measured from the trades).
    """
    got = archive_read.load(identity, version)
    folder = Path(got["folder"])
    step = got["manifest"]["step"]
    symbol, timeframed = sqxfile.symbol(Path(got["sqx"]))
    feed = f"{symbol}_{timeframed.split('_LOM_')[0]}"          # the `_LOM_<tf>` suffix is not part
    trades = pd.read_parquet(folder / "harvest" / "trades.parquet")  # of the data registry's key
    return {"identity": identity, "version": got["version"], "step": step,
            "development": float(step) < 26, "symbol": symbol, "feed": feed,
            "clock": feeds.timezone(feed), "trades": trades,
            "sqx_equity": pd.read_parquet(folder / "harvest" / "equity.parquet"),
            "point_value": calibrate.point_value(trades)}

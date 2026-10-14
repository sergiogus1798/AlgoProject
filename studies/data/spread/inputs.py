"""What the spread study reads: its knobs, a tick feed's minutes, Dukascopy's daily volatility."""

import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from core import assetdata, tickfile
from core.barstore import source
from core.datapaths import spread_dir, tick_file
from core.paths import bar_source
from core.study import config as study_config
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict[str, Any]:
    """Every knob, `ledger:` placeholders filled, command-line overrides applied."""
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def asset(symbol: str) -> dict[str, Any]:
    """The asset as `assets/` declares it (tick size, point value, segments, costs)."""
    return assetdata.load(symbol)


def minutes(feed: str) -> pd.DataFrame:
    """One tick feed's minute table, decoded once and cached beside the `.dat`'s stamp.

    Args:
        feed: SQX tick feed, e.g. "XAUUSD_TICK".

    Returns:
        `core.tickfile.minutes()`'s frame. The cache is rebuilt when the `.dat` changed size
        or date — SQX appends to it on a data update — so it never answers with old ticks.
    """
    dat = tick_file(feed).stat()
    stamp = {"size": dat.st_size, "mtime": int(dat.st_mtime)}
    folder = spread_dir(feed)
    cached, meta = folder / "minutes.parquet", folder / "minutes.json"
    if meta.exists() and json.loads(meta.read_text())["stamp"] == stamp:
        return pd.read_parquet(cached)
    frame, ticks = tickfile.minutes(feed)
    folder.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(cached)
    meta.write_text(json.dumps({"stamp": stamp, "ticks": ticks, "minutes": len(frame),
                                "from": str(frame.index[0]), "to": str(frame.index[-1])}))
    return frame


def volatility(feed: str) -> pd.DataFrame:
    """Dukascopy's daily volatility and price, for every day its M1 bars cover.

    Args:
        feed: SQX M1 feed, e.g. "XAUUSD_M1".

    Returns:
        Indexed by day: `rv` the mean absolute 1-minute log return, `price` the median close.
        The one thing known in every year, Darwinex's or not, that the spread may follow.
        From the bar library, or straight from SQX's own M1 file for a feed it lacks.
    """
    close = cast(pd.Series, (source(feed, ["Close"]) if bar_source(feed).exists() else tickfile.bars(feed))["Close"])
    moves = cast(pd.Series, np.log(close)).diff().abs()
    day = cast(Any, close.index).normalize()
    got = pd.DataFrame({"rv": moves.groupby(day).mean(), "price": close.groupby(day).median()})
    return cast(pd.DataFrame, got[got["rv"] > 0])   # a day without a single move is no trading day

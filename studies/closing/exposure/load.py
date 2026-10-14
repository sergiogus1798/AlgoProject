"""Everything one run of the exposure study reads, assembled once: window, bars, trades."""

from pathlib import Path
from typing import TypedDict

import pandas as pd

from core.study import identity
from studies.closing.exposure import inputs


class Loaded(TypedDict):
    """What the study reads: the export's trades, the window's bars, point value, names, identity."""

    project: str
    databank: str
    feed: str
    symbol: str
    span: tuple[pd.Timestamp, pd.Timestamp]
    bars: pd.DataFrame
    point_value: float
    packed: Path
    frame: pd.DataFrame
    strategies: list[str]
    identity: dict[str, str | None]


def load(project: str, databank: str, feed: str, symbol: str, cfg: dict) -> Loaded:
    """The inputs one.run() and many.run() read.

    Args:
        project, databank: Where the trades were exported from.
        feed: SQX feed name, e.g. XAUUSD_M1.
        symbol: Asset file name, e.g. XAUUSD.
        cfg: What `inputs.config` returned.

    Returns:
        The window from policy, its bars, the point value, the newest export read on the
        configured sample, the strategy names and their identity.
    """
    span = inputs.window(symbol, cfg["study"]["segment"])
    packed = inputs.newest(project, databank)
    frame = inputs.sample(packed, cfg["study"]["sample"])
    names = list(frame["strategy"].unique())
    return {"project": project, "databank": databank, "feed": feed, "symbol": symbol,
            "span": span, "bars": inputs.bars(feed, cfg["study"]["timeframe"], span),
            "point_value": inputs.point_value(symbol), "packed": packed, "frame": frame,
            "strategies": names, "identity": identity.lookup(project, databank, names)}

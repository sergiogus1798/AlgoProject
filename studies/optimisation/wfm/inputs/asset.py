"""The asset a WFM export traded: its daily close, its point value, its untouched `oos2` days."""

import pandas as pd

from core import assetdata, barstore


def of(feed: str) -> dict:
    """Everything the benchmark needs about the asset behind one SQX feed.

    Args:
        feed: The trades' `Symbol`, e.g. "XAUUSD_M1".

    Returns:
        `name`, `point_value`, `close` (D1, indexed by day) and `oos` — the first and last
        day of `oos2` in `_policy.yaml`. Not `oos1` (owner, 2026-10-01): the population was
        screened on it, and a window that chose the survivors cannot also judge them
        (`knowhow/research/post-selection-bias.md`).
    """
    name = assetdata.symbol_for(feed)
    data = assetdata.load(name)
    close = barstore.read(feed, "D1")["Close"]
    close.index = pd.DatetimeIndex(close.index).normalize()
    start, end = assetdata.window(data, "oos2")
    return {"name": name, "point_value": data["instrument"]["point_value"], "close": close,
            "oos": (pd.to_datetime(start, unit="ms"), pd.to_datetime(end, unit="ms"))}

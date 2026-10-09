"""Measure on an asset only the measures its stored cells lack, and add them to what is stored."""

from datetime import datetime

import pandas as pd

from core import assetdata
from studies.research.marketProfile import inputs, one, store


def missing(symbol: str, cfg: dict) -> list[dict]:
    """The config's measures that the asset's stored cells do not carry."""
    have = set(pd.read_parquet(store.cells() / f"{symbol}.parquet", columns=["measure"])["measure"])
    return [s for s in cfg["measures"] if s["name"] not in have]


def run(symbol: str, cfg: dict) -> dict:
    """One asset's missing measures on every timeframe, against their own null draws.

    Each measure's p is the share of its own draws at or above it, so measures added later are
    tested exactly as the stored ones were; only the seed differs, and it is recorded.

    Returns:
        {"status": "ok", "measures": the names measured, "wall_s": {timeframe: s}}, or a status
        saying why nothing was measured: nothing new, or a feed being rewritten.
    """
    specs = missing(symbol, cfg)
    if not specs:
        return {"status": "nada nuevo"}
    m1 = inputs.minute_bars(symbol, cfg["run"]["fresh_minutes"])
    if m1 is None:
        return {"status": "feed modificado hace poco o durante la lectura"}
    only, asset = {**cfg, "measures": specs}, assetdata.load(symbol)
    got = [one.run(symbol, timeframe, inputs.bars(m1, timeframe), asset, only)
           for timeframe in cfg["run"]["timeframes"]]
    names = [s["name"] for s in specs]
    walls = {g["context"]["timeframe"]: round(g["wall_s"], 1) for g in got}
    store.extend(symbol, [r for g in got for r in g["rows"]], {
        "measures": names, "seed": cfg["nulls"]["seed"], "wall_s": walls,
        "computed_at": datetime.now().isoformat("T", "seconds")})
    return {"status": "ok", "measures": names, "wall_s": walls}

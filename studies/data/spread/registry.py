"""What SQX's own data registry says about a symbol: its feeds, its instrument, its range, every broker's swap."""

import re
import sqlite3

import pandas as pd

from core.paths import MASTER
from core.symbols import alias

REGISTRY = MASTER / "user" / "data" / "data.db"
DUKASCOPY, DARWINEX = 2, 4   # DATA.SOURCE codes: what `-symbol action=list` prints as the source


def _query(sql: str, args: tuple = ()) -> list[tuple]:
    """One read-only query: a running master is never written to."""
    with sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True) as db:
        return db.execute(sql, args).fetchall()


def feeds(symbol: str) -> dict:
    """Every feed of a symbol, split by kind.

    Returns:
        {"bars": [Dukascopy M1 feeds], "ticks": [Darwinex tick feeds]}, e.g. "EURGBP_M1" and
        "EURGBP_TICK". Told apart by SQX's own timeframe and source columns, not by the name:
        since 2026-10-01 a name carries neither the source nor the broker. Several of one kind
        is a question for the owner.
    """
    rows = [r for r in _query("SELECT SYMBOL, TIMEFRAME, SOURCE FROM DATA") if alias(r[0]) == symbol]
    return {"bars": sorted(n for n, tf, src in rows if tf == "M1" and src == DUKASCOPY),
            "ticks": sorted(n for n, tf, src in rows if tf == "TICK" and src == DARWINEX)}


def broker(feed: str) -> str:
    """The broker whose instrument a feed is defined on, as `assets/` spells it.

    Returns:
        The broker's postfix in SQX's registry without its underscore, e.g. "Infinox",
        "the5ers", "ftmo".
    """
    return _query("SELECT B.POSTFIX FROM DATA D JOIN BROKER B ON B.ID = D.BROKER_ID "
                  "WHERE D.SYMBOL = ?", (feed,))[0][0].lstrip("_")


def instrument(feed: str) -> dict:
    """The feed's instrument: tick size and point value, as SQX defines them.

    Returns:
        {"tick_size", "point_value", "min_distance"}. SQX's registry holds no minimum
        distance; 0 is what every index already carries and it only matters to pending orders.
    """
    name = _query("SELECT INSTRUMENT FROM DATA WHERE SYMBOL = ?", (feed,))[0][0]
    pv, tick = _query("SELECT POINTVALUE, TICKSIZE FROM INSTRUMENTS WHERE INSTRUMENT = ?", (name,))[0]
    return {"tick_size": float(tick), "point_value": float(pv), "min_distance": 0}


def data_range(feed: str) -> tuple:
    """First and last day SQX holds for the feed, as dates."""
    start, end = _query("SELECT DATEFROM, DATETO FROM DATA WHERE SYMBOL = ?", (feed,))[0]
    return pd.Timestamp(start, unit="ms").date(), pd.Timestamp(end, unit="ms").date()


def broker_swaps(symbol: str, tick: float) -> dict:
    """The mean swap, in points per night, of every variant of the symbol with an active swap.

    Args:
        symbol: e.g. "EURGBP".
        tick: The asset's tick size; each broker's points are rescaled from its own tick.

    Returns:
        {"long", "short", "n", "brokers", "skipped"}. A variant with its swap off, or in
        percent or money rather than points, is skipped and named: converting a percentage
        would need a reference price nobody chose.
    """
    got, skipped = [], []
    for name, tk, swap in _query("SELECT INSTRUMENT, TICKSIZE, SWAP FROM INSTRUMENTS"):
        if not re.match(rf"^{symbol}([._]|$)", name) or not swap:
            continue
        at = dict(re.findall(r'(\w+)="([^"]*)"', swap))
        if at.get("use") != "true" or at["type"] != "points":
            skipped.append(f"{name} ({'off' if at.get('use') != 'true' else at['type']})")
            continue
        got.append((name, float(at["long"]) * tk / tick, float(at["short"]) * tk / tick))
    frame = pd.DataFrame(got, columns=["broker", "long", "short"])
    return {"long": round(float(frame["long"].mean()), 2), "short": round(float(frame["short"].mean()), 2),
            "n": len(frame), "brokers": frame["broker"].tolist(), "skipped": skipped}

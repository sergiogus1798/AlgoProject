"""The portfolio's one calendar (owner, Q1), and what a member borrows from its own other segments."""

import pandas as pd

from core import assetdata

SEGMENTS = ("build", "oos1", "oos2")


def _bound(value: int | str, end: bool) -> pd.Timestamp:
    """One segment bound, inclusive: a bare year's Jan 1 or Dec 31, or an explicit date."""
    if isinstance(value, int):
        return pd.Timestamp(value, 12, 31) if end else pd.Timestamp(value, 1, 1)
    return pd.Timestamp(value)


def combine(segments_by_symbol: dict[str, dict]) -> dict:
    """The portfolio calendar (Q1) from each member's own `segments` block.

    Args:
        segments_by_symbol: One `core.assetdata.load()["segments"]` per symbol.

    Returns:
        `{"build": (from, to), "oos1": (...), "oos2": (...)}`, naive `Timestamp`s, both
        inclusive: build from the earliest member's build start to the latest member's build
        end; each later segment from the day after the previous one's end to the latest
        member's own end of that segment. A segment no member has dates for is left out.
    """
    calendar, previous_end = {}, None
    for name in SEGMENTS:
        starts, ends = [], []
        for segments in segments_by_symbol.values():
            spec = segments.get(name, {})
            if spec.get("from") is None or spec.get("to") is None:
                continue
            starts.append(_bound(spec["from"], False))
            ends.append(_bound(spec["to"], True))
        if not ends:
            continue
        lo = previous_end + pd.Timedelta(days=1) if previous_end is not None else min(starts)
        hi = max(ends)
        calendar[name] = (lo, hi)
        previous_end = hi
    return calendar


def portfolio(symbols: list[str]) -> dict:
    """The portfolio calendar over a list of assets, read from `assets/_policy.yaml`."""
    return combine({symbol: assetdata.load(symbol)["segments"] for symbol in symbols})


def borrowed_from(calendar: dict, segments: dict) -> dict[str, int]:
    """Days of each portfolio segment this member spends in one of its own other segments.

    Args:
        calendar: `portfolio()`'s (or `combine()`'s) result.
        segments: One member's own `segments` block (`core.assetdata.load()["segments"]`).

    Returns:
        One count per portfolio segment name.
    """
    own_bounds = {name: (_bound(spec["from"], False), _bound(spec["to"], True))
                  for name, spec in segments.items()
                  if spec["from"] is not None and spec["to"] is not None}
    out = {}
    for name, (lo, hi) in calendar.items():
        count = 0
        for other, (o_lo, o_hi) in own_bounds.items():
            if other == name:
                continue
            start, end = max(lo, o_lo), min(hi, o_hi)
            if start <= end:
                count += (end - start).days + 1
        out[name] = count
    return out


def borrowed(calendar: dict, symbol: str) -> dict[str, int]:
    """Days of each portfolio segment this symbol spends in one of its own other segments.

    Args:
        calendar: `portfolio()`'s (or `combine()`'s) result.
        symbol: One member asset, read from `assets/_policy.yaml`.

    Returns:
        One count per portfolio segment name.
    """
    return borrowed_from(calendar, assetdata.load(symbol)["segments"])

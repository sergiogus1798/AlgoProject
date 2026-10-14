"""The calendar cells of the travel test: the pieces of year one joint shift stays inside, and the window each belongs to."""

from typing import cast

import numpy as np
import pandas as pd

from core import assetdata

MONTHS = {
    "year": (1,),
    "semester": (1, 7),
}  # travel.shift_unit -> the months a cell opens on


def cuts(asset: str) -> dict[str, pd.Timestamp]:
    """The main asset's dates the windows V0, V1 and V2 are cut at, derived and never written.

    Args:
        asset: Main asset, e.g. "NIKKEI225".

    Returns:
        `build` and `oos1`, the first instant of each segment, and `end`, the first instant
        after oos1. Before `build` is V0, [build, oos1) V1, [oos1, end) V2.
    """
    data = assetdata.load(asset)
    (build, _), (oos1, end) = (
        assetdata.window(data, "build"),
        assetdata.window(data, "oos1"),
    )
    return {
        k: cast(pd.Timestamp, pd.Timestamp(v, unit="ms"))
        for k, v in (("build", build), ("oos1", oos1), ("end", end))
    }


def table(
    first: pd.Timestamp,
    last: pd.Timestamp,
    cuts: dict[str, pd.Timestamp],
    unit: str,
    step: str,
) -> pd.DataFrame:
    """Every cell between the first and the last bar of any market.

    Args:
        first, last: The earliest and the latest bar over all the markets.
        cuts: As cuts() returns it; a cell is split wherever one falls inside it, so no shift
            crosses a window's frontier.
        unit: travel.shift_unit, "year" or "semester".
        step: travel.shift_step, "week" or "day".

    Returns:
        One row per cell, in time order: `start` and `end` (end exclusive, datetime64[s]),
        `window` ("V0", "V1", "V2", or "after" past the main's oos1) and `steps`, how many
        whole steps fit in it — the shift of a run is drawn in 0..steps-1.
    """
    lo, hi = (
        cast(pd.Timestamp, pd.Timestamp(first.year, 1, 1)),
        cast(pd.Timestamp, pd.Timestamp(last.year + 1, 1, 1)),
    )
    regular = [
        pd.Timestamp(y, m, 1) for y in range(lo.year, hi.year + 1) for m in MONTHS[unit]
    ]
    edges = np.array(
        sorted({e for e in [*regular, *cuts.values()] if lo <= e <= hi}),
        "datetime64[s]",
    )
    start, end = edges[:-1], edges[1:]
    window = np.select(
        [
            start < np.datetime64(cuts["build"]),
            start < np.datetime64(cuts["oos1"]),
            start < np.datetime64(cuts["end"]),
        ],
        ["V0", "V1", "V2"],
        "after",
    )
    steps = (
        (end - start).astype(np.int64) // (7 * 86400)
        if step == "week"
        else np.busday_count(start.astype("datetime64[D]"), end.astype("datetime64[D]"))
    )
    return pd.DataFrame(
        {"start": start, "end": end, "window": window, "steps": np.maximum(steps, 1)}
    )


def occupancy(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Locate every trade on the bar grid.

    Args:
        trades: One market's trades, times already parsed.
        bars: That market's bars, indexed by bar open time.

    Returns:
        Columns entry, exit and hold, in bar indices. Trades whose entry or exit falls outside
        the bar file are dropped: they cannot be repriced and would silently shorten the hold.
    """
    entry = bars.index.get_indexer(trades["Open time"], method="pad")
    out = bars.index.get_indexer(trades["Close time"], method="pad")
    keep = (entry >= 0) & (out > entry)
    return pd.DataFrame(
        {"entry": entry[keep], "exit": out[keep], "hold": out[keep] - entry[keep]},
        index=trades.index[keep],
    )

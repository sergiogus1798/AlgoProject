"""The bar library: M1 is the only bar data stored, every other timeframe is resampled from it."""

import hashlib
from pathlib import Path

import pandas as pd

from core import bars, manifest
from core.paths import DATA, bar_cache, bar_source
from core.symbols import current

# SQX timeframe code to the pandas offset that reproduces it. Verified on XAUUSD 2026-09-21:
# resampling 7,708,823 M1 bars to M30 gives SQX's own M30 export to the last decimal on all
# four prices, same index, no bar on either side — see knowhow/export/bars.md.
RULE = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h",
        "H4": "4h", "H12": "12h", "D1": "1D"}
AGG = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}


def fingerprint(frame: pd.DataFrame) -> str:
    """Short identity of one feed's M1 data.

    Args:
        frame: The M1 bars, indexed by bar open time.

    Returns:
        Eight hex characters over the bar count and the last bar's time. Those two move
        whenever SQX's data for the feed moves, which is the only event that has to
        invalidate a resampled timeframe.
    """
    text = f"{len(frame)}-{frame.index[-1]:%Y%m%d%H%M}"
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def library() -> dict:
    """What the bar library currently holds.

    Returns:
        {feed: {"bars": int, "version": str, "from": str, "to": str}}, as the last sync
        wrote it, and empty before the first sync has run.
    """
    path = DATA / "bars"
    return manifest.read(path)["counts"] if (path / "manifest.json").exists() else {}


def store(feed: str, csv: Path) -> dict:
    """Put one feed's freshly exported M1 CSV into the library as Parquet.

    Args:
        feed: SQX symbol without the timeframe suffix.
        csv: Path of the CSV `-data action=export` wrote.

    Returns:
        The library entry for that feed. The CSV is removed once the Parquet is written:
        it is three times the size and nothing reads it again.
    """
    frame = bars.read(csv)
    out = bar_source(feed)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.reset_index(names="t").to_parquet(out, compression="zstd", index=False)
    csv.unlink()
    return {"bars": len(frame), "version": fingerprint(frame),
            "from": f"{frame.index[0]:%Y-%m-%d}", "to": f"{frame.index[-1]:%Y-%m-%d}"}


def source(feed: str, columns: list[str] | None = None) -> pd.DataFrame:
    """One feed's M1 bars.

    Args:
        feed: SQX symbol without the timeframe suffix.
        columns: Only these price columns, for a caller that reads one or two of them: a
            feed is 7.7 M bars and each column read is 62 MB.

    Returns:
        Columns Open, High, Low, Close, Volume indexed by bar open time, as core.bars.read()
        returns them. Prices stay float64: under zstd they compress smaller than float32
        does, so rounding them buys nothing and costs precision.
    """
    return pd.read_parquet(bar_source(current(feed)),
                           columns=["t", *columns] if columns else None).set_index("t")


def read(feed: str, timeframe: str) -> pd.DataFrame:
    """One feed's bars at any timeframe, resampled from M1 and cached.

    Args:
        feed: SQX symbol without the timeframe suffix.
        timeframe: A key of RULE, e.g. "M30".

    Returns:
        The same frame core.bars.read() returns. M1 comes straight from the library;
        anything else is resampled on first use — 0.4 s for a feed of 7.7 M bars — and
        kept under the M1 fingerprint, so a refreshed feed rebuilds it instead of serving
        bars from the previous data.
    """
    feed = current(feed)   # an older .sqx names the feed as it was before 2026-10-01
    if timeframe == "M1":
        return source(feed)
    cache = bar_cache(feed, timeframe, library()[feed]["version"])
    if cache.exists():
        return pd.read_parquet(cache).set_index("t")
    frame = source(feed).resample(RULE[timeframe]).agg(AGG).dropna()
    cache.parent.mkdir(parents=True, exist_ok=True)
    frame.reset_index(names="t").to_parquet(cache, compression="zstd", index=False)
    return frame

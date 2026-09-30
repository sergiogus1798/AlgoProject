"""SQX's own daily curve — each day's LOWEST equity, floating included — per policy segment."""

import pandas as pd

from core import assetdata

SAMPLE_TO_SEGMENT = {"IS": "build", "OOS": "oos1"}
SEGMENTS = ("build", "oos1", "oos2")


def _segment(values: pd.Series, data: dict, segment: str) -> pd.DataFrame:
    """One leg's curve, sliced to its policy window, duplicates of the next leg's warm-up dropped.

    Args:
        values: SQX's daily values, naive day index, ascending, may hold cross-leg duplicates
            (the earlier leg's row comes first and is the real one, `leg-curve-warmup.md`).
        data: One asset as `core.assetdata.load()` returned it.
        segment: Segment name, e.g. "build".

    Returns:
        Columns `low` (the day's lowest equity since the leg started, account currency) and
        `segment`.
    """
    start_ms, end_ms = assetdata.window(data, segment)
    lo, hi = pd.Timestamp(start_ms, unit="ms"), pd.Timestamp(end_ms, unit="ms")
    sliced = values[(values.index >= lo) & (values.index < hi)]
    sliced = sliced[~sliced.index.duplicated(keep="first")]
    return pd.DataFrame({"low": sliced, "segment": segment})


def from_harvest(equity: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """One identity's `harvest/equity.parquet` rows, per segment.

    Args:
        equity: Rows of one identity only: `day`, `equity`, `sample` ("IS" or "OOS").
        symbol: Asset name, to read the policy's segment dates.

    Returns:
        As `_segment`, build and oos1 (the harvest carries no oos2), each leg from its own 0.
        🔬 Day D's value is D's lowest equity on the feed's clock, not a mark to market:
        the M1 rebuild matches it on every day (`knowhow/sqx-format/daily-equity-bin.md`).
    """
    data = assetdata.load(symbol)
    return pd.concat([_segment(equity.loc[equity["sample"] == sample].set_index("day")["equity"]
                               .sort_index(), data, segment)
                      for sample, segment in SAMPLE_TO_SEGMENT.items()])


def from_batch(column: pd.Series, symbol: str) -> pd.DataFrame:
    """One column of a 16.5 batch `equity.parquet`, per segment.

    Args:
        column: One variant's values, naive day index, legs `build, oos1, oos2` sorted
            together — a duplicate date is the next leg's warm-up zero, always the later row.
        symbol: Asset name, to read the policy's segment dates.

    Returns:
        As `_segment`, every segment the policy has dates for.
    """
    data = assetdata.load(symbol)
    values = column.sort_index(kind="stable")
    return pd.concat([_segment(values, data, segment) for segment in SEGMENTS
                      if data["segments"][segment]["from"] is not None])

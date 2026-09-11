"""Read an OHLC bar file exported by SQX into a frame indexed by bar open time."""

from pathlib import Path

import pandas as pd

TIME = "%Y.%m.%d %H:%M"


def read(path: Path) -> pd.DataFrame:
    """One symbol's bars for one timeframe.

    Args:
        path: A CSV written by `-data action=export`, header
            `Date,Time,Open,High,Low,Close,Volume`.

    Returns:
        Columns Open, High, Low, Close, Volume indexed by the bar's open time. The index is
        the alignment key for everything downstream, so it is sorted and carries no duplicates.
    """
    d = pd.read_csv(path)
    d.index = pd.to_datetime(d["Date"] + " " + d["Time"], format=TIME)
    return d[["Open", "High", "Low", "Close", "Volume"]].sort_index()

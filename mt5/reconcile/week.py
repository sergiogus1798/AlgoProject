"""One ISO week on the server's clock: its bounds, and the trades that belong to it."""
import re

import pandas as pd


def bounds(week: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Monday 00:00 of an ISO week and Monday 00:00 of the next, naive, server clock.

    Args:
        week: "YYYY-Www", e.g. "2026-W38". ISO: week 1 holds the year's first Thursday, so
            2026-W01 starts on Monday 2025-12-29.

    Returns:
        (start, end): a trade belongs to the week when start <= its open time < end.
    """
    if not re.fullmatch(r"\d{4}-W\d{2}", week):
        raise SystemExit(f"semana «{week}»: se escribe AAAA-Wss, por ejemplo 2026-W38")
    start = pd.Timestamp.fromisocalendar(int(week[:4]), int(week[6:]), 1)
    return start, start + pd.Timedelta(days=7)  # pyright: ignore[reportReturnType]  # pandas stubs: Timedelta/Timestamp unions with NaT


def cut(trades: pd.DataFrame, week: str) -> pd.DataFrame:
    """The trades OPENED inside the week, whenever they closed. Times already on the server's clock."""
    start, end = bounds(week)
    opened = pd.to_datetime(trades["Open time"])
    return trades[(opened >= start) & (opened < end)].reset_index(drop=True)  # pyright: ignore[reportReturnType]  # pandas/numpy stubs lose the type through indexing


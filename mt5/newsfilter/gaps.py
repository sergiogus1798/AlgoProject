"""The stretches of a tester run with no M1 history under them, read from the patched EA's own log lines."""

import re
from pathlib import Path

import pandas as pd

THIN = re.compile(
    r"News filter \(tester\): thin history (\d{4}\.\d{2}\.\d{2}) (\d+) ticks"
)
LOADED = re.compile(r"News filter \(tester\): (\d+ releases that move|no release in)")
JOIN = pd.Timedelta(days=4)  # thin Friday + thin Monday is one stretch, not two


def agent_log() -> Path:
    """The newest log of the local tester agent, where a single test's Print lines land (UTF-16)."""
    from mt5 import wine

    return max(
        (wine.data_dir() / "Tester" / "Agent-127.0.0.1-3000" / "logs").glob("2*.log")
    )


def thin_days(text: str, stem: str) -> list[pd.Timestamp]:
    """The days the EA called thin in its LAST run in this log.

    Args:
        text: The agent log, decoded.
        stem: The EA's file name without extension, as the log's source column shows it.

    Returns:
        Server days, in order. The EA says one when a day held fewer than NEWS_THIN_DAY ticks
        — built from H1 bars, so no tick fell in the minutes before any release.
    """
    days = []
    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) < 5 or not cols[3].startswith(stem + " ("):
            continue
        if LOADED.search(cols[4]):
            days = []  # a new run of the same EA starts here
        hit = THIN.search(cols[4])
        if hit:
            days.append(pd.Timestamp(hit.group(1).replace(".", "-")))
    return days


def stretches(days: list[pd.Timestamp]) -> pd.DataFrame:
    """Thin days joined into stretches: `start` (00:00 of the first), `end` (00:00 after the last), `days`."""
    rows = []
    for day in days:
        if rows and day - rows[-1]["last"] <= JOIN:
            rows[-1]["last"], rows[-1]["days"] = day, rows[-1]["days"] + 1
        else:
            rows.append({"start": day, "last": day, "days": 1})
    out = pd.DataFrame(rows, columns=["start", "last", "days"])  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
    return out.assign(end=out["last"] + pd.Timedelta(days=1)).drop(columns="last")


def outside(trades: pd.DataFrame, gaps: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    """The trades that never touch a stretch, and per stretch how many did (open at any moment inside it)."""
    touched = pd.Series(False, index=trades.index)
    counts = []
    for g in gaps.itertuples():
        hit = (trades["Open time"] < g.end) & (trades["Close time"] >= g.start)  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
        counts.append(int(hit.sum()))
        touched |= hit
    return trades[~touched].reset_index(drop=True), counts  # pyright: ignore[reportReturnType]  # pandas/numpy stubs lose the type through indexing

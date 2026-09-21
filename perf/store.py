"""The catalogue itself: one appended row per measurement, and the only way anything reads it."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.paths import ROOT, perf_dir

HISTORY = "history.csv"
DISK = "disk.csv"
COLUMNS = ["day", "time", "commit", "target", "area", "unit", "scale", "budget",
           "wall_s", "cpu_s",
           "rss_peak_mb", "self_rss_mb", "alloc_peak_mb", "bytes_in_mb", "wall_spread_pct",
           "repeats", "load1", "avail_mb"]


def commit() -> str:
    """Which version of the code was measured.

    Returns:
        Short hash, with `-dirty` appended when the tree carried uncommitted changes. A
        measurement whose commit is dirty cannot be reproduced, and the panel says so.
    """
    out = subprocess.run(["git", "describe", "--always", "--dirty"], cwd=ROOT,
                         capture_output=True, text=True)
    return out.stdout.strip()


def context() -> dict:
    """What else the machine was doing while the measurement ran.

    Returns:
        One-minute load average and available memory in MB. Stored with every row because a
        time measured against a busy machine is not comparable with one measured against an
        idle one, and six months later nobody remembers which it was.
    """
    fields = dict(line.split(":", 1) for line in
                  Path("/proc/meminfo").read_text(encoding="utf-8").splitlines())
    return {"load1": os.getloadavg()[0],
            "avail_mb": int(fields["MemAvailable"].split()[0]) / 1024}


def append(rows: list[dict], name: str = HISTORY) -> Path:
    """Add measurements to the catalogue.

    Args:
        rows: One dict per measurement.
        name: Which file — the target history or the disk inventory.

    Returns:
        The file written. Appended, never rewritten: the comparison between dates is the
        whole point, so a row that exists is never edited or removed. The one exception is a
        **new column**: the file is then rewritten once with the wider header and every old
        row kept, blank in the new column. Appending a wider row to a narrower header
        corrupts the file outright, which is how this case was found.
    """
    where = perf_dir() / name
    where.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame = frame[[c for c in COLUMNS if c in frame.columns]] if name == HISTORY else frame
    if where.exists():
        stored = pd.read_csv(where)
        if list(stored.columns) != list(frame.columns):
            pd.concat([stored, frame]).reindex(
                columns=list(dict.fromkeys(list(stored.columns) + list(frame.columns)))
            ).to_csv(where, index=False)
            return where
    frame.to_csv(where, mode="a", header=not where.exists(), index=False)
    return where


def history(name: str = HISTORY) -> pd.DataFrame:
    """Everything ever measured.

    Args:
        name: Which file to read.

    Returns:
        The catalogue in the order it was written, empty with the right columns when
        nothing has been measured yet.
    """
    where = perf_dir() / name
    if not where.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(where)


def stamp() -> dict:
    """Day and time a run is recorded under.

    Returns:
        `day` as YYYY-MM-DD and `time` as HH:MM. Two runs on one day are two rows, because
        the question "did this change make it slower" is asked between runs, not between days.
    """
    now = datetime.now()
    return {"day": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M")}

"""SQX's own log from the moment of a launch on, across midnight: only the lines written since."""

from datetime import date, timedelta
from pathlib import Path

from ui.daemon import progress

KEEP = 20_000       # lines held; run_state needs the start, the task lines and the last percent


def path(top: Path, day: date) -> Path:
    """The install's SQX log of one day (SQX starts a new file at midnight)."""
    return top / "user" / "log" / "StrategyQuant" / f"log_{day:%Y_%m_%d}.log"


def days() -> list[date]:
    """Yesterday and today: a run launched before midnight writes on in yesterday's file
    until the new one opens."""
    today = date.today()
    return [today - timedelta(days=1), today]


def mark(top: Path) -> dict[Path, int]:
    """Where each existing log of the two days ends now, just before `action=start`.

    Returns:
        File → size. Everything before these offsets is an earlier run's, however it ended.
    """
    return {f: f.stat().st_size for f in (path(top, d) for d in days()) if f.exists()}


def grow(top: Path, offsets: dict[Path, int], kept: list[str]) -> list[str]:
    """Add what the logs gained since the last read, and advance the offsets.

    Args:
        top: The install.
        offsets: What `mark` returned, updated in place; a file born after it reads from 0.
        kept: The lines so far, extended in place with the start, progress and percent lines.

    Returns:
        `kept`, for `progress.run_state`. A half-written last line waits for the next read.
    """
    for f in (path(top, d) for d in days()):
        start = offsets.get(f, 0)
        if not f.exists() or f.stat().st_size <= start:
            continue
        with f.open("rb") as fh:
            fh.seek(start)
            data = fh.read()
        whole = data[:data.rfind(b"\n") + 1]
        offsets[f] = start + len(whole)
        kept.extend(line for line in whole.decode("utf-8", errors="replace").splitlines()
                    if progress.STARTING.search(line) or progress.PROGRESS.search(line)
                    or progress.PERCENT.search(line))
    del kept[:-KEEP]
    return kept

"""Today's SQX log of an install, as the lines that say which project runs and how far."""

import re
import threading
from datetime import datetime
from pathlib import Path

KEPT_MAX = 50_000           # kept lines of a log with no «Starting project» at all
PROGRESS = re.compile(r"ProgressEngine - (.+)$")
PERCENT = re.compile(r"\[Blocking computeThread[^\]]*?(\d+) %")
STARTING = re.compile(r"Starting project '([^']+)'")


def trim(lines: list[str], keep: int = KEPT_MAX) -> list[str]:
    """The last «Starting project» line and at most `keep` lines after it.

    Everything before the last start is an earlier run's; after it, a Walk-Forward Matrix
    writes a progress line per cell and step, so the lines are bounded — but the start is
    never the one dropped: 🔬 2026-09-29, a watcher that kept only the last 20,000 lost it
    20 min into the WFM, read «SQX did not start» and stopped the custodian mid-run.
    """
    last = next((i for i in range(len(lines) - 1, -1, -1) if STARTING.search(lines[i])), None)
    head, after = ([], lines) if last is None else ([lines[last]], lines[last + 1:])
    # Only the newest percentage is ever read, and during a WFM SQX logs thousands of
    # «StatsComputer - Exception computing databank column …» lines that carry one: kept
    # all, they pushed every task line out and the watcher said «esperando» (2026-09-29).
    bare = [x for x in after if PERCENT.search(x) and not PROGRESS.search(x)]
    body = [x for x in after if not (PERCENT.search(x) and not PROGRESS.search(x))][-keep:]
    return head + body + bare[-1:]


# Today's log, read once and then only what it gained: file → (bytes read, kept lines).
_SEEN: dict[Path, tuple[int, list[str]]] = {}
_LOCK = threading.Lock()


def log_lines(install: Path) -> tuple[list[str], float]:
    """The lines of today's SQX log that `run_state` reads, since the last project start.

    Args:
        install: The install's top folder.

    Returns:
        The start, progress and percentage lines from the last «Starting project» on, and
        the file's modification time as a timestamp. Today's file only: a run that crosses
        midnight starts a new one. It used to be the last 2 MB of the file, and a retest's
        periodic syncs fill 2 MB in an hour: 🔬 2026-09-29, MCR 2 Spread 1 h in, the start
        line fell out, every reader took the run for finished — the count, the pulse and
        `loader.find.writing`, the guard that keeps loads off a databank SQX is writing.
        The file is read whole once and then only what it gained, so the start is never
        lost however big the day grows.
    """
    f = install / "user" / "log" / "StrategyQuant" / f"log_{datetime.now():%Y_%m_%d}.log"
    if not f.exists():
        return [], 0.0
    with _LOCK:
        read, kept = _SEEN.get(f, (0, []))
        size = f.stat().st_size
        if size < read:                         # rewritten from scratch: read it again
            read, kept = 0, []
        if size > read:
            with f.open("rb") as fh:
                fh.seek(read)
                data = fh.read(size - read)
            cut = data.rfind(b"\n") + 1        # a line SQX is still writing waits
            read += cut
            fresh = [line for line in data[:cut].decode("utf-8", errors="replace").splitlines()
                     if STARTING.search(line) or PROGRESS.search(line) or PERCENT.search(line)]
            kept = trim(kept + fresh)
        _SEEN[f] = (read, kept)
        return list(kept), f.stat().st_mtime

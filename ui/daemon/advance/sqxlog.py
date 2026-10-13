"""SQX's own log from the moment of a launch on, across midnight: only the lines written since."""

import re
from datetime import date, timedelta
from pathlib import Path

from sqx.projects import live, taskcap
from ui.daemon import progress

KEEP = 20_000       # lines held; run_state needs the start, the task lines and the last percent
# The line SQX writes under «Error while running project»: the Java exception, which is the cause
# (📓 2026-10-07, «java.lang.Exception: Strategy from template file requires 2 charts, 1 defined.»).
CAUSE = re.compile(r"^[\w.$]+(?:Exception|Error): ")
CAUSES = 5          # distinct ones a failure report keeps, the newest


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


def grow(top: Path, offsets: dict[Path, int], kept: list[str],
         fresh: list[str] | None = None) -> list[str]:
    """Add what the logs gained since the last read, and advance the offsets.

    Args:
        top: The install.
        offsets: What `mark` returned, updated in place; a file born after it reads from 0.
        kept: The lines so far, extended in place with the start, progress and percent lines.
        fresh: Extended in place with EVERY line this read gained, for `police`.

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
        lines = whole.decode("utf-8", errors="replace").splitlines()
        if fresh is not None:
            fresh.extend(lines)
        kept.extend(line for line in lines
                    if progress.STARTING.search(line) or progress.PROGRESS.search(line)
                    or progress.PERCENT.search(line))
    kept[:] = progress.trim(kept, KEEP)       # the start line stays, whatever the volume
    return kept


def police(cap: dict, fresh: list[str], project: str, role: str, top: Path, stopped: bool) -> None:
    """End a watched run on what `live.wait` ends it on: an abort line (`live.BAD`, the one list
    `wait.sh` mirrors) or a task past its deadline (`taskcap`), worded as the transient abort
    `call.again` repeats once and as the step failure it does not.

    Args:
        cap: `taskcap.fresh()`, kept by the watcher across its polls.
        fresh: The lines one `grow` gained.
        project: The project watched.
        role: Its worker.
        top: The install.
        stopped: The watcher itself sent the build's `stop` (`buildcap`): «Project stopped» is
            then the end it asked for, not an abort.
    """
    for line in fresh:
        taskcap.note(cap, line)
        if live.BAD.search(line) and not (stopped and "Project stopped" in line):
            raise SystemExit(f"SQX abortó {project}: {line.strip()[:200]}; la tarea no terminó, "
                             "se para el worker")
    taskcap.enforce(cap, role, path(top, date.today()))


def matching(top: Path, offsets: dict[Path, int], rx: re.Pattern[str]) -> list[str]:
    """Every line the logs gained since `offsets` that `rx` finds, read line by line.

    Args:
        top: The install.
        offsets: What `mark` returned before the start, NOT the copy `grow` advances.
        rx: The pattern.

    Returns:
        The matching lines. A WFM day is millions of lines: nothing but these is kept.
    """
    found = []
    for f in (path(top, d) for d in days()):
        if not f.exists():
            continue
        with f.open("rb") as fh:
            fh.seek(offsets.get(f, 0))
            found += [line for raw in fh
                      if rx.search(line := raw.decode("utf-8", errors="replace"))]
    return found


def causes(top: Path, offsets: dict[Path, int]) -> str:
    """The Java exceptions SQX logged since `offsets`, as the block a failure report appends.

    Args:
        top: The install.
        offsets: What `mark` returned before the run.

    Returns:
        A fenced markdown block of the newest distinct ones, or "" when SQX logged none.
    """
    found = list(dict.fromkeys(line.strip() for line in matching(top, offsets, CAUSE)))[-CAUSES:]
    return "\nLo que SQX escribió en su log:\n\n```\n" + "\n".join(found) + "\n```\n" if found else ""

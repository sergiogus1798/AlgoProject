"""The custodian's four variant databanks, emptied off the disk between two batches."""

import re
from pathlib import Path

from core import worker
from core.paths import worker_dir
from sqx.variants import legs as legmod


def clear(cfg: dict) -> int:
    """Empty the input and the three legs' databanks, off the disk, with the install down.

    Args:
        cfg: The `execute` block, with the project.

    Returns:
        How many `.sqx` were deleted. Run after `equity` and `collect`, which read these very
        files, and before the next mother is loaded.

        With the install stopped nothing is in memory, so the next start loads the four
        empty -- hard rule 1 works for us here instead of against us. 🔬 2026-09-25, doing
        it through the API instead cost 206 s and a 47 GB JVM: starting the install syncs
        all 20,000 files INTO memory before `clear` can drop them.
    """
    held = worker.holding(worker_dir(cfg["role"]))
    if held:
        raise SystemExit(f"el {cfg['role']} esta arriba (PID {held}): con SQX vivo un sync "
                         "desharia el borrado. Paralo antes: bin/sqx-worker.sh --role "
                         f"{cfg['role']} stop")
    gone = 0
    for bank in [legmod.source()] + [leg["databank"] for leg in legmod.legs()]:
        for path in legmod.bank_dir(cfg["role"], cfg["project"], bank).glob("*.sqx"):
            path.unlink()
            gone += 1
    return gone


# SQX's own line when a run dies: 🔬 2026-09-29, a NullPointerException in ProjectGlobalLog at the
# end of «WFC 1 IS» aborted the project and `execute.run` waited 53 min for tests never coming.
ABORTED = b"Error while running project"
TESTED = re.compile(r"Total tested\s+(\d+)")
# A project whose tasks are all Retest reports no "Total tested" line; what moves is the
# record count across its databanks, the loaded batch plus every leg's output so far.
IN_BANK = re.compile(r"In databank\s+(\d+)")


def mark(logs: Path) -> dict[Path, int]:
    """Where each of SQX's logs ends now: `aborted` reads only what is written after it.

    Args:
        logs: The install's `user/log/StrategyQuant`.
    """
    return {p: p.stat().st_size for p in logs.glob("log_*.log")}


def aborted(logs: Path, seen: dict[Path, int]) -> bool:
    """Whether SQX's log says, past `seen`, that the project died.

    Args:
        logs: The install's `user/log/StrategyQuant`.
        seen: Bytes already read per log, from `mark`; advanced here by every whole line
            read, so each poll costs what was written since the last one.

    Returns:
        True on the abort line. Every log is read, not one fixed at the start: SQX opens the
        next day's at midnight, and a run that crosses it aborts in a file `mark` never saw.
    """
    for log in sorted(logs.glob("log_*.log")):
        with log.open("rb") as fh:
            fh.seek(seen.get(log, 0))
            chunk = fh.read()
        whole = chunk[:chunk.rfind(b"\n") + 1]      # a half-written line waits for its end
        seen[log] = seen.get(log, 0) + len(whole)
        if ABORTED in whole:
            return True
    return False


def in_bank(status: str, project: str) -> int:
    """The «In databank» count of an `action=status` reply.

    Returns:
        The count. SystemExit naming the reply when it carries none — `Error: CLI not
        ready.`, or a project SQX does not know.
    """
    found = IN_BANK.search(status)
    if not found:
        raise SystemExit(f"{project}: `action=status` no trae «In databank»; SQX respondió: "
                         f"{status.strip()[:300] or '(vacío)'}")
    return int(found.group(1))


def tested(status: str, project: str, base: int) -> int:
    """How many retests an `action=status` reply says are done, counted from `base`."""
    found = TESTED.search(status)
    return int(found.group(1)) if found else in_bank(status, project) - base

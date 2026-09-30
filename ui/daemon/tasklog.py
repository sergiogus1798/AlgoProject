"""A project's own task log and the worker's status line: counts, times and the running total."""

import re
import time
from datetime import datetime
from pathlib import Path

from core import worker
from core.paths import WORKERS

STAMP = "%Y.%m.%d %H:%M:%S.%f"
STARTED = re.compile(r"TASK STARTED at ([\d.]+ [\d:.]+)")
FINISHED = re.compile(r"TASK FINISHED at ([\d.]+ [\d:.]+)")
TASK = re.compile(r"^Task: (.+), Type: (\w+)", re.M)
BEFORE = re.compile(r"Databanks before start: (.+)")
BANK = re.compile(r"(?:^|, )([^(]+?) \((\d+)\)")
# SQX's durations: «850 ms.», «21 s.», «1 min. 10 s.», «1 hr. 15 min.» (🔬 2026-09-29: past a
# minute per strategy the «N s.» pattern matched nothing and /api/pulse answered 500).
DURATION = r"((?:[\d.]+ (?:hr|min|s|ms)\.\s*)+)"
UNIT_MS = {"hr": 3_600_000, "min": 60_000, "s": 1000, "ms": 1}
TESTED = re.compile(r"Total tested: (\d+), Time per strategy: " + DURATION
                    + r", Passed: (\d+), Failed: (\d+)")
STATUS = {"generated": re.compile(r"Strategies generated\s+(\d+)"),
          "per_strategy_ms": re.compile(r"Time per strategy\s+" + DURATION),
          "running": re.compile(r"Running time so far\s+(.+)"),
          "in_databank": re.compile(r"In databank\s+(\d+)")}


def to_ms(text: str) -> float:
    """Milliseconds in one of SQX's durations, «1 min. 10 s.» → 70000.0."""
    return sum(float(n) * UNIT_MS[u] for n, u in re.findall(r"([\d.]+) (hr|min|s|ms)\.", text))


def task_runs(project_dir: Path) -> list[dict]:
    """Every task start SQX logged for this project today, oldest first.

    Args:
        project_dir: The project's folder; its `log/global_log_<day>_<time>.log` files are
            written by SQX at each start, one per start, and completed at each finish.

    Returns:
        One dict per task: `title`, `type`, `started` and `finished` (ISO or None),
        `elapsed_s`, `before` (databank → count when it started), and when finished
        `tested`, `per_strategy_ms`, `passed`, `failed`.
    """
    out = []
    for f in sorted((project_dir / "log").glob(f"global_log_{datetime.now():%Y%m%d}_*.log")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for chunk in text.split("TASK STARTED at ")[1:]:
            chunk = "TASK STARTED at " + chunk
            task = TASK.search(chunk)
            # SQX writes a start in pieces: read the second after it began, the chunk may stop
            # at its title, with no «Databanks before start» yet. 🔬 2026-09-28: indexing that
            # missing line killed the watcher and, through its `finally`, a live build.
            if task is None:
                continue
            started = datetime.strptime(STARTED.search(chunk).group(1), STAMP)
            fin = FINISHED.search(chunk)
            finished = datetime.strptime(fin.group(1), STAMP) if fin else None
            listed = BEFORE.search(chunk)
            before = ({m.group(1).strip(): int(m.group(2)) for m in BANK.finditer(listed.group(1))}
                      if listed else {})
            row = {"title": task.group(1), "type": task.group(2),
                   "started": started.isoformat(timespec="seconds"),
                   "finished": finished.isoformat(timespec="seconds") if finished else None,
                   "elapsed_s": round(((finished or datetime.now()) - started).total_seconds()),
                   "before": before}
            t = TESTED.search(chunk)
            if t:
                row |= {"tested": int(t.group(1)), "per_strategy_ms": to_ms(t.group(2)),
                        "passed": int(t.group(3)), "failed": int(t.group(4))}
            out.append(row)
    return out


_ASKED: dict[tuple[str, str], tuple[float, str]] = {}
ASK_EVERY_S = 15


def _asked(role: str, project: str) -> str:
    """The worker's status text, asked at most every ASK_EVERY_S for all the daemon's readers.

    The pulse, «En marcha» and the jobs strip each asked on their own, beside the running job's
    own poll: 🔬 2026-09-29 two statuses landed together as SQX closed «WFC 1 IS» and it died
    with a NullPointerException in ProjectGlobalLog (a likely, not a proven, cause). One cached
    answer serves them all.
    """
    now = time.monotonic()
    seen = _ASKED.get((role, project))
    if seen and now - seen[0] < ASK_EVERY_S:
        return seen[1]
    text = worker.call(f"-project action=status name={project}", role)
    _ASKED[(role, project)] = (now, text)
    return text


def status(role: str, project: str) -> dict | None:
    """The worker's own status line for a project, while it runs.

    Args:
        role: A worker role; the master is never asked (its GUI owns its CLI).
        project: Project name.

    Returns:
        `generated` (strategies processed so far), `per_strategy_ms`, `running` (SQX's own
        text) and `in_databank`, or None when the role is not a worker or its process is
        not up. `-project action=status` is the one command the custodian may receive
        between start and collect (owner, 2026-09-25): it syncs nothing.
    """
    if role not in WORKERS or not worker.holding(WORKERS[role]["path"]):
        return None
    text = _asked(role, project)
    got = {k: rx.search(text) for k, rx in STATUS.items()}
    if not got["generated"]:
        return None
    per = got["per_strategy_ms"]
    return {"generated": int(got["generated"].group(1)),
            "per_strategy_ms": to_ms(per.group(1)) if per else None,
            "running": got["running"].group(1).strip(),
            "in_databank": int(got["in_databank"].group(1))}

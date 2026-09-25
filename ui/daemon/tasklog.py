"""A project's own task log and the worker's status line: counts, times and the running total."""

import re
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
TESTED = re.compile(r"Total tested: (\d+), Time per strategy: ([\d.]+) (ms|s)\., Passed: (\d+), Failed: (\d+)")
STATUS = {"generated": re.compile(r"Strategies generated\s+(\d+)"),
          "per_strategy_ms": re.compile(r"Time per strategy\s+([\d.]+) (ms|s)\."),
          "running": re.compile(r"Running time so far\s+(.+)"),
          "in_databank": re.compile(r"In databank\s+(\d+)")}


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
            started = datetime.strptime(STARTED.search(chunk).group(1), STAMP)
            task = TASK.search(chunk)
            fin = FINISHED.search(chunk)
            finished = datetime.strptime(fin.group(1), STAMP) if fin else None
            before = {m.group(1).strip(): int(m.group(2))
                      for m in BANK.finditer(BEFORE.search(chunk).group(1))}
            row = {"title": task.group(1), "type": task.group(2),
                   "started": started.isoformat(timespec="seconds"),
                   "finished": finished.isoformat(timespec="seconds") if finished else None,
                   "elapsed_s": round(((finished or datetime.now()) - started).total_seconds()),
                   "before": before}
            t = TESTED.search(chunk)
            if t:
                unit = 1000 if t.group(3) == "s" else 1
                row |= {"tested": int(t.group(1)), "per_strategy_ms": float(t.group(2)) * unit,
                        "passed": int(t.group(4)), "failed": int(t.group(5))}
            out.append(row)
    return out


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
    text = worker.call(f"-project action=status name={project}", role)
    got = {k: rx.search(text) for k, rx in STATUS.items()}
    if not got["generated"]:
        return None
    per = got["per_strategy_ms"]
    return {"generated": int(got["generated"].group(1)),
            "per_strategy_ms": float(per.group(1)) * (1000 if per.group(2) == "s" else 1),
            "running": got["running"].group(1).strip(),
            "in_databank": int(got["in_databank"].group(1))}

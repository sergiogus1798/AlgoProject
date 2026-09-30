"""What each SQX worker runs right now and how far its task is: the SQX bars of the jobs strip."""

from core import worker
from core.paths import WORKERS
from ui.daemon import progress


def count(role: str, project: str) -> dict | None:
    """How far the running task of one project is, from `progress.state`.

    Args:
        role: A worker role.
        project: The project its log says is running.

    Returns:
        `task`, `done`, `total` (None for a build: it has no input to count against),
        `elapsed_s` (the task's own clock, from the project log) and `percent` — SQX's own compute-thread figure when the log carries one, else done over
        total — or None when the project is not on disk or has no running task. The only
        command this can send is `progress.state`'s `-project action=status`, the one the
        custodian may receive between start and collect (CLAUDE.md rule 3).
    """
    install = WORKERS[role]["path"]
    if project not in progress.projects(install):
        return None                       # the log names a project since retired
    got = progress.state(role, project)
    now = next((t for t in got["tasks"] if t["status"] == "running"), None)
    if now is None:
        return None
    done, total = now["done"], now["total"]
    percent = got["run"]["percent"]
    if percent is None and done is not None and total:
        percent = min(100, round(100 * done / total))
    return {"task": now["title"], "done": done, "total": total,
            "elapsed_s": now.get("elapsed_s"), "percent": percent}


def running(role: str) -> dict | None:
    """The project one worker is running, if any.

    Args:
        role: A worker role.

    Returns:
        `role`, `project` and what `count` adds, or None when the worker is down or its
        log's last start has finished. A worker that is up with nothing running is None too.
    """
    install = WORKERS[role]["path"]
    if not worker.holding(install):
        return None
    run = progress.run_state(progress.log_lines(install)[0])
    if not run["project"] or run["finished"]:
        return None
    base = {"role": role, "project": run["project"], "task": run["current"], "done": None,
            "total": None, "percent": run["percent"]}
    return base | (count(role, run["project"]) or {})


def runs() -> list[dict]:
    """Every worker's running project, custodian first: it is the one that holds long runs.

    Returns:
        What `running` returns for each worker that runs something. The master is never
        read here: its GUI owns its CLI, and a run there is the owner's.
    """
    roles = sorted(WORKERS, key=lambda r: r != "custodian")
    return [got for role in roles if (got := running(role))]

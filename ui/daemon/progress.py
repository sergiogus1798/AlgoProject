"""Where a running SQX project is: its tasks, which one runs, how far, read from disk only."""

import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MASTER, WORKERS
from sqx.projects import live
from ui.daemon import tasklog
from ui.daemon.daylog import PERCENT, PROGRESS, STARTING, log_lines, trim  # noqa: F401

TAIL_LINES = 14


def installs() -> dict[str, Path]:
    """Every SQX install this machine declares, by role.

    Returns:
        Role → top folder. The master is included read-only: the window opens two files
        of it and sends it nothing.
    """
    return {**{role: w["path"] for role, w in WORKERS.items()}, "master": MASTER}


def projects(install: Path) -> list[str]:
    """The projects an install holds.

    Args:
        install: Its top folder.

    Returns:
        Names of every folder under `user/projects` with a `project.cfx`, sorted.
    """
    return sorted(p.parent.name for p in (install / "user" / "projects").glob("*/project.cfx"))


def tasks(cfx: Path) -> list[dict]:
    """The tasks of a project, in the order SQX runs them.

    Args:
        cfx: The project's `project.cfx`, a zip.

    Returns:
        One dict per task: `title` (what the log calls it), `type`, `active` (what the next
        start runs), `output` and `input` databank names.
    """
    out = []
    with zipfile.ZipFile(cfx) as z:
        root = ElementTree.fromstring(z.read("config.xml"))
        for t in root.iter("Task"):
            settings = ElementTree.fromstring(z.read(t.get("taskXMLFile")))
            banks = {d.get("name"): d.get("value") for d in settings.iter("Databank")}
            out.append({"title": t.get("title"), "type": t.get("type"),
                        "active": t.get("active") == "true",
                        "output": banks.get("Output", ""), "input": banks.get("Input", "")})
    return out


def counts(project_dir: Path) -> dict[str, int]:
    """How many strategies each databank holds on disk.

    Args:
        project_dir: The project's folder.

    Returns:
        Databank name → `.sqx` files. SQX writes them on sync, so a running task's output
        lags until it saves.
    """
    return {d.name: sum(1 for _ in d.glob("*.sqx"))
            for d in (project_dir / "databanks").glob("*") if d.is_dir()}   # none before its first run


def run_state(lines: list[str]) -> dict:
    """What the log says about the last project start.

    Args:
        lines: The tail of the log.

    Returns:
        `project` — the last one started, or None; `finished` — whether the log has seen
        «Project finished» since; `events` — task title → «running», «done» or «skipped»,
        in the order they appeared; `percent` — the last figure a compute thread carried
        after the running task began, or None; `tail` — the last progress lines; `current`
        — the task running, or None.
    """
    project, finished, events, percent, current = None, True, {}, None, None
    tail: list[str] = []
    since = 0   # index of the running task's first line; a percentage before it is another task's
    for i, line in enumerate(lines):
        m = STARTING.search(line)
        if m:
            project, finished, events, percent, current = m.group(1), False, {}, None, None
            continue
        p = PROGRESS.search(line)
        if not p:
            continue
        text = p.group(1)
        tail.append(line[:12] + " " + text)
        if text.startswith("Project finished") or text.startswith("Project stopped"):
            finished, current = True, None
            continue
        if "Error while running project" in text:
            # SQX aborted the run and will never write «Project finished» (🔬 2026-09-29):
            # it is an end, and a watcher waiting for the finish would wait forever.
            finished, current, events["error"] = True, None, "aborted"
            continue
        if " : " not in text:
            continue
        title, message = text.split(" : ", 1)
        if message.startswith("SKIPPED"):
            events[title] = "skipped"
        elif message.startswith("Task finished"):
            events[title] = "done"
            current, percent = None, None
        elif events.get(title) != "done":
            if current != title:
                current, percent, since = title, None, i
            events[title] = "running"
    for line in reversed(lines[since:]):
        m = PERCENT.search(line)
        if m:
            percent = int(m.group(1))
            break
    return {"project": project, "finished": finished, "events": events, "current": current,
            "percent": None if finished else percent, "tail": tail[-TAIL_LINES:]}


def in_memory(task: dict, status: str, runs: list[dict], live: dict | None) -> int | None:
    """What SQX itself holds in a task's output databank, which the disk shows only after a sync.

    Args:
        task: One row of `tasks`.
        status: Its status in this start.
        runs: `tasklog.task_runs` of the project, oldest first.
        live: The worker's `status` while this project runs, or None.

    Returns:
        The running task: SQX's own «In databank». Any other: the count SQX logged for that
        databank at the latest task start («Databanks before start» is memory, not files),
        unless that start is the task's own — then it predates what the task wrote. None when
        neither says.
    """
    if status == "running":
        return live["in_databank"] if live else None
    if not runs or runs[-1]["title"] == task["title"]:
        return None
    return runs[-1]["before"].get(task["output"])


def gui_memory(role: str, project: str) -> dict[str, int] | None:
    """Strategies per databank in a GUI session's memory (`sqx.projects.live`), None without one.

    The window's boundary: a session closing between the check and the call answers None.
    """
    if role not in WORKERS or not live.gui_up(role):
        return None
    try:
        return live.records(role, project)
    except (OSError, SystemExit, KeyError):
        return None


def state(role: str, project: str) -> dict:
    """Everything the generation zone draws for one project of one install.

    Args:
        role: An install role, as `installs()` lists them.
        project: A project name of that install.

    Returns:
        `tasks` with each task's `status` — `done`, `running`, `skipped`, `earlier` (skipped
        in this start but its output databank holds strategies: a previous start did it),
        `queued` (active, not reached), `inactive` — its `strategies` on disk, and from the
        project's own log `started`, `elapsed_s`, `total` (its input databank when it
        started), `done` (tested, or the worker's count while it runs), `per_strategy_ms`;
        `run`, what the install log says; `workflow_s`, from today's first task start to
        the last finish or now; `status`, the worker's line; `log_age_s`.
    """
    install = installs()[role]
    folder = install / "user" / "projects" / project
    lines, mtime = log_lines(install)
    run = run_state(lines)
    held = counts(folder)
    runs = tasklog.task_runs(folder)
    # A start with no finish and later starts after it is a run that was killed: its
    # counts are another population's (📓 2026-09-29, the cancelled MCR 2 Spread over 200
    # lent its total to the next one over 21, whose own start SQX had not logged yet).
    by_title = {r["title"]: r for i, r in enumerate(runs)
                if r["finished"] or i == len(runs) - 1}
    going = run["project"] == project and not run["finished"]
    live = tasklog.status(role, project) if going else None
    mem = gui_memory(role, project) if going and not live else None
    rows = []
    for t in tasks(folder / "project.cfx"):
        seen = run["events"].get(t["title"]) if run["project"] == project else None
        status = seen or ("queued" if t["active"] else "inactive")
        if status == "skipped" and held.get(t["output"]):
            status = "earlier"
        row = {**t, "status": status, "strategies": held.get(t["output"]),
               "in_memory": in_memory(t, status, runs, live),
               "started": None, "elapsed_s": None, "total": None, "done": None,
               "per_strategy_ms": None}
        r = by_title.get(t["title"])
        if r:
            # The project log writes «Databanks before start» late, not when the task
            # begins (📓 2026-09-29, MCR 1 Bar: 2 min in, still absent), so a running retest
            # had no total; its input databank on disk does not change while it reads it.
            total = (r["before"].get(t["input"], held.get(t["input"]))
                     if t["type"] != "Build" else None)
            row |= {"started": r["started"], "elapsed_s": r["elapsed_s"], "total": total,
                    "done": r.get("tested"), "per_strategy_ms": r.get("per_strategy_ms")}
            if status == "running" and live:
                row["done"] = live["generated"]
                row["per_strategy_ms"] = (live["per_strategy_ms"] or
                                          (r["elapsed_s"] * 1000 / live["generated"]
                                           if live["generated"] else None))
        elif status == "running" and live:
            # Running, but its start is not in the project log yet (SQX writes it late):
            # the worker's count over the input on disk.
            row |= {"done": live["generated"], "per_strategy_ms": live["per_strategy_ms"],
                    "total": held.get(t["input"]) if t["type"] != "Build" else None}
        if status == "running" and mem:
            # A GUI session has no `action=status`: the task's output in SQX's memory is its
            # count — every retest here is silenced, so each strategy tested lands there.
            base = r["before"].get(t["output"], 0) if r and t["type"] != "Build" else 0
            row |= {"in_memory": mem.get(t["output"]),
                    "done": (mem.get(t["output"]) or 0) - base}
            if row["elapsed_s"] and row["done"]:
                row["per_strategy_ms"] = row["elapsed_s"] * 1000 / row["done"]
        if row["total"] == 0 and row["done"]:
            # An input loaded through the API after the start (the WFC legs' WFC_Variants) is
            # empty on disk: «190 de 0» (📓 2026-09-29). Unknown, not zero.
            row["total"] = None
        rows.append(row)
    first = datetime.fromisoformat(runs[0]["started"]) if runs else None
    last = (datetime.fromisoformat(runs[-1]["finished"]) if runs and runs[-1]["finished"]
            else datetime.now())
    return {"tasks": rows, "run": run, "banks": held, "status": live,
            "workflow_s": round((last - first).total_seconds()) if first else None,
            "log_age_s": round(datetime.now().timestamp() - mtime) if mtime else None}

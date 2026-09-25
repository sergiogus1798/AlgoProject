"""Where a running SQX project is: its tasks, which one runs, how far, read from disk only."""

import re
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MASTER, WORKERS

TAIL_BYTES = 2_000_000
TAIL_LINES = 14
PROGRESS = re.compile(r"ProgressEngine - (.+)$")
PERCENT = re.compile(r"\[Blocking computeThread[^\]]*?(\d+) %")
STARTING = re.compile(r"Starting project '([^']+)'")


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
            for d in (project_dir / "databanks").iterdir() if d.is_dir()}


def log_lines(install: Path) -> tuple[list[str], float]:
    """The end of today's SQX log.

    Args:
        install: The install's top folder.

    Returns:
        Its last `TAIL_BYTES` as lines, and the file's modification time as a timestamp.
        Today's file only: a run that crosses midnight starts a new one, and reading the
        whole 40 MB day would make every refresh cost what one tail costs.
    """
    f = install / "user" / "log" / "StrategyQuant" / f"log_{datetime.now():%Y_%m_%d}.log"
    if not f.exists():
        return [], 0.0
    with f.open("rb") as fh:
        fh.seek(max(0, f.stat().st_size - TAIL_BYTES))
        data = fh.read().decode("utf-8", errors="replace")
    return data.splitlines()[1:], f.stat().st_mtime


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
    for line in lines:
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
                current, percent = title, None
            events[title] = "running"
    for line in reversed(lines):
        m = PERCENT.search(line)
        if m:
            percent = int(m.group(1))
            break
    return {"project": project, "finished": finished, "events": events, "current": current,
            "percent": None if finished else percent, "tail": tail[-TAIL_LINES:]}


def state(role: str, project: str) -> dict:
    """Everything the generation zone draws for one project of one install.

    Args:
        role: An install role, as `installs()` lists them.
        project: A project name of that install.

    Returns:
        `tasks` with each task's `status` — `done`, `running`, `skipped`, `earlier` (skipped
        in this start but its output databank holds strategies: a previous start did it),
        `queued` (active, not reached), `inactive` — and `strategies`, its output
        databank's count on disk;
        `run`, what the log says (whose `project` may be another one: the log is per
        install); `log_age_s`, seconds since the log last grew.
    """
    install = installs()[role]
    folder = install / "user" / "projects" / project
    lines, mtime = log_lines(install)
    run = run_state(lines)
    held = counts(folder)
    rows = []
    for t in tasks(folder / "project.cfx"):
        seen = run["events"].get(t["title"]) if run["project"] == project else None
        status = seen or ("queued" if t["active"] else "inactive")
        if status == "skipped" and held.get(t["output"]):
            status = "earlier"
        rows.append({**t, "status": status, "strategies": held.get(t["output"])})
    return {"tasks": rows, "run": run, "banks": held,
            "log_age_s": round(datetime.now().timestamp() - mtime) if mtime else None}

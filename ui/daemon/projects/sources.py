"""Every project the window can open, merged from the four places that each know part of it."""

import re
import zipfile
from functools import cache, lru_cache
from pathlib import Path

from core import worker
from core.paths import DATA
from sqx.projects import registry
from sqx.projects.retire import STOCK
from ui.daemon import progress, runs
from ui.daemon.loader import find

# The order the gallery lists states in: what moves first, then what can be opened.
ORDER = ("corriendo", "parado", "terminado", "construido", "ausente")
FIRST_TASK = re.compile(r'<Task [^>]*taskXMLFile="([^"]+)"')
CHART = re.compile(r'<Chart symbol="([^"]+)" timeframe="([^"]+)"')
LABEL = {"master": "maestro", "conductor": "conductor", "custodian": "custodio"}


def registered() -> dict[str, dict]:
    """The live row of every project `registry.csv` knows, by name (a rebuild's row wins)."""
    return {r["name"]: r for r in registry.rows() if not r["retired"]}


def on_disk() -> dict[str, tuple[str, Path]]:
    """Every custom project an install holds, by name, with the install that answers for it.

    Returns:
        Name → (role, top folder). Workers first, as `find.install_of` does: a project the
        owner copied to the master to look at is the worker's. SQX's five stock projects are
        not projects of anyone's (CLAUDE.md rule 10) and are left out.
    """
    out: dict[str, tuple[str, Path]] = {}
    for role, top in progress.installs().items():
        for name in progress.projects(top):
            if name not in STOCK:
                out.setdefault(name, (role, top))
    return out


def reported() -> set[str]:
    """Projects with a folder under `AlgoData/reports/` (the old `/api/projects` list)."""
    root = DATA / "reports"
    return {p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")}


@cache
def chart(cfx: Path, stamp: float) -> tuple[str | None, str | None]:
    """The symbol and timeframe of the project's main chart, read off its first task.

    Args:
        cfx: The project's `project.cfx`, a zip.
        stamp: Its mtime: the cache key, so a rebuilt project is read again.

    Returns:
        (`USDJPY`, `M30`) from the first `<Chart symbol timeframe>` of the first task; (None,
        None) for a project with no task. Searched, not parsed: a task file runs to megabytes
        and parsing fourteen of them cost the gallery a second.
    """
    with zipfile.ZipFile(cfx) as z:
        first = FIRST_TASK.search(z.read("config.xml").decode("utf-8", "replace"))
        if first is None:
            return None, None
        found = CHART.search(z.read(first.group(1)).decode("utf-8", "replace"))
    if found is None:
        return None, None
    return found.group(1).split("_")[0], found.group(2)


@cache
def distinct(project: str, databank: str, stamp: float) -> int:
    """How many distinct strategies a databank holds, for one state of its folder.

    Args:
        project: Project name.
        databank: Databank name.
        stamp: The folder's mtime, which changes when a file comes or goes: a new stamp is a
            new entry. Kept here, unbounded (an int per state), because `find.roster`'s own
            cache holds 64 folders and the gallery walks every databank of every install.
    """
    return len(find.roster(project, databank))


def banks(name: str, top: Path) -> dict[str, int]:
    """Strategies per databank, from each databank's roster (identity → name).

    Args:
        name: Project name.
        top: The install holding it.

    Returns:
        Databank → distinct strategies; an empty folder is 0 without hashing anything. The
        roster is empty while SQX writes the project, so the caller counts a running
        project by its files instead (`progress.counts`).
    """
    folder = top / "user" / "projects" / name / "databanks"
    return {d.name: distinct(name, d.name, d.stat().st_mtime) if any(d.glob("*.sqx")) else 0
            for d in sorted(folder.iterdir()) if d.is_dir()}


def ending(run: dict) -> str:
    """How the last start of the log ended: «Project stopped» or «Project finished»."""
    stopped = next((line for line in reversed(run["tail"])
                    if "Project stopped" in line or "Project finished" in line), "")
    return "parado" if "Project stopped" in stopped else "terminado"


def state(role: str, top: Path, name: str, run: dict, held: int) -> tuple[str, str, dict | None]:
    """Where one project stands, from its install's log; a live worker is asked only its status.

    Args:
        role: Install role.
        top: Its top folder.
        name: Project name.
        run: `progress.run_state` of the install's log today.
        held: Strategies its databanks hold on disk.

    Returns:
        (state, the sentence that says how it was known, the worker's status line or None).
        Only a worker whose process is up and whose log has this project running gets
        `-project action=status` (through `progress.state`); never `count`, which syncs from
        the files and wipes what is only in memory (CLAUDE.md rule 3). The master is files.
    """
    if run["project"] == name and not run["finished"]:
        if role != "master" and not worker.holding(top):
            return "parado", "El log de hoy lo dejó a medias y el worker está parado.", None
        live = progress.state(role, name)["status"]
        return "corriendo", "El log de hoy lo tiene en marcha.", live
    if run["project"] == name:
        said = ending(run)
        word = "stopped" if said == "parado" else "finished"
        return said, f"El log de hoy dice «Project {word}».", None
    if held:
        return "terminado", "No corre hoy y sus databanks guardan estrategias.", None
    return "construido", "Existe, ninguna tarea ha dejado estrategias todavía.", None


def template(path: str) -> str | None:
    """A registry template path as its library name: `.../library/<name>/template.sqx` → name."""
    if not path:
        return None
    p = Path(path)
    return p.parent.name if p.name == "template.sqx" else p.stem


def card(name: str, where: tuple[str, Path] | None, row: dict, runs_today: dict,
         has_reports: bool) -> dict:
    """One gallery card: what `fake.projects` promised, plus where each figure came from.

    Args:
        name: Project name.
        where: (role, top) of the install that holds it, or None when only reports remain.
        row: Its live `registry.csv` row, or {}.
        runs_today: Role → `progress.run_state` of that install's log.
        has_reports: Whether `AlgoData/reports/<name>/` exists.

    Returns:
        name, symbol, timeframe, strategies, databanks {name: count}, template, state, why,
        live, install (role), install_label, kind, purpose, reports.
    """
    base = {"name": name, "kind": registry.kind(name), "purpose": row.get("purpose", ""),
            "template": template(row.get("template", "")), "reports": has_reports}
    if where is None:
        return {**base, "symbol": row.get("symbol") or runs.guess_asset(name),
                "timeframe": row.get("timeframe") or None, "strategies": 0, "databanks": {},
                "state": "ausente", "why": "Ya no está en ningún install; quedan sus informes.",
                "live": None, "install": None, "install_label": "ningún install"}
    role, top = where
    folder = top / "user" / "projects" / name
    cfx = folder / "project.cfx"
    symbol, timeframe = chart(cfx, cfx.stat().st_mtime)
    run = runs_today[role]
    writing = run["project"] == name and not run["finished"]      # what `find.writing` reads
    counted = progress.counts(folder) if writing else banks(name, top)
    said, why, live = state(role, top, name, run, sum(counted.values()))
    return {**base, "symbol": row.get("symbol") or symbol or runs.guess_asset(name),
            "timeframe": row.get("timeframe") or timeframe, "strategies": sum(counted.values()),
            "databanks": counted, "state": said, "why": why, "live": live, "install": role,
            "install_label": LABEL.get(role, role)}


def gallery() -> list[dict]:
    """Every card, the running ones first, then by name.

    Returns:
        One `card` per project on an install or with reports. A registry row whose project
        is on no install and left no report is a retired project's ghost and is not listed.
    """
    held, rows, reps = on_disk(), registered(), reported()
    runs_today = {role: progress.run_state(progress.log_lines(top)[0])
                  for role, top in progress.installs().items()}
    cards = [card(n, held.get(n), rows.get(n, {}), runs_today, n in reps)
             for n in sorted(set(held) | reps)]
    return sorted(cards, key=lambda c: (ORDER.index(c["state"]), c["name"]))


def locate(project: str, identity: str, databank: str = "") -> dict:
    """Which databank of a project holds a strategy, and its name there.

    Args:
        project: Project name.
        identity: The strategy's SHA-256 identity.
        databank: The databank to look in first (the one the window has selected), or "".

    Returns:
        `{databank, name}`, or `{error}` when no databank of the project holds it.
    """
    where = on_disk().get(project)
    names = [databank] if databank else []
    if where:
        names += [d.name for d in sorted((where[1] / "user" / "projects" / project /
                                           "databanks").iterdir()) if d.is_dir()]
    for d in names:
        got = find.roster(project, d).get(identity)
        if got:
            return {"databank": find.spelled(project, d), "name": got}
    return {"error": f"ninguna databank de {project} guarda esa estrategia"}

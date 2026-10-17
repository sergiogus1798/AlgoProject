"""What a project's folder on disk says: the installs, their projects, a project's tasks, databank counts, genetic settings."""

import re
import shutil
import zipfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

from core.datapaths import project_registry
from core.paths import MASTER, WORKERS
from sqx.projects.buildcensus import census

# The project folder before a start (hard rule 1), without log/; deleted once the counts match.
SNAPSHOTS = project_registry().parent / "snapshots"


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
    return sorted(
        p.parent.name for p in (install / "user" / "projects").glob("*/project.cfx")
    )


def tasks(cfx: Path) -> list[dict]:
    """The tasks of a project, in the order SQX runs them; read again only when its file changed.

    Args:
        cfx: The project's `project.cfx`, a zip.

    Returns:
        One dict per task: `title` (what the log calls it), `type`, `active` (what the next
        start runs), `output` and `input` databank names.
    """
    return [dict(t) for t in _tasks(cfx, cfx.stat().st_mtime_ns)]


@lru_cache(maxsize=256)
def _tasks(cfx: Path, stamp: int) -> tuple[dict, ...]:
    """`tasks` for one mtime `stamp` (the cache key): the zip is opened once per save."""
    out = []
    with zipfile.ZipFile(cfx) as z:
        root = ElementTree.fromstring(z.read("config.xml"))
        for t in root.iter("Task"):
            settings = ElementTree.fromstring(z.read(cast(str, t.get("taskXMLFile"))))
            banks = {d.get("name"): d.get("value") for d in settings.iter("Databank")}
            out.append(
                {
                    "title": t.get("title"),
                    "type": t.get("type"),
                    "active": t.get("active") == "true",
                    "output": banks.get("Output", ""),
                    "input": banks.get("Input", ""),
                }
            )
    return tuple(out)


def counts(project_dir: Path) -> dict[str, int]:
    """How many strategies each databank holds on disk.

    Args:
        project_dir: The project's folder.

    Returns:
        Databank name → `.sqx` files. SQX writes them on sync, so a running task's output
        lags until it saves.
    """
    return {
        d.name: sum(1 for _ in d.glob("*.sqx"))
        for d in (project_dir / "databanks").glob("*")
        if d.is_dir()
    }  # none before its first run


def genetic(cfx: Path, running: bool, banks: dict[str, int]) -> dict | None:
    """The running Build's genetic settings and the two genetic databanks, read off disk.

    Neither SQX's `action=status` nor its log carries a generation, an island or the initial
    population's fill (🔬 2026-10-04, w1/w2 logs), so only the settings and the databanks'
    files — which SQX writes on sync, so they lag — are shown.

    Args:
        cfx: The project's cfx file (read only).
        running: Whether a Build task runs in this start.
        banks: `counts` of the project.

    Returns:
        `population` (PopulationSize × Islands, what must fill before the databank gets any),
        `size`, `islands`, `generations`, `initial`, `last` and `results` (files in «Initial
        population», «Last generation» and «Results»); None when no Build runs or it is not genetic.
    """
    if not running:
        return None
    try:
        c = census(cfx)
        if c["generation"] != "genetic-evolution":
            return None
        g = c["genetic"]
        size, islands = int(g["PopulationSize"]), int(g["Islands"])
    except (StopIteration, AttributeError, KeyError, ValueError, zipfile.BadZipFile):
        return None
    return {
        "population": size * islands,
        "size": size,
        "islands": islands,
        "generations": int(g["MaxGenerations"]),
        "initial": banks.get("Initial population"),
        "last": banks.get("Last generation"),
        "results": banks.get("Results"),
    }


def snapshot(folder: Path) -> Path:
    """Copy the project aside, `log/` left out (knowhow/databanks/snapshot-before-restart.md);
    named `.partial` until complete, and a copy cut short (a cancel) is removed."""
    to = SNAPSHOTS / folder.name / f"{datetime.now():%Y%m%d-%H%M%S}"
    partial = to.with_name(to.name + ".partial")
    partial.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(folder, partial, ignore=shutil.ignore_patterns("log"))
    except BaseException:  # SystemExit from a SIGTERM too
        shutil.rmtree(partial, ignore_errors=True)
        raise
    return partial.rename(to)


def compare(
    before: dict[str, int], after: dict[str, int], output: str | set[str], kept: Path
) -> str:
    """The line on what the run did to the databanks; the snapshot goes only when nothing fell.

    Args:
        before: `counts` before the start.
        after: `counts` after the stop.
        output: The tasks' own output databank(s), which they may clear by configuration.
        kept: The snapshot.

    Returns:
        The line to print. A databank no task of the run writes that lost files keeps the
        snapshot (hard rule 1: a sync deletes what is not in memory).
    """
    outputs = {output} if isinstance(output, str) else output
    fell = {
        d: (n, after.get(d, 0))
        for d, n in before.items()
        if d not in outputs and after.get(d, 0) < n
    }
    if fell:
        return (
            "⚠️ bajaron databanks que la tarea no escribe: "
            + ", ".join(f"{d} {a} → {b}" for d, (a, b) in fell.items())
            + f". La copia se queda en {kept}"
        )
    shutil.rmtree(kept)
    return "ningún otro databank bajó; la copia de seguridad se ha borrado"


INTERRUPTED = re.compile(r"Cannot process strategy '([^']+)'")


def restore(
    project_dir: Path,
    kept: Path,
    before: dict[str, int],
    outputs: set[str],
    lines: list[str],
) -> list[str]:
    """Put back the strategies SQX's own sync race deleted, from the pre-run snapshot.

    🔬 2026-09-29: the stop's shutdown sync ran while a periodic sync of «Retest Markets -
    Family» held a strategy's lock; SQX logged «Cannot process strategy 'Strategy 9.11.67'»
    (InterruptedException) and the periodic sync then counted it removed and deleted its
    file. Only a strategy named in such a line, missing from a databank no task of the run
    writes, is copied back — the worker is stopped, so nothing rewrites it.

    Args:
        project_dir: The project's folder on the install.
        kept: The snapshot of it taken before the start.
        before: `counts` before the start.
        outputs: The run's own output databanks.
        lines: The install log's lines written since the start.

    Returns:
        «databank/strategy» per file restored.
    """
    named = {m.group(1) for line in lines for m in [INTERRUPTED.search(line)] if m}
    back = []
    for bank in (b for b in before if b not in outputs):
        for f in (kept / "databanks" / bank).glob("*.sqx") if named else []:
            live = project_dir / "databanks" / bank / f.name
            if f.stem in named and not live.exists():
                shutil.copy2(f, live)
                back.append(f"{bank}/{f.stem}")
    return back

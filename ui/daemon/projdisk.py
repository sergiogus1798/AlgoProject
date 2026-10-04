"""What a project's folder on disk says: the installs, their projects, a project's tasks, databank counts, genetic settings."""

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MASTER, WORKERS
from sqx.projects.buildcensus import census


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
    return {"population": size * islands, "size": size, "islands": islands,
            "generations": int(g["MaxGenerations"]), "initial": banks.get("Initial population"),
            "last": banks.get("Last generation"), "results": banks.get("Results")}

"""What the disk holds for one project: its install, its tasks, its study results, its template."""

import csv
import json
from datetime import datetime
from pathlib import Path

from core.datapaths import project_registry, template_dir, template_runs
from core.paths import DATA
from ui.daemon import progress, tasklog
from ui.daemon.workflow.steps import BATCH_ROOTS, DROP

# Which install holds a project when more than one does: the workers run the workflow; the
# master only ever holds a copy the owner made to look at (CLAUDE.md rule 3).
PREFERENCE = ("custodian", "conductor", "master")


def install(project: str) -> tuple[str, Path] | None:
    """The install whose `user/projects` holds this project.

    Args:
        project: SQX project name.

    Returns:
        (role, top folder), the first in `PREFERENCE` order, or None.
    """
    found = progress.installs()
    return next(((role, found[role]) for role in PREFERENCE
                 if role in found and project in progress.projects(found[role])), None)


def sqx_view(role: str, top: Path, project: str) -> dict:
    """The project's tasks, today's task runs and the install log's last start. Files only.

    Args:
        role: Install role.
        top: Install folder.
        project: Project name.

    Returns:
        `tasks` (from project.cfx), `banks` (databank → .sqx on disk), `runs` (today's task
        runs from the project's own log) and `run` (what the install log says). Unlike
        `progress.state` this never asks the worker for its status line: the rail sends no
        command to any install.
    """
    folder = top / "user" / "projects" / project
    lines, _ = progress.log_lines(top)
    return {"role": role, "folder": folder, "tasks": progress.tasks(folder / "project.cfx"),
            "banks": progress.counts(folder), "runs": tasklog.task_runs(folder),
            "run": progress.run_state(lines)}


def day_of(path: Path) -> str:
    """The day a file or folder was last written, ISO."""
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def results(project: str, key: str, strategy_runs: bool | None = None) -> list[dict]:
    """Every contract result of one study for one project, newest first.

    Args:
        project: Project name.
        key: Study folder name, e.g. "gate".
        strategy_runs: For edgeCost, which runs to keep: True only those launched with
            `--strategy` (step 25), False only the population ones (step 8), None all.

    Returns:
        One dict per result: `path`, `day`, `databank` (None for a batch) and `manifest`.
        Reports live under reports/<project>/<databank>/<day>/<key>/; batch studies under
        `BATCH_ROOTS`/<project>/<batch>/estudios/<key>(.json).
    """
    found = []
    for folder in (DATA / "reports" / project).glob(f"*/*/{key}"):
        m = folder / "manifest.json"
        manifest = json.loads(m.read_text(encoding="utf-8")) if m.exists() else {}
        found.append({"path": folder, "day": folder.parent.name,
                      "databank": folder.parent.parent.name, "manifest": manifest})
    for root in BATCH_ROOTS:
        for hit in (DATA / root / project).glob(f"*/estudios/{key}*"):
            if hit.name in (key, f"{key}.json"):
                found.append({"path": hit, "day": day_of(hit), "databank": None,
                              "manifest": {}})
    if strategy_runs is not None:
        found = [r for r in found
                 if ("--strategy" in r["manifest"].get("command", "")) == strategy_runs]
    return sorted(found, key=lambda r: r["day"], reverse=True)


def funnel(result: dict) -> tuple[int | None, int | None, str]:
    """What entered one study result, what it kept, and the words it used.

    Args:
        result: One entry of `results`.

    Returns:
        (in, out, breakdown). A gate manifest's `entered`/`survives` first; else the rows
        of `verdict.csv`, out being those whose verdict is not in `DROP`; else the count of
        per-strategy JSONs with out = in (a study that describes removes nobody). A batch
        result counts as one batch: its verdict.csv is shared by the studies of that batch.
    """
    if result["databank"] is None:
        return 1, 1, ""
    counts = result["manifest"].get("counts", {})
    if "entered" in counts:
        return counts["entered"], counts["survives"], ""
    folder = result["path"]
    verdict = folder / "verdict.csv" if folder.is_dir() else folder.parent / "verdict.csv"
    if verdict.exists():
        with verdict.open(newline="", encoding="utf-8") as f:
            words = [row.get("verdict", "") for row in csv.DictReader(f)]
        tally = {w: words.count(w) for w in dict.fromkeys(words)}
        kept = sum(n for w, n in tally.items() if w not in DROP)
        return len(words), kept, " · ".join(f"{w or '—'} {n}" for w, n in tally.items())
    many = len(list((folder / "estrategias").glob("*.json")))
    return many, many, ""


def template(project: str, studies: list[str]) -> tuple[str | None, str]:
    """The template a project was built from, and where that link is written.

    Args:
        project: Project name.
        studies: The ledger study ids tied to this project, whose family may name it.

    Returns:
        (template name or None, the source in Spanish). runs.csv and the project registry
        record the link; failing them, a ledger family that is a folder of the library.
    """
    for source, path in (("runs.csv", template_runs()), ("projects/registry.csv",
                                                           project_registry())):
        if path.exists():
            with path.open(newline="", encoding="utf-8") as f:
                rows = [r for r in csv.DictReader(f) if r.get("project", r.get("name")) == project]
            if rows and rows[-1].get("template"):
                path = Path(rows[-1]["template"])
                # a library template is <name>/template.sqx: its name is the folder's
                return (path.parent.name if path.name == "template.sqx" else path.stem), source
    for study in studies:
        family = study.split("_", 2)[-1]   # a study id is <symbol>_<timeframe>_<family>
        if template_dir(family).is_dir():
            return family, f"la familia del estudio {study} en el ledger"
    return None, ""


def variants(project: str) -> tuple[int, int, str | None]:
    """The mothers of step 16.5 and how many have their batch collected.

    Args:
        project: Project name.

    Returns:
        (mothers with a batch folder, mothers with `collected.json`, newest day or None).
    """
    batches = [b for b in (DATA / "strategyPermutations" / project).glob("*") if b.is_dir()]
    done = [b / "collected.json" for b in batches if (b / "collected.json").exists()]
    return len(batches), len(done), max((day_of(f) for f in done), default=None)


def curated(project: str, databank: str) -> str:
    """What `/curate` last removed from a databank, as a Spanish clause, or ''."""
    hits = sorted((DATA / "reports" / project / databank).glob("*/curate/manifest.json"))
    if not hits:
        return ""
    c = json.loads(hits[-1].read_text(encoding="utf-8")).get("counts", {})
    return f"; /curate quitó {c.get('removed')} de {c.get('judged')} ({hits[-1].parts[-3]})"

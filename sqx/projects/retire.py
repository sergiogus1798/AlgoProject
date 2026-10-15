"""List the custom projects of every install, and retire the ones a finished run left behind."""

import argparse
import shutil
import tarfile
import time
import zipfile
from collections.abc import Callable
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from core.datapaths import retired_project
from core.paths import MASTER, WORKERS
from core.store import save
from core.worker import holding, installs
from sqx.projects import cfxio
from sqx.projects import registry, sweep
from core.xmlget import el
from typing import TypedDict

STOCK = {"Builder", "Retester", "Optimizer", "PortfolioComposer", "PortfolioMaster"}
FRESH_MINUTES = 60  # younger than this, someone may still be collecting from it


def master_up() -> bool:
    """Whether any process runs from inside the master install (its GUI or a sqcli)."""
    return bool(holding(MASTER))


class Described(TypedDict):
    """One project folder: task count (or "?"), last change and size on disk."""

    tasks: int | str
    mtime: float
    mb: float


def describe(folder: Path) -> Described:
    """One project's task count, last change and size on disk."""
    tasks = "?"
    try:
        with zipfile.ZipFile(folder / "project.cfx") as z:
            tasks = len(el(ElementTree.fromstring(z.read("config.xml")).find("Tasks")))
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError, TypeError):
        pass
    files = [p for p in folder.rglob("*") if p.is_file()]
    newest = max((p.stat().st_mtime for p in files), default=folder.stat().st_mtime)
    return {
        "tasks": tasks,
        "mtime": newest,
        "mb": sum(p.stat().st_size for p in files) / 1e6,
    }


def listing() -> None:
    """Print every custom project, per install, with what the registry knows of it."""
    known = {(r["install"], r["name"]): r for r in registry.rows() if not r["retired"]}
    for role, inst in installs().items():
        projects = sorted(
            p
            for p in (inst / "user/projects").iterdir()
            if p.is_dir() and p.name not in STOCK
        )
        print(f"== {role} ({inst.name}) — {len(projects)} custom")
        for p in projects:
            d, r = describe(p), known.get((inst.name, p.name), {})
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(d["mtime"]))
            print(
                f"  {p.name:<34} {d['tasks']:>3} tareas  {d['mb']:>8.0f} MB  {when}  "
                f"{registry.kind(p.name):<6} {r.get('purpose', '')}"
            )


def retire(
    name: str,
    role: str,
    keep: list[str],
    apply: bool,
    own: bool = False,
    drop_unsaved: bool = False,
) -> str:
    """Archive one project's config (plus any databank named) and remove it from its install.

    Args:
        name: Project name.
        role: "master", "conductor" or "custodian".
        keep: Databank names archived alongside the config, e.g. ["WFM"].
        apply: False only says what would happen.
        own: The caller built this project in the same job and is done with it (MT5
            Bridge's `Test_MT5Verify_…`): the FRESH_MINUTES wait, which protects someone
            else still collecting, is skipped. Every other refusal stands.
        drop_unsaved: The owner said to lose the step-8 survivors the store does not hold
            (owner, 2026-10-09: 1,352 near-clones took 3 h to save). Never set by a sweep.

    Returns:
        One line saying what was, or would be, done.
    """
    inst = installs()[role]
    folder = inst / "user/projects" / name
    if name in STOCK:
        raise SystemExit(f"{name} is a stock project; it is never retired.")
    if not (folder / "project.cfx").exists():
        raise SystemExit(f"{folder} holds no project.cfx.")
    if master_up() if role == "master" else cfxio.held(folder / "project.cfx"):
        raise SystemExit(
            f"the {role} is up: it holds {name} in memory and would write it "
            "back on exit (hard rule 4). Stop it first."
        )
    d = describe(folder)
    if d["tasks"] == "?":
        raise SystemExit(
            f"{name}: project.cfx unreadable, never retired (cannot tell what it is)."
        )
    if not own and time.time() - d["mtime"] < FRESH_MINUTES * 60:
        raise SystemExit(
            f"{name} changed less than {FRESH_MINUTES} min ago — someone may still "
            "be collecting from it. Check ListAgents and the day's log."
        )
    missing = [b for b in keep if not (folder / "databanks" / b).is_dir()]
    if missing:
        raise SystemExit(f"{name} has no databank {', '.join(missing)}.")
    lost = [] if drop_unsaved else save.unsaved(name)
    if lost:
        raise SystemExit(
            f"{name}: {len(lost)} supervivientes del paso 8 no están guardadas en el "
            f"almacén ({', '.join(lost[:3])}…): retirarlo borraría sus .sqx. Antes: "
            f"python3 -m core.store save {name} (o --drop-unsaved si el dueño las da por perdidas)"
        )
    out = first = retired_project(inst.name, name, date.today().isoformat())
    n = 1
    while out.exists():  # the same name retired twice in a day: the first archive stays
        n += 1
        out = first.with_name(first.name.replace(".tar.gz", f"_{n}.tar.gz"))
    line = f"{inst.name}/{name}: {d['tasks']} tareas, {d['mb']:.0f} MB → {out}"
    if not apply:
        return "would retire " + line
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w:gz") as tar:
        tar.add(folder / "project.cfx", arcname=f"{name}/project.cfx")
        for b in keep:
            tar.add(folder / "databanks" / b, arcname=f"{name}/databanks/{b}")
    shutil.rmtree(folder)
    registry.mark_retired(name, inst.name, str(out))
    return "retired " + line


def is_up(role: str) -> bool:
    """Whether one install is running now."""
    if role == "master":
        return master_up()
    return bool(
        cfxio.held(WORKERS[role]["path"] / "user/projects" / "_" / "project.cfx")
    )


def sweep_all(apply: bool, parked: Callable[[str], bool]) -> None:
    """Apply the weekly rule to every install and print one line per project looked at.

    Args:
        apply: Really retire; without it, a dry run.
        parked: Whether a project's workflow stopped between steps (`sweep.candidates`).
    """
    inst = installs()
    for row in sweep.candidates(
        inst, {r: is_up(r) for r in inst}, STOCK, describe, parked
    ):
        head = f"{row['role']:<9} {row['name']:<34} {row['tasks']:>3} tareas {row['mb']:>6} MB"
        if row["action"] == "keep":
            print(f"keep    {head}  {row['reason']}")
            continue
        if not apply:
            print(f"retire? {head}  {row['reason']}")
            continue
        try:
            retire(row["name"], row["role"], [], True)
            sweep.dequeue(row["role"], row["name"])
            print(f"retired {head}  {row['reason']}")
        except SystemExit as e:
            print(f"FAILED  {head}  {e}")


def main() -> None:
    """List custom projects, or retire the named ones (dry run unless --yes)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="projects to retire")
    ap.add_argument(
        "--list", action="store_true", help="every custom project, per install"
    )
    ap.add_argument("--role", choices=sorted(installs()), default="custodian")
    ap.add_argument(
        "--keep",
        action="append",
        default=[],
        help="a databank to archive with the config, e.g. --keep WFM; repeatable",
    )
    ap.add_argument(
        "--yes", action="store_true", help="really do it; without it, a dry run"
    )
    ap.add_argument(
        "--own",
        action="store_true",
        help="the caller built it in this same job: skip the 60-min freshness wait",
    )
    ap.add_argument(
        "--drop-unsaved",
        action="store_true",
        help="retire although step-8 survivors are not in the store: their .sqx are lost",
    )
    a = ap.parse_args()
    if a.list or not a.names:
        listing()
        return
    for n in a.names:
        print(retire(n, a.role, a.keep, a.yes, a.own, a.drop_unsaved))
    if not a.yes:
        print("dry run — add --yes to retire them")


if __name__ == "__main__":
    main()

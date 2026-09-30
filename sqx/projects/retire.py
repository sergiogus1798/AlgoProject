"""List the custom projects of every install, and retire the ones a finished run left behind."""

import argparse
import shutil
import tarfile
import time
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from core.datapaths import retired_project
from core.paths import MASTER, WORKERS
from sqx.projects import registry, sweep
from sqx.projects.configure import running_install

STOCK = {"Builder", "Retester", "Optimizer", "PortfolioComposer", "PortfolioMaster"}
FRESH_MINUTES = 60   # younger than this, someone may still be collecting from it


def installs() -> dict[str, Path]:
    """Role → install folder, the master included."""
    return {"master": MASTER, **{r: w["path"] for r, w in WORKERS.items()}}


def master_up() -> bool:
    """Whether any process runs from inside the master install (its GUI or a sqcli)."""
    needle = (str(MASTER) + "/").encode()
    for cmd in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            if needle in cmd.read_bytes():
                return True
        except OSError:
            continue
    return False


def describe(folder: Path) -> dict:
    """One project's task count, last change and size on disk."""
    tasks = "?"
    try:
        with zipfile.ZipFile(folder / "project.cfx") as z:
            tasks = len(ElementTree.fromstring(z.read("config.xml")).find("Tasks"))
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError, TypeError):
        pass
    files = [p for p in folder.rglob("*") if p.is_file()]
    newest = max((p.stat().st_mtime for p in files), default=folder.stat().st_mtime)
    return {"tasks": tasks, "mtime": newest, "mb": sum(p.stat().st_size for p in files) / 1e6}


def listing() -> None:
    """Print every custom project, per install, with what the registry knows of it."""
    known = {(r["install"], r["name"]): r for r in registry.rows() if not r["retired"]}
    for role, inst in installs().items():
        projects = sorted(p for p in (inst / "user/projects").iterdir()
                          if p.is_dir() and p.name not in STOCK)
        print(f"== {role} ({inst.name}) — {len(projects)} custom")
        for p in projects:
            d, r = describe(p), known.get((inst.name, p.name), {})
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(d["mtime"]))
            print(f"  {p.name:<34} {d['tasks']:>3} tareas  {d['mb']:>8.0f} MB  {when}  "
                  f"{registry.kind(p.name):<6} {r.get('purpose', '')}")


def retire(name: str, role: str, keep: list[str], apply: bool, own: bool = False) -> str:
    """Archive one project's config (plus any databank named) and remove it from its install.

    Args:
        name: Project name.
        role: "master", "conductor" or "custodian".
        keep: Databank names archived alongside the config, e.g. ["WFM"].
        apply: False only says what would happen.
        own: The caller built this project in the same job and is done with it (MT5
            Bridge's `Test_MT5Verify_…`): the FRESH_MINUTES wait, which protects someone
            else still collecting, is skipped. Every other refusal stands.

    Returns:
        One line saying what was, or would be, done.
    """
    inst = installs()[role]
    folder = inst / "user/projects" / name
    if name in STOCK:
        raise SystemExit(f"{name} is a stock project; it is never retired.")
    if not (folder / "project.cfx").exists():
        raise SystemExit(f"{folder} holds no project.cfx.")
    if (master_up() if role == "master" else running_install(folder / "project.cfx")):
        raise SystemExit(f"the {role} is up: it holds {name} in memory and would write it "
                         "back on exit (hard rule 4). Stop it first.")
    d = describe(folder)
    if not own and time.time() - d["mtime"] < FRESH_MINUTES * 60:
        raise SystemExit(f"{name} changed less than {FRESH_MINUTES} min ago — someone may still "
                         "be collecting from it. Check ListAgents and the day's log.")
    missing = [b for b in keep if not (folder / "databanks" / b).is_dir()]
    if missing:
        raise SystemExit(f"{name} has no databank {', '.join(missing)}.")
    out = retired_project(inst.name, name, date.today().isoformat())
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
    return bool(running_install(WORKERS[role]["path"] / "user/projects" / "_" / "project.cfx"))


def sweep_all(apply: bool) -> None:
    """Apply the weekly rule to every install and print one line per project looked at."""
    inst = installs()
    for row in sweep.candidates(inst, {r: is_up(r) for r in inst}, STOCK, describe):
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
    ap.add_argument("--list", action="store_true", help="every custom project, per install")
    ap.add_argument("--role", choices=sorted(installs()), default="custodian")
    ap.add_argument("--keep", action="append", default=[],
                    help="a databank to archive with the config, e.g. --keep WFM; repeatable")
    ap.add_argument("--sweep", action="store_true",
                    help="the weekly rule: Test_, fewer than 10 tasks, the owner's queue")
    ap.add_argument("--yes", action="store_true", help="really do it; without it, a dry run")
    ap.add_argument("--own", action="store_true",
                    help="the caller built it in this same job: skip the 60-min freshness wait")
    a = ap.parse_args()
    if a.sweep:
        sweep_all(a.yes)
        return
    if a.list or not a.names:
        listing()
        return
    for n in a.names:
        print(retire(n, a.role, a.keep, a.yes, a.own))
    if not a.yes:
        print("dry run — add --yes to retire them")


if __name__ == "__main__":
    main()

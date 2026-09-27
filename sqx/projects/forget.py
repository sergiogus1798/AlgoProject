"""Erase one named project everywhere: its live SQX project and every AlgoData folder it filled."""

import argparse
import shutil
from pathlib import Path

from core.paths import DATA
from sqx.projects import retire

# The top-level AlgoData trees that nest a subfolder per project name. Shared or reference
# data (bars, barsDerived, spread, templates, ledger, projectsBackup, cache, snapshots, logs,
# profiling, notes, pipeline) is never named here and forget() never touches it.
PROJECT_DIRS = ("crosstf", "harvest", "metrics", "reports", "structural",
                "strategyPermutations", "atrCalculator", "raw")


def _folder_size(p: Path) -> float:
    """A folder's total size in MB."""
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6


def find(name: str) -> dict:
    """Where a project's traces are: its live install (conductor/custodian only) and its
    AlgoData folders.

    Args:
        name: Project name.

    Returns:
        `{"role": str | None, "folders": [(Path, mb), ...], "mb": float}`. `role` is None
        when no conductor or custodian holds it live.
    """
    role = next((r for r, inst in retire.installs().items()
                if r != "master" and (inst / "user/projects" / name / "project.cfx").exists()),
                None)
    folders = [(DATA / d / name, _folder_size(DATA / d / name))
              for d in PROJECT_DIRS if (DATA / d / name).is_dir()]
    return {"role": role, "folders": folders, "mb": sum(mb for _, mb in folders)}


def forget(name: str, apply: bool) -> list[str]:
    """Retire the live project, if any, and delete its AlgoData folders.

    Args:
        name: Project name. A project only on the master is left alone — that install is the
            owner's (hard rule 3) and this never touches it.
        apply: False only says what would happen.

    Returns:
        One line per thing done or that would be done.
    """
    if name in retire.STOCK:
        raise SystemExit(f"{name} is a stock project; it is never retired or purged.")
    found = find(name)
    if found["role"] is None and not found["folders"]:
        master_has_it = (retire.installs()["master"] / "user/projects" / name).is_dir()
        if master_has_it:
            raise SystemExit(f"{name} only exists on the master — that install is the owner's "
                             "(hard rule 3); nothing was touched. Ask him if it should go.")
        raise SystemExit(f"no trace of {name} on conductor, custodian or in AlgoData.")
    lines = []
    if found["role"]:
        lines.append(retire.retire(name, found["role"], [], apply))
    for folder, mb in found["folders"]:
        lines.append(f"{'delete' if apply else 'would delete'} {folder} ({mb:.0f} MB)")
        if apply:
            shutil.rmtree(folder)
    return lines


def main() -> None:
    """Show, or with --yes actually erase, everything a named project left behind."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("name", help="the project to forget")
    ap.add_argument("--yes", action="store_true", help="really do it; without it, a dry run")
    a = ap.parse_args()
    for line in forget(a.name, a.yes):
        print(line)
    if not a.yes:
        print("dry run — add --yes to actually erase it")


if __name__ == "__main__":
    main()

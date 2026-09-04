#!/usr/bin/env python3
"""Heal a project.cfx that declares task files its archive lacks, grafting them from a donor."""

import argparse
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.paths import DATA, MASTER, project_dir

TASK_REF = re.compile(r'taskXMLFile="([^"]+)"')
PROC = Path("/proc")


def holding(install: Path) -> list[int]:
    """PIDs of StrategyQuant processes running out of one install.

    Args:
        install: Top-level SQX folder.

    Returns:
        Every PID whose command line names that folder. Writing to user/projects while
        one of these is alive is silently undone: SQX rewrites the file on save and exit.
    """
    found = []
    for d in PROC.iterdir():
        if not d.name.isdigit():
            continue
        cmdline = d / "cmdline"
        if cmdline.exists() and str(install) in cmdline.read_bytes().decode("utf-8", "replace"):
            found.append(int(d.name))
    return found


def missing(cfx: Path) -> list[str]:
    """Task files a project declares but its archive does not hold.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        Member names, in declaration order. Any of these makes the GUI drop the project
        at load with no error — see knowhow/03-driving-sqx.md.
    """
    with zipfile.ZipFile(cfx) as z:
        return [t for t in TASK_REF.findall(z.read("config.xml").decode("utf-8", "replace"))
                if t not in z.namelist()]


def graft(cfx: Path, donor: Path, out: Path) -> list[str]:
    """Write a repaired archive: every live member, plus the absent ones from the donor.

    Args:
        cfx: The broken project.cfx.
        donor: An older archive still holding the lost task files.
        out: Where to write the repaired archive.

    Returns:
        The member names taken from the donor. The live config.xml and the live task
        files are kept as they are — the donor's are older, and on this project they
        carry the pre-rename name and a stale input databank.
    """
    wanted = missing(cfx)
    with zipfile.ZipFile(cfx) as live, zipfile.ZipFile(donor) as old, \
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as new:
        for name in live.namelist():
            new.writestr(name, live.read(name))
        for name in wanted:
            new.writestr(name, old.read(name))
    return wanted


def registered(cfx: Path) -> set[str]:
    """Databanks a project's config.xml declares.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        Databank names. A task writing into one that is absent here has nowhere to go.
    """
    with zipfile.ZipFile(cfx) as z:
        return set(re.findall(r'<Databank name="([^"]*)"',
                              z.read("config.xml").decode("utf-8", "replace")))


def unresolved(cfx: Path) -> list[tuple[str, str]]:
    """Input and output databanks the tasks name but the project does not register.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        (task file, databank) pairs. Empty is the healthy answer.
    """
    known = registered(cfx)
    out = []
    with zipfile.ZipFile(cfx) as z:
        for name in z.namelist():
            if name == "config.xml":
                continue
            text = z.read(name).decode("utf-8", "replace")
            for attrs in re.findall(r"<Databank ([^>]*)>", text):
                d = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
                value = d.get("value")
                if d.get("name") in ("Input", "Output") and value not in (None, "null", *known):
                    out.append((name, value))
    return out


def main() -> None:
    """Repair one project, after backing it up and refusing to run under a live SQX."""
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="project name on the master")
    ap.add_argument("--donor", default="project_backup.cfx", help="archive to graft from")
    ap.add_argument("--apply", action="store_true", help="write it; otherwise dry run")
    a = ap.parse_args()

    folder = project_dir(a.project)
    cfx, donor = folder / "project.cfx", folder / a.donor
    wanted = missing(cfx)
    print(f"{a.project}: {len(wanted)} task files missing — {', '.join(wanted) or 'none'}")
    if not wanted:
        return

    pids = holding(MASTER)
    if pids:
        sys.exit(f"SQX is running from {MASTER} (PID {', '.join(map(str, pids))}). "
                 f"Close it first: a write under a live instance is silently overwritten.")

    staged = folder / "project.repaired.cfx"
    print("took from the donor:", ", ".join(graft(cfx, donor, staged)))
    left, dangling = missing(staged), unresolved(staged)
    print(f"still missing: {left or 'none'}\nunregistered databanks: {dangling or 'none'}")
    if left or dangling:
        staged.unlink()
        sys.exit("repair rejected, nothing was changed")

    if not a.apply:
        staged.unlink()
        print("dry run — rerun with --apply to install it")
        return

    backup = DATA / "backups/projects" / a.project / datetime.now().strftime("%Y-%m-%d_%H%M")
    backup.mkdir(parents=True)
    shutil.copy2(cfx, backup / "project.cfx")
    staged.replace(cfx)
    print(f"repaired. Previous archive kept at {backup / 'project.cfx'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Report what is wrong with every project on an install: broken archives, drift, mojibake."""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.paths import MASTER

TASK_REF = re.compile(r'taskXMLFile="([^"]+)"')
VERSION = re.compile(r'version="([0-9]+\.[0-9]+)"')
# A field re-encoded UTF-8 as CP1252 always ends up carrying these.
MOJIBAKE = re.compile(r'[ÃÂ][\x80-\xbfŒ-ž–-™]')


def decode(text: str) -> str:
    """Undo however many UTF-8-as-CP1252 round trips a field went through.

    Args:
        text: A value read out of a project file.

    Returns:
        The original text. Windows-imported `.cfx` fields have been re-encoded up to
        seven times, so one pass is not enough.
    """
    while True:
        try:
            once = text.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text
        if once == text:
            return text
        text = once


def members(cfx: Path) -> tuple[list[str], list[str]]:
    """Task files a project declares against the ones its archive holds.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        (declared, missing). A project with anything missing is dropped by the GUI at
        load with no error at all — see knowhow/03-driving-sqx.md.
    """
    with zipfile.ZipFile(cfx) as z:
        declared = TASK_REF.findall(z.read("config.xml").decode("utf-8", "replace"))
        return declared, [t for t in declared if t not in z.namelist()]


def mojibake(cfx: Path) -> dict[str, str]:
    """Every mangled text field in a project, decoded.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        Attribute name to what the value originally said. These are leftovers from a
        project imported off Windows; they are metadata, not paths SQX resolves.
    """
    found = {}
    with zipfile.ZipFile(cfx) as z:
        for name in z.namelist():
            text = z.read(name).decode("utf-8", "replace")
            for attr, value in re.findall(r'(\w+)="([^"]*)"', text):
                if MOJIBAKE.search(value):
                    found[f"{name}:{attr}"] = decode(value)
    return found


def version_of(cfx: Path) -> str:
    """The build of SQX that last wrote a project.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        The version attribute of config.xml, e.g. "142.2399".
    """
    with zipfile.ZipFile(cfx) as z:
        return VERSION.search(z.read("config.xml").decode("utf-8", "replace")).group(1)


def report(install: Path) -> list[dict]:
    """One row per project, worst problem first.

    Args:
        install: Top-level SQX folder holding user/projects.

    Returns:
        Rows with the project's version, its missing task files and its mangled fields.
        The install's own build is taken as the newest version any project carries: SQX
        restamps a project to its own build every time it saves one.
    """
    rows = []
    for d in sorted((install / "user/projects").iterdir()):
        cfx = d / "project.cfx"
        if not cfx.exists():
            continue
        declared, missing = members(cfx)
        rows.append({"project": d.name, "version": version_of(cfx), "tasks": len(declared),
                     "missing": missing, "mojibake": mojibake(cfx),
                     "backup": (d / "project_backup.cfx").exists()})
    build = max(r["version"] for r in rows)
    for r in rows:
        r["stale"] = r["version"] != build
    return rows


def main() -> None:
    """Print the health table, or the whole thing as JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", type=Path, default=MASTER, help="default is the master")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rows = report(a.install)
    if a.json:
        print(json.dumps(rows, indent=2))
        return

    build = max(r["version"] for r in rows)
    print(f"{a.install} — newest project stamp {build}\n")
    print(f"{'project':34} {'version':9} {'tasks':>5} {'moji':>5}  state")
    for r in rows:
        state = "broken: missing " + ", ".join(r["missing"]) if r["missing"] else \
                "older than the install" if r["stale"] else "ok"
        if r["missing"] and r["backup"]:
            state += "  (project_backup.cfx present)"
        print(f"{r['project']:34} {r['version']:9} {r['tasks']:>5} "
              f"{len(r['mojibake']):>5}  {state}")
    mangled = {k: v for r in rows for k, v in r["mojibake"].items()}
    if mangled:
        print("\nMangled fields, decoded:")
        for k, v in sorted(set(mangled.items())):
            print(f"  {k} = {v}")


if __name__ == "__main__":
    main()

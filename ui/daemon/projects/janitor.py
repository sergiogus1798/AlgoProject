"""The weekly sweep, run from where the workflow rail can be read (`sqx` may not import `ui`)."""

import argparse
import sqlite3
import zipfile

import yaml

from sqx.projects import retire
from ui.daemon.workflow.api import workflow


def parked(project: str) -> bool:
    """Whether the workflow started (a step from 6 on is done) and step 21 is not; unreadable: True."""
    try:
        steps = {s["n"]: s["state"] for s in workflow(project)["steps"]}
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        IndexError,
        zipfile.BadZipFile,
        sqlite3.Error,
        yaml.YAMLError,
    ):  # a rail that cannot be read must never open the door to a retire
        return True
    ok = ("done", "sealed")
    return (
        any(st in ok for n, st in steps.items() if float(n) >= 6)
        and steps.get("21") not in ok
    )


def main() -> None:
    """The weekly rule over every install: dry run unless --yes."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yes", action="store_true", help="really retire; else a dry run")
    retire.sweep_all(ap.parse_args().yes, parked)


if __name__ == "__main__":
    main()

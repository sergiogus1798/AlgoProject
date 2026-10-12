"""Who created each custom SQX project, for what, and whether it has been retired."""

import csv
import fcntl
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

from core.assetdata import expected_sign
from core.datapaths import project_registry
from sqx.projects.rankings import describe

# Owner, 2026-09-26: `Test_` is a functional test that will be thrown away, `Trade_` a project
# meant to bear fruit; `Research_` (owner, 2026-10-03) is what the research queue builds, kept
# until the owner decides (sweep.py). The prefix is how a later session tells clutter from work.
KINDS = {"Test_": "test", "Trade_": "trade", "Research_": "research"}
NAME_OK = re.compile(r"^(Test|Trade|Research)_[A-Za-z0-9_]+$")
COLUMNS = ("name", "kind", "install", "created", "purpose", "symbol", "timeframe",
           "template", "workflow", "retired", "archive", "acceptance", "family")


def check_name(name: str) -> str | None:
    """Why a new project name is refused, or None when it is fine.

    Args:
        name: The name `sqx.projects.builder` was asked to create.

    Returns:
        A message for SystemExit, or None.
    """
    if NAME_OK.match(name):
        return None
    return (f"'{name}': a project name starts with Test_ (a functional test, thrown away "
            "afterwards), Trade_ (meant to bear real fruit) or Research_ (the research queue's), then letters, digits and "
            "underscores only — the HTTP API splits its command on whitespace.")


def check_family(family: str | None, simple: bool = True, name: str = "") -> str | None:
    """Why a Simple Strategy's idea family is refused, or None when it is one of the table's rows.
    With a template (`simple` False) a family is refused: the family is its archetype.
    A name that already has a row with an empty family may be recreated without one (store-resume,
    owner 2026-10-12, D7): such a project is judged as before.

    The valid values are the keys of `_expected_sign` in assets/_markets.yaml (owner, 2026-10-12);
    there is no default: a missing family is a question for the owner (rule 11).
    """
    valid = list(expected_sign())
    if not simple:
        return "--family es sólo de una Simple Strategy: con plantilla la familia es su arquetipo." if family else None
    if family in valid or (not family and any(r["name"] == name and not r.get("family") for r in rows())):
        return None
    return (f"una Simple Strategy lleva su familia de idea (--family), una de: {', '.join(valid)}. "
            f"Recibido: {family!r}. Sin valor por defecto: pregunta al dueño cuál es.")


def kind(name: str) -> str:
    """'test', 'trade', 'research' or 'legacy' (created before the prefixes existed)."""
    return next((k for p, k in KINDS.items() if name.startswith(p)), "legacy")


def rows() -> list[dict]:
    """Every row of the registry, oldest first; empty when nothing was registered yet."""
    path = project_registry()
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@contextmanager
def _locked() -> Iterator[None]:
    """Hold an exclusive lock on the registry for one read-modify-write.

    Two sessions registering at once would each rewrite the CSV from their own stale copy and
    lose the other's row; so every mutator reads `rows()` inside this lock, then `_write`s.
    """
    path = project_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_name(path.name + ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _write(all_rows: list[dict]) -> None:
    """Rewrite the whole registry beside itself and swap it in, so a crash keeps the old one.

    Call it only inside `_locked()`.
    """
    path = project_registry()
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows({c: r.get(c, "") for c in COLUMNS} for r in all_rows)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def record(done: dict, purpose: str, symbol: str, template: str, family: str = "") -> None:
    """Append the project `builder.build` just installed; a rebuild replaces its live row.

    Args:
        done: What `builder.build` returned.
        purpose: One sentence: what the project is for.
        symbol: Asset name.
        template: Path of the template it builds from.
        family: Idea family of a Simple Strategy (no template); empty for a template project.
    """
    row = {"name": done["project"], "kind": kind(done["project"]), "install": done["install"],
           "created": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
           "purpose": purpose, "symbol": symbol, "timeframe": done["timeframe"],
           "template": template, "workflow": "yes" if done.get("added") else "no",
           "acceptance": describe(done["acceptance"]), "family": family}
    with _locked():
        keep = [r for r in rows()
                if not (r["name"] == done["project"] and r["install"] == done["install"]
                        and not r["retired"])]
        keep.append(row)
        _write(keep)


def mark_retired(name: str, install: str, archive: str) -> None:
    """Stamp the live row of a project as retired, adding one if it was never registered.

    Args:
        name: Project name.
        install: Install folder name.
        archive: Path of the archive the project went to.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with _locked():
        all_rows = rows()
        live = [r for r in all_rows if r["name"] == name and r["install"] == install
                and not r["retired"]]
        if not live:
            live = [{"name": name, "kind": kind(name), "install": install,
                     "purpose": "(unregistered — created before the registry)"}]
            all_rows += live
        for r in live:
            r["retired"], r["archive"] = now, archive
        _write(all_rows)

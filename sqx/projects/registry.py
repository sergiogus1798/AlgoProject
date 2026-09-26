"""Who created each custom SQX project, for what, and whether it has been retired."""

import csv
import re
from datetime import datetime, timezone

from core.datapaths import project_registry

# Owner, 2026-09-26: `Test_` is a functional test that will be thrown away, `Trade_` a project
# meant to bear fruit. The prefix is how a later session tells clutter from work at a glance.
KINDS = {"Test_": "test", "Trade_": "trade"}
NAME_OK = re.compile(r"^(Test|Trade)_[A-Za-z0-9_]+$")
COLUMNS = ("name", "kind", "install", "created", "purpose", "symbol", "timeframe",
           "template", "workflow", "retired", "archive")


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
            "afterwards) or Trade_ (meant to bear real fruit), then letters, digits and "
            "underscores only — the HTTP API splits its command on whitespace.")


def kind(name: str) -> str:
    """'test', 'trade' or 'legacy' (created before the prefixes existed)."""
    return next((k for p, k in KINDS.items() if name.startswith(p)), "legacy")


def rows() -> list[dict]:
    """Every row of the registry, oldest first; empty when nothing was registered yet."""
    path = project_registry()
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write(all_rows: list[dict]) -> None:
    """Rewrite the whole registry; it is small, and a rewrite keeps the columns in order."""
    path = project_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows({c: r.get(c, "") for c in COLUMNS} for r in all_rows)


def record(done: dict, purpose: str, symbol: str, template: str) -> None:
    """Append the project `builder.build` just installed; a rebuild replaces its live row.

    Args:
        done: What `builder.build` returned.
        purpose: One sentence: what the project is for.
        symbol: Asset name.
        template: Path of the template it builds from.
    """
    keep = [r for r in rows()
            if not (r["name"] == done["project"] and r["install"] == done["install"]
                    and not r["retired"])]
    keep.append({"name": done["project"], "kind": kind(done["project"]),
                 "install": done["install"],
                 "created": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                 "purpose": purpose, "symbol": symbol, "timeframe": done["timeframe"],
                 "template": template, "workflow": "yes" if done.get("added") else "no"})
    _write(keep)


def mark_retired(name: str, install: str, archive: str) -> None:
    """Stamp the live row of a project as retired, adding one if it was never registered.

    Args:
        name: Project name.
        install: Install folder name.
        archive: Path of the archive the project went to.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
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

"""What the template library holds, read off disk into one answer per template."""

import csv
import json
from pathlib import Path

from core.datapaths import template_dir, template_registry, template_runs
from core.paths import MASTER, WORKERS
from sqx.templates.holes import reach, shape

DRAFTS = template_registry().parent / "drafts"
STATUSES = ("draft", "validated", "buildConfirmed", "archived")
VERDICTS = ("promising", "weak", "dead")


def rows(csv_path: Path) -> list[dict[str, str]]:
    """Every row of one of the library's CSVs.

    Args:
        csv_path: The registry or the runs file.

    Returns:
        One dict per row, empty when the file does not exist yet — a machine that has
        never authored a template has no CSV, and that is not an error.
    """
    if not csv_path.exists():
        return []
    return list(csv.DictReader(csv_path.open(encoding="utf-8")))


def folder(name: str) -> dict[str, object]:
    """What is actually on disk for one template, beside what the registry claims.

    Args:
        name: Template name as it appears in the registry.

    Returns:
        Whether the .sqx, the brief and deps/ are there, plus the manifest when it parses.
        The registry is a claim; this is the evidence, and the catalogue shows both so a
        row pointing at a folder nobody copied is visible instead of silent.
    """
    d = template_dir(name)
    manifest = d / "manifest.json"
    deps = d / "deps"
    return {"path": str(d),
            "exists": d.is_dir(),
            "sqx": (d / "template.sqx").exists(),
            "brief": (d / "brief.md").exists(),
            "deps": sorted(f.name for f in deps.iterdir()) if deps.is_dir() else [],
            "manifest": json.loads(manifest.read_text(encoding="utf-8"))
                        if manifest.exists() else None}


def catalogue() -> list[dict[str, object]]:
    """Every template, with its runs attached and its folder inspected.

    Returns:
        One dict per registry row, newest first by creation date, each carrying its own
        runs. Runs naming a template the registry does not hold are kept under that name
        with an empty registry half, because a run of a deleted template is a fact.
    """
    runs = rows(template_runs())
    by_template: dict[str, list[dict[str, str]]] = {}
    for r in runs:
        by_template.setdefault(r["template"], []).append(r)

    out = []
    seen = set()
    for row in rows(template_registry()):
        name = row["name"]
        seen.add(name)
        out.append({**row, "runs": sorted(by_template.get(name, []), key=lambda r: r["date"]),
                    "disk": folder(name), "orphan": False})
    for name, its in by_template.items():
        if name not in seen:
            out.append({"name": name, "status": "", "archetype": "", "created": "",
                        "runs": sorted(its, key=lambda r: r["date"]),
                        "disk": folder(name), "orphan": True})
    return sorted(out, key=lambda t: (t.get("created") or "", t["name"]), reverse=True)


def drafts() -> list[dict[str, object]]:
    """Briefs the interview composed that nobody has authored into a template yet.

    Returns:
        One dict per draft file, newest first. A draft is not in the registry: it has no
        .sqx, and counting it as a template would inflate the coverage matrix with ideas.
    """
    if not DRAFTS.is_dir():
        return []
    return sorted((json.loads(f.read_text(encoding="utf-8")) | {"draft_file": str(f)}
                   for f in DRAFTS.glob("*.json")),
                  key=lambda d: d.get("created", ""), reverse=True)


def one(name: str) -> dict[str, object]:
    """One template's whole record, including the brief as text.

    Args:
        name: Template name as it appears in the registry.

    Returns:
        The catalogue entry plus `brief_md`, the Spanish brief read verbatim so the panel
        renders what the author wrote rather than a summary of it, and `holes` / `fixed` /
        `reach` — which parts the builder fills freely, which are bound to a group, and
        whether a block palette can narrow this template at all. They are flattened rather
        than nested under `shape` because the registry already has a `shape` column and a
        second meaning for that name would overwrite it.
    """
    entry = next(t for t in catalogue() if t["name"] == name)
    brief = template_dir(name) / "brief.md"
    sqx = template_dir(name) / "template.sqx"
    # The groups a hole names live where the template's blocks were installed: both workers,
    # and builds run on the custodian. Read against the master, every bound hole of a template
    # authored after 2026-09-22 said «un grupo que esta instalación no tiene» (📓 2026-09-29).
    builds = WORKERS["custodian"]["path"] if "custodian" in WORKERS else MASTER
    form = shape(sqx, builds) if sqx.exists() else None
    return {**entry, "brief_md": brief.read_text(encoding="utf-8") if brief.exists() else "",
            "holes": form["holes"] if form else [], "fixed": form["fixed"] if form else [],
            "reach": reach(form) if form else ""}

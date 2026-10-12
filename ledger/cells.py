"""The per-cell counter: how much was tried in each asset x timeframe x direction x idea family.

Owner, 2026-10-12 (encargo 65 §5.1). The ledger's study (`study.py`) carries no direction; a cell
does. The builds are
read from the project registry, the step-8 judgements from `projects.csv` (one row per
project, upserted, so a re-run never double-counts); `table()` groups them into one row per cell
with the six integers, and `batches_screened` (B) is what the step-8 rule reads. A `Test_` project counts the same as a `Trade_`.
"""

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from collections import defaultdict

from core.paths import DATA, ROOT
from ledger import study as studymod
from studies.research.memory import sources

FOLDER = DATA / "ledger" / "cells"
PROJECTS = FOLDER / "projects.csv"
EXTRAS = FOLDER / "extras.json"    # per-cell integers nothing derives yet: oos2 looks
SEAL = FOLDER / "seal.json"            # {"sha256", "date"}: put once, by `--seal`, on every cell at once
JUDGEMENTS = FOLDER / "judgements.csv"  # append-only: project, date, sha256 of criteria.yaml at each step-8 judgement
CRITERIA = ROOT / "pipeline" / "autopilot" / "criteria.yaml"
FIELDS = ("project", "screened")
UNKNOWN = "unknown"


def key(symbol: str, timeframe: str, direction: str, family: str) -> str:
    """A cell's identity, e.g. `USATEC_H1_long_breakout`."""
    return "_".join((symbol, timeframe, direction or UNKNOWN, family or UNKNOWN))


def describe(row: dict, tpl: dict) -> dict:
    """symbol, timeframe, direction, family and template of a registry row.

    Direction: `simple:long` in the registry's template column, else the library template's `shape`
    (`market_long`). Family: the template's archetype, else the registry's `family`
    (the lookup `sources.family_of` does for one project). Anything unknown is 'unknown'.
    """
    path = row.get("template", "")
    name = sources.template_of(row)
    word = path.removeprefix("simple:") if path.startswith("simple:") else tpl.get(name, {}).get("shape", "")
    side = next((s for s in ("long", "short") if word.endswith(s)), UNKNOWN)
    family = tpl.get(name, {}).get("archetype", "") or row.get("family") or UNKNOWN
    return {"symbol": row.get("symbol", ""), "timeframe": row.get("timeframe", ""), "direction": side,
            "family": family, "template": name}


def built() -> dict[str, int]:
    """Strategies the build generated, by project: the `n_scored` of the step-6 rows
    `steprows.log_build` wrote (note `proyecto <name>`). Absent for a project that left none."""
    out: dict[str, int] = {}
    for sid in studymod.studies():
        frame = studymod.read(sid)
        for r in frame[frame["step"] == 6].itertuples() if len(frame) else ():
            if str(r.note).startswith("proyecto ") and r.n_scored == r.n_scored:
                out[str(r.note)[9:]] = int(r.n_scored)
    return out


def _judged() -> dict[str, dict]:
    """step-8 judgements by project."""
    return {r["project"]: r for r in sources.read_csv(PROJECTS)}


def _save(rows: dict[str, dict]) -> None:
    """Write `projects.csv`."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    with PROJECTS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows.values())


def note(project: str, screened: int) -> None:
    """Upsert one project's step-8 judgement (`judge.judge`): idempotent, a re-run replaces it."""
    _save(_judged() | {project: {"project": project, "screened": screened}})
    new = not JUDGEMENTS.exists()      # the same sha256 `judge.ledger_row` signs its ledger row with
    with JUDGEMENTS.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(("project", "date", "sha256"))
        w.writerow((project, _now(), hashlib.sha256(CRITERIA.read_bytes()).hexdigest()))


def _now() -> str:
    """UTC timestamp, ISO, second precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def seal() -> dict:
    """Put the first seal, once: the sha256 of `criteria.yaml` now, on every cell at once.

    Returns:
        The stored seal. Raises SystemExit when one exists: a second seal is the owner's call.
    """
    if SEAL.exists():
        sys.exit(f"{SEAL} ya existe: el sello se pone una vez")
    FOLDER.mkdir(parents=True, exist_ok=True)
    seal_ = {"sha256": hashlib.sha256(CRITERIA.read_bytes()).hexdigest(), "date": _now()}
    SEAL.write_text(json.dumps(seal_), encoding="utf-8")
    return seal_


def edits(cell: str) -> int | None:
    """Distinct `criteria.yaml` hashes, other than the sealed one, among the cell's step-8
    judgements dated after the seal. None before any seal exists."""
    return table()[cell]["edits_since_seal"] if cell in table() else None


def _edits() -> dict[str, set]:
    """Per project: the hashes (not the sealed one) of its judgements after the seal."""
    if not SEAL.exists():
        return {}
    sealed = json.loads(SEAL.read_text(encoding="utf-8"))
    out: dict[str, set] = defaultdict(set)
    for r in sources.read_csv(JUDGEMENTS):
        if r["date"] > sealed["date"] and r["sha256"] != sealed["sha256"]:
            out[r["project"]].add(r["sha256"])
    return out


def table() -> dict[str, dict]:
    """Cell key -> its six integers, plus `batches_screened` (the B of the step-8 rule).

    Builds (templates tried, batches built) are read from the project registry, which the builder
    writes: `sqx` may not import `ledger`, and one source cannot be counted twice. Step-8 judgements
    come from `projects.csv`.
    """
    extras = json.loads(EXTRAS.read_text(encoding="utf-8")) if EXTRAS.exists() else {}
    judged, tpl, made, changed = _judged(), sources.templates(), built(), _edits()
    sealed = SEAL.exists()
    hashes: dict[str, set] = defaultdict(set)
    cells: dict[str, dict] = defaultdict(lambda: {"templates": set(), "batches_built": 0, "generated": 0,
                                                  "screened": 0, "batches_screened": 0})
    for name, row in sources.registry_projects().items():
        d = describe(row, tpl)
        c = cells[key(d["symbol"], d["timeframe"], d["direction"], d["family"])]
        c["templates"] |= {d["template"]} - {""}
        c["batches_built"] += 1
        c["generated"] += made.get(name, 0)
        if name in judged:
            c["screened"] += int(judged[name]["screened"])
            c["batches_screened"] += 1
        hashes[key(d["symbol"], d["timeframe"], d["direction"], d["family"])] |= changed.get(name, set())
    return {k: {"templates_tried": len(c.pop("templates")), **c, "edits_since_seal": len(hashes[k]) if sealed else None,
                "oos2_looks": extras.get(k, {}).get("oos2", 0)} for k, c in cells.items()}


def batches_screened(cell: str) -> int:
    """B: the batches screened on oos1 in this cell; 0 for a cell never seen."""
    return table().get(cell, {}).get("batches_screened", 0)


def batches_for(project: str) -> int:
    """B for a project's own cell, counting this batch: the step-8 rule's `B`.

    A project already judged is in the count; one not yet judged adds itself, so the gate (before
    the judgement) and the judge (before `note`) read the same B, and a re-run reads it again.
    """
    row = sources.registry_projects().get(project)
    if row is None:
        return 1
    d = describe(row, sources.templates())
    return max(1, batches_screened(key(d["symbol"], d["timeframe"], d["direction"], d["family"]))
               + (project not in _judged()))


def look_oos2(project: str, max_looks: int) -> int:
    """Spend the project's single look at oos2 in its cell, once: a re-run of the same project adds none.

    Args:
        project: Project name, in the registry.
        max_looks: Looks a cell admits (3, owner 2026-10-12); the next is refused.

    Returns:
        The cell's looks, this one included. Raises PermissionError for a cell of unknown
        direction or family, or one already holding `max_looks` looks of other projects
        («solo vivo»: its medoids go on without being read). Written to `extras.json`.
    """
    d = describe(sources.registry_projects()[project], sources.templates())
    cell = key(d["symbol"], d["timeframe"], d["direction"], d["family"])
    if UNKNOWN in (d["direction"], d["family"]):
        raise PermissionError(f"celda {cell}: sin dirección o familia no hay celda a la que apuntar la mirada")
    extras = json.loads(EXTRAS.read_text(encoding="utf-8")) if EXTRAS.exists() else {}
    now, seen = extras.get(cell, {}).get("oos2", 0), extras.get(cell, {}).get("oos2_projects", [])
    if project not in seen:
        if now >= max_looks:
            raise PermissionError(f"celda {cell}: «solo vivo», ya tiene {now} miradas a oos2 "
                                  f"(máximo {max_looks}); no se lee")
        now, seen = now + 1, [*seen, project]
        extras[cell] = {**extras.get(cell, {}), "oos2": now, "oos2_projects": seen}
        FOLDER.mkdir(parents=True, exist_ok=True)
        EXTRAS.write_text(json.dumps(extras), encoding="utf-8")
    return now


def backfill() -> dict:
    """Rebuild `projects.csv` from each registered project's newest `gate/funnel.csv`. Run once.

    Returns:
        `projects` (registry), `judged`, `unknown_family`, `unknown_direction` (projects whose
        family or direction is unknown), `orphan_reports` (reports of a project the registry
        does not hold: skipped).
    """
    registry, tpl = sources.registry_projects(), sources.templates()
    rows, orphans = {}, 0
    for folder in sorted((DATA / "reports").glob("*/Results/*/gate")):    # by date: the newest run wins
        project = folder.parents[2].name
        funnel = sources.read_csv(folder / "funnel.csv")
        if project not in registry:
            orphans += 1
        elif funnel:
            rows[project] = {"project": project, "screened": funnel[0]["passed"]}
    _save(rows)
    seen = [describe(r, tpl) for r in registry.values()]
    made = built()
    return {"projects": len(registry), "judged": len(rows), "without_build_row": sum(n not in made for n in registry), "orphan_reports": orphans,
            "unknown_family": sum(d["family"] == UNKNOWN for d in seen),
            "unknown_direction": sum(d["direction"] == UNKNOWN for d in seen)}


if __name__ == "__main__":
    if "--seal" in sys.argv:
        print(seal())
        sys.exit()
    print(backfill())
    for k, c in sorted(table().items()):
        if c["batches_screened"] >= 2:
            print(k, c)

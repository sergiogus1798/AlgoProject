"""The per-cell counter: how much was tried in each asset x timeframe x direction x idea family.

Owner, 2026-10-12 (encargo 65 §5.1). The ledger's study (`study.py`) carries no direction; a cell
does. The builds are
read from the project registry, the step-8 judgements from `projects.csv` (one row per
project, upserted, so a re-run never double-counts); `table()` groups them into one row per cell
with the six integers, and `batches_screened` (B) is what the step-8 rule reads. `table()` counts a `Test_` like a `Trade_`; `ask()` reports them apart.
"""

import argparse
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from collections import defaultdict
from typing import Any

import pandas as pd

from core.datapaths import campaign_dir
from core.paths import DATA, ROOT
from core.fsio import atomic_write
from core.store.write import locked
from ledger import study as studymod
from studies.research.memory import sources

FOLDER = DATA / "ledger" / "cells"
PROJECTS = FOLDER / "projects.csv"
EXTRAS = FOLDER / "extras.json"  # per-cell integers nothing derives yet: oos2 looks
SEAL = (
    FOLDER / "seal.json"
)  # {"sha256", "date", "previous"}: `--seal`; again only by `--reseal` (the owner's call)
JUDGEMENTS = (
    FOLDER / "judgements.csv"
)  # append-only: project, date, sha256 of criteria.yaml at each step-8 judgement
CRITERIA = ROOT / "pipeline" / "autopilot" / "criteria.yaml"
FIELDS = ("project", "screened")
UNKNOWN = "unknown"


def key(symbol: str, timeframe: str, direction: str, family: str) -> str:
    """A cell's identity, e.g. `USATEC_H1_long_breakout`."""
    return "_".join((symbol, timeframe, direction or UNKNOWN, family or UNKNOWN))


def describe(row: dict, tpl: dict) -> dict[str, str]:
    """symbol, timeframe, direction, family and template of a registry row.

    Direction: `simple:long` in the registry's template column, else the library template's `shape`
    (`market_long`). Family: the template's archetype, else the registry's `family`
    (the lookup `sources.family_of` does for one project). Anything unknown is 'unknown'.
    """
    path = row.get("template", "")
    name = sources.template_of(row)
    word = (
        path.removeprefix("simple:")
        if path.startswith("simple:")
        else tpl.get(name, {}).get("shape", "")
    )
    side = next((s for s in ("long", "short") if word.endswith(s)), UNKNOWN)
    family = tpl.get(name, {}).get("archetype", "") or row.get("family") or UNKNOWN
    return {
        "symbol": row.get("symbol", ""),
        "timeframe": row.get("timeframe", ""),
        "direction": side,
        "family": family,
        "template": name,
    }


def built() -> dict[str, int]:
    """Strategies the build generated, by project: the `n_scored` of the step-6 rows
    `steprows.log_build` wrote (note `proyecto <name>`). Absent for a project that left none."""
    out: dict[str, int] = {}
    r: Any  # itertuples() rows are namedtuples, typed as plain tuples
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
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, FIELDS)
    w.writeheader()
    w.writerows(rows.values())
    atomic_write(
        PROJECTS, buf.getvalue().encode(), durable=True
    )  # a reader never sees it half-written


def note(project: str, screened: int) -> bool:
    """Upsert one project's step-8 judgement (`judge.judge`): `screened` never decreases, so a
    resume that re-judges the already-cut databank cannot understate the multiple-testing count.
    Every judgement is still dated and hashed in `judgements.csv`, the edits-since-seal audit.

    Returns:
        False when `screened` is below the project's recorded one: the cut bank judged again,
        which signs no second ledger row.
    """
    with locked(FOLDER):  # read-change-write: two processes at once lost an update
        rows = _judged()
        before = int(rows.get(project, {}).get("screened") or 0)
        _save(rows | {project: {"project": project, "screened": max(before, screened)}})
        new = (
            not JUDGEMENTS.exists()
        )  # the same sha256 `judge.ledger_row` signs its ledger row with
        with JUDGEMENTS.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(("project", "date", "sha256"))
            w.writerow(
                (project, _now(), hashlib.sha256(CRITERIA.read_bytes()).hexdigest())
            )
    return screened >= before


def _now() -> str:
    """UTC timestamp, ISO, second precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def seal(again: bool = False) -> dict[str, Any]:
    """Seal the sha256 of `criteria.yaml` now, on every cell at once.

    Args:
        again: Reseal over an existing seal (the owner's call: S1, 2026-10-16). The old
            seals are kept in `previous`; edits are counted from the newest one on.

    Returns:
        The stored seal. Raises SystemExit when one exists and `again` is not given.
    """
    old = json.loads(SEAL.read_text(encoding="utf-8")) if SEAL.exists() else None
    if old and not again:
        sys.exit(f"{SEAL} ya existe: un segundo sello es del dueño (`--reseal`)")
    FOLDER.mkdir(parents=True, exist_ok=True)
    seal_ = {
        "sha256": hashlib.sha256(CRITERIA.read_bytes()).hexdigest(),
        "date": _now(),
        "previous": [*old.pop("previous", []), old] if old else [],
    }
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
    cells: dict[str, dict] = defaultdict(
        lambda: {
            "templates": set(),
            "batches_built": 0,
            "generated": 0,
            "screened": 0,
            "batches_screened": 0,
        }
    )
    for name, row in sources.registry_projects().items():
        d = describe(row, tpl)
        c = cells[key(d["symbol"], d["timeframe"], d["direction"], d["family"])]
        c["templates"] |= {d["template"]} - {""}
        c["batches_built"] += 1
        c["generated"] += made.get(name, 0)
        if name in judged:
            c["screened"] += int(judged[name]["screened"])
            c["batches_screened"] += 1
        hashes[key(d["symbol"], d["timeframe"], d["direction"], d["family"])] |= (
            changed.get(name, set())
        )
    return {
        k: {
            "templates_tried": len(c.pop("templates")),
            **c,
            "edits_since_seal": len(hashes[k]) if sealed else None,
            "oos2_looks": extras.get(k, {}).get("oos2", 0),
        }
        for k, c in cells.items()
    }


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
    return max(
        1,
        batches_screened(key(d["symbol"], d["timeframe"], d["direction"], d["family"]))
        + (project not in _judged()),
    )


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
        raise PermissionError(
            f"celda {cell}: sin dirección o familia no hay celda a la que apuntar la mirada"
        )
    with locked(FOLDER):  # read-change-write: two processes at once lost a look
        extras = (
            json.loads(EXTRAS.read_text(encoding="utf-8")) if EXTRAS.exists() else {}
        )
        now, seen = (
            extras.get(cell, {}).get("oos2", 0),
            extras.get(cell, {}).get("oos2_projects", []),
        )
        if project not in seen:
            if now >= max_looks:
                raise PermissionError(
                    f"celda {cell}: «solo vivo», ya tiene {now} miradas a oos2 "
                    f"(máximo {max_looks}); no se lee"
                )
            now, seen = now + 1, [*seen, project]
            extras[cell] = {**extras.get(cell, {}), "oos2": now, "oos2_projects": seen}
            atomic_write(EXTRAS, json.dumps(extras).encode(), durable=True)
    return now


def backfill() -> dict[str, int]:
    """Rebuild `projects.csv` from each registered project's newest `gate/funnel.csv`. Run once.

    Returns:
        `projects` (registry), `judged`, `unknown_family`, `unknown_direction` (projects whose
        family or direction is unknown), `orphan_reports` (reports of a project the registry
        does not hold: skipped).
    """
    registry, tpl = sources.registry_projects(), sources.templates()
    rows, orphans = {}, 0
    for folder in sorted(
        (DATA / "reports").glob("*/Results/*/gate")
    ):  # by date: the newest run wins
        project = folder.parents[2].name
        funnel = sources.read_csv(folder / "funnel.csv")
        if project not in registry:
            orphans += 1
        elif funnel:
            rows[project] = {"project": project, "screened": funnel[0]["passed"]}
    _save(rows)
    seen = [describe(r, tpl) for r in registry.values()]
    made = built()
    return {
        "projects": len(registry),
        "judged": len(rows),
        "without_build_row": sum(n not in made for n in registry),
        "orphan_reports": orphans,
        "unknown_family": sum(d["family"] == UNKNOWN for d in seen),
        "unknown_direction": sum(d["direction"] == UNKNOWN for d in seen),
    }


def ask(
    symbol: str, timeframe: str, template: str = "", direction: str = ""
) -> dict[str, Any]:
    """Read-only: was this cell tried? The three registries, side by side (encargo 62, part 1).

    Owner, 2026-10-14: a `Test_` spends segments, not the cell; a price series is the whole symbol.
    A "screening" is a step-8 row on oos1 (one per `criteria.yaml` run); "rows" is every book row.

    Args:
        symbol: Asset, e.g. "USDJPY".
        timeframe: Grid, e.g. "M30".
        template: Library template; "" asks for the whole symbol x timeframe.
        direction: "long", "short" or "" for both.

    Returns:
        `projects` (kind -> names), `campaign` (state or None), `cell` and `series_tf` and `series`
        (segment -> rows, screenings, days, criteria), and `verdict`.
    """
    tpl = sources.templates()
    mine = {
        n: r
        for n, r in sources.registry_projects().items()
        if r["symbol"] == symbol and r["timeframe"] == timeframe
    }
    chosen = {
        n: r
        for n, r in mine.items()
        if (not template or describe(r, tpl)["template"] == template)
        and (not direction or describe(r, tpl)["direction"] == direction)
    }
    projects: dict[str, list[str]] = defaultdict(list)
    for n, r in chosen.items():
        projects[r.get("kind", "")].append(
            n + (" (retirado)" if r.get("retired") == "yes" else "")
        )
    camp_file = campaign_dir() / "ledger.jsonl"
    latest: dict[
        str, dict
    ] = {}  # a cell's lines merged oldest to newest, as the campaign does
    for line in (
        camp_file.read_text(encoding="utf-8").splitlines() if camp_file.exists() else []
    ):
        c = json.loads(line)
        k = "|".join(
            str(c.get(f)) for f in ("template", "symbol", "timeframe", "direction")
        )
        latest[k] = {**latest.get(k, {}), **c}
    camp = [
        c
        for c in latest.values()
        if c["symbol"] == symbol
        and c["timeframe"] == timeframe
        and (not template or c["template"] == template)
        and (not direction or c["direction"] == direction)
    ]
    frames = {
        s: studymod.read(s) for s in studymod.studies() if s.startswith(f"{symbol}_")
    }

    def spent(select: Any) -> dict[str, dict[str, int]]:
        """Rows, screenings, days and criteria per segment, over the studies `select` keeps."""
        out = {}
        for seg in ("build", "oos1", "oos2"):
            rows = [
                x
                for s, f in frames.items()
                if select(s)
                and len(x := f.loc[f["segment"] == seg, ["step", "ts", "criterion"]])
            ]
            f = (
                pd.concat(rows)
                if rows
                else pd.DataFrame(columns=pd.Index(["step", "ts", "criterion"]))
            )
            out[seg] = {
                "rows": len(f),
                "screenings": int((f["step"] == 8).sum()),
                "days": int(f["ts"].astype(str).str[:10].nunique()),
                "criteria": int(f["criterion"].nunique()),
            }
        return out

    tf = f"{symbol}_{timeframe}_"
    mine_ = f"{tf}{studymod.SAFE.sub('_', template).strip('_')}" if template else ""
    # ponytail: the book has no direction; without a template it is read off the study's suffix
    cell = spent(
        lambda s: (
            s == mine_
            if template
            else s.startswith(tf) and (not direction or s.lower().endswith(direction))
        )
    )
    n1, o2 = cell["oos1"]["screenings"], cell["oos2"]["rows"]
    verdict = (
        f"oos2 abierto ({o2} filas)"
        if o2
        else f"oos1 gastado {n1} veces"
        if n1
        else "construida, sin juzgar"
        if chosen or camp
        else "sin probar"
    )
    return {
        "projects": dict(projects),
        "campaign": [c.get("state") for c in camp],
        "cell": cell,
        "series_tf": spent(lambda s: s.startswith(tf)),
        "series": spent(lambda s: True),
        "verdict": verdict,
    }


if __name__ == "__main__":
    if "--ask" in sys.argv:
        ap = argparse.ArgumentParser(prog="ledger.cells --ask")
        ap.add_argument("--ask", action="store_true")
        ap.add_argument("symbol")
        ap.add_argument("timeframe")
        ap.add_argument("--template", default="")
        ap.add_argument("--direction", default="", choices=("", "long", "short"))
        ap.add_argument("--json", action="store_true")
        a = ap.parse_args()
        out = ask(a.symbol, a.timeframe, a.template, a.direction)
        print(
            json.dumps(out, ensure_ascii=False, indent=1)
            if a.json
            else "\n".join(f"{k}: {v}" for k, v in out.items())
        )
        sys.exit()
    if "--seal" in sys.argv or "--reseal" in sys.argv:
        print(seal(again="--reseal" in sys.argv))
        sys.exit()
    print(backfill())
    for k, c in sorted(table().items()):
        if c["batches_screened"] >= 2:
            print(k, c)

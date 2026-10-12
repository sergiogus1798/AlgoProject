"""Steps 17 to 20, blind: each look admitted and computed, the ledger rows of 17-19 written, then the joint reading."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from core.datapaths import variants_dir
from core.paths import DATA, report_dir
from ledger import blind as rebuilt
from ledger import gate, record, thresholds
from ledger import study as studymod
from pipeline.autopilot import call, survivors
from sqx.projects import stage
from ui.daemon import jobs
from ui.daemon.launch import chain, preflight


# The flag that adds a study's oos2 reading to the one that decides without it (18.5).
OOS2 = {"marketSurfaces": "--oos2"}
REFUSED = 3     # exit code of `studies.optimisation.oos2Reading.report` for a cell with no look left


def admit(project: str, n: str) -> None:
    """Ask the ledger's door before step `n` looks at oos2 (it raises only for an autonomous agent)."""
    gate.allow(float(n), "oos2", survivors.about(project)["symbol"])


def has(file: Path, flag: str | None) -> bool:
    """Whether a mother's result is there — with its oos2 reading, when a `flag` asks for one."""
    return file.exists() and (
        not flag or "oos2" in (json.loads(file.read_text(encoding="utf-8")).get("facts") or {}))


def skipped(project: str, mother: str) -> str | None:
    """Why 18.5 does not run for `mother`: the repricer must reproduce SQX (encargo 65 row 8).

    Returns:
        None when step 17's `wfc.json` gives `descuadre_sqx` (largest over c1-c3) strictly under
        `wfc.sqx_gap_relative`; otherwise the Spanish line saying why, a missing figure included.
    """
    file = variants_dir(project, mother) / "estudios" / "wfc.json"
    facts = json.loads(file.read_text(encoding="utf-8")).get("facts") or {} if file.exists() else {}
    gaps = [c["descuadre_sqx"] for c in facts.values() if c.get("descuadre_sqx") is not None]
    limit = thresholds.value("wfc.sqx_gap_relative")
    if gaps and max(gaps) < limit:
        return None
    what = f"descuadre con SQX {max(gaps):.2f} ≥ {limit}".replace(".", ",") if gaps else "sin descuadre con SQX (falta wfc.json)"
    return f"18.5 saltado en {mother}: {what} — el repreciador no reproduce a SQX en esta madre"


def look(project: str, n: str, key: str, mothers: pd.DataFrame, redo: bool,
         oos2: bool = True) -> str:
    """One of 17, 18, 18.5 over every mother's variant batch, computed and not read.

    Args:
        project: Project name.
        n: The step.
        key: Its study: wfc, cscv or marketSurfaces.
        mothers: `survivors.mothers`.
        redo: The batches are new (16.5 ran in this run): every mother again. Otherwise a
            mother that has the study's result is skipped — each run is a look the ledger counts.
        oos2: False for 18.5's deciding reading, run before the block: build and oos1 only,
            so the door is not asked and the study runs without its `OOS2` flag.

    Returns:
        How many mothers were read and how many already were. The study signs its own
        ledger rows (`engines.variants.look`); none of its numbers is printed here.
    """
    flag = OOS2.get(key) if oos2 else None
    if oos2:
        admit(project, n)
    todo = [m for m in mothers["strategy"]
            if redo or not has(variants_dir(project, m) / "estudios" / f"{key}.json", flag)]
    skip = [skipped(project, m) for m in todo] if key == "marketSurfaces" else []
    todo, lines = [m for m, why in zip(todo, skip or [None] * len(todo)) if not why], [w for w in skip if w]
    who = survivors.about(project)
    # The mothers at once, by the window's own width rule (`chain.python_step`): each writes
    # its own <work>/estudios and the ledger takes concurrent appends (18.5: 570 s in a row).
    # ponytail: no RAM floor (a mother's study is ~13 MB of input); `chain.floored` if one grows.
    width = 1 if key in jobs.WIDE else max(1, jobs.SLOTS // jobs.LIGHT)
    with ThreadPoolExecutor(width) as pool:
        list(pool.map(call.run, [argv + [flag] * bool(flag) for argv in
                                 call.window(key, project, "", who["symbol"], todo)] if todo else []))
    how = "a ciegas" if oos2 else "sin oos2 (la lectura que decide)"
    return "\n".join([f"{key}: {len(todo)} madre(s) leídas {how}, "
                      f"{len(mothers) - len(todo) - len(lines)} ya lo estaban", *lines])


def bank(project: str) -> str:
    """The databank the project's WFM task writes, as its project.cfx names it."""
    return next(t["output"] for t in preflight.tasks(project)["tasks"]
                if t["title"] in stage.titles("wfm"))


def wfm(project: str, role: str) -> str:
    """Step 19's reading, computed from the matrix SQX just ran and not read.

    The export is the worker stop's own (`loader.afterrun`); it is made here only when the
    databank has none at all (a stop with `ALGO_NO_EXPORT`).
    """
    name = bank(project)
    if not list((DATA / "raw" / project / name.replace(" ", "_")).glob("*/wfm/manifest.json")):
        call.run(["-m", "sqx.export.export_wfm", "--project", project, "--databank", name,
                  "--role", role])
    call.run(["-m", "studies.optimisation.wfm.report", "--project", project, "--databank", name])
    return f"lectura de {name} escrita, sin leer"


def study(project: str) -> tuple[str, dict]:
    """The ledger study the block signs — the one blindJoint reads — and its rows' shared fields."""
    who = survivors.about(project)
    sid = studymod.study_id(who["symbol"], who["timeframe"], who["family"])
    return sid, {"study": sid, "symbol": who["symbol"], "timeframe": who["timeframe"],
                 "config_hash": None}


def register(project: str, mothers: pd.DataFrame) -> str:
    """Write the ledger rows 17, 18 and 19 still lack, then ask the blind door.

    Args:
        project: Project name.
        mothers: `survivors.mothers`.

    Returns:
        How many rows were written, per step.

    Raises:
        PermissionError: Under `gate.enforced()`, when one of 17, 18, 19 still has no row.

    What `ledger.backfill --blind --write` does, with two differences that command cannot
    make: only this run's mothers, and the WFM row is owed per PROJECT — the study is asset,
    timeframe and family, so a second project of the same study finds step 19 «already
    written» and `backfill` refuses, leaving its own look at oos2 uncounted. A WFM reading
    is registered once: its row's note names its folder.
    """
    sid, base = study(project)
    frame = studymod.read(sid)
    rows = [r for m in mothers["strategy"]
            for r in rebuilt.from_batch(variants_dir(project, m), base, frame)]
    read = sorted(report_dir(project, bank(project), "x").parent.glob("*/wfm/verdict.csv"))
    notes = frame.loc[frame["step"] == 19, "note"].fillna("").astype(str)
    if read and not notes.str.contains(str(read[-1].parent), regex=False).any():
        rows += rebuilt.from_wfm(read[-1].parent, base)
    for row in rows:
        record.log(sid, row)
    gate.allow_read(studymod.read(sid))
    written = pd.Series([r["step"] for r in rows]).value_counts().sort_index()
    return ("filas escritas: " + ", ".join(f"paso {s:g}: {n}" for s, n in written.items())
            if rows else "17, 18 y 19 ya tenían sus filas")


def oos2read(project: str) -> str:
    """Step 19.5: the single reading of oos2 over every mother's batch (one look in the project's cell).

    Exit 3 is the ledger refusing a fourth look («solo vivo»): the step goes on, writes no
    fact, and `criteria.yaml` reads a missing fact as limbo, so nobody is cut on it.
    """
    rc, text = chain.command(["-m", "studies.optimisation.oos2Reading.report", "--project", project])
    if rc == REFUSED:
        return "celda «solo vivo»: no se lee oos2, las madres siguen en limbo"
    if rc:
        raise SystemExit(f"oos2Reading: {text}")
    return "oos2Reading sobre los lotes de las madres"


def joint(project: str) -> str:
    """Step 20: the four pieces read at once — through the blind door, never around it."""
    sid, _ = study(project)
    gate.allow_read(studymod.read(sid))
    who = survivors.about(project)
    for argv in call.window("blindJoint", project, "", who["symbol"], []):
        call.run(argv)
    return f"blindJoint sobre el estudio {sid}"

"""Steps 17 to 20, blind: each look admitted and computed, the ledger rows of 17-19 written, then the joint reading."""

from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from core.datapaths import variants_dir
from core.paths import DATA, report_dir
from ledger import blind as rebuilt
from ledger import gate, record
from ledger import study as studymod
from pipeline.autopilot import call, survivors
from sqx.projects import stage
from ui.daemon import jobs
from ui.daemon.launch import preflight


def admit(project: str, n: str) -> None:
    """Ask the ledger's door before step `n` looks at oos2 (it raises only for an autonomous agent)."""
    gate.allow(float(n), "oos2", survivors.about(project)["symbol"])


def look(project: str, n: str, key: str, mothers: pd.DataFrame, redo: bool) -> str:
    """One of 17, 18, 18.5 over every mother's variant batch, computed and not read.

    Args:
        project: Project name.
        n: The step.
        key: Its study: wfc, cscv or marketSurfaces.
        mothers: `survivors.mothers`.
        redo: The batches are new (16.5 ran in this run): every mother again. Otherwise a
            mother that has the study's result is skipped — each run is a look the ledger counts.

    Returns:
        How many mothers were read and how many already were. The study signs its own
        ledger rows (`engines.variants.look`); none of its numbers is printed here.
    """
    admit(project, n)
    todo = [m for m in mothers["strategy"]
            if redo or not (variants_dir(project, m) / "estudios" / f"{key}.json").exists()]
    who = survivors.about(project)
    # The mothers at once, by the window's own width rule (`chain.python_step`): each writes
    # its own <work>/estudios and the ledger takes concurrent appends (18.5: 570 s in a row).
    # ponytail: no RAM floor (a mother's study is ~13 MB of input); `chain.floored` if one grows.
    width = 1 if key in jobs.WIDE else max(1, jobs.SLOTS // jobs.LIGHT)
    with ThreadPoolExecutor(width) as pool:
        list(pool.map(call.run, call.window(key, project, "", who["symbol"], todo) if todo else []))
    return f"{key}: {len(todo)} madre(s) leídas a ciegas, {len(mothers) - len(todo)} ya lo estaban"


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


def joint(project: str) -> str:
    """Step 20: the four pieces read at once — through the blind door, never around it."""
    sid, _ = study(project)
    gate.allow_read(studymod.read(sid))
    who = survivors.about(project)
    for argv in call.window("blindJoint", project, "", who["symbol"], []):
        call.run(argv)
    return f"blindJoint sobre el estudio {sid}"

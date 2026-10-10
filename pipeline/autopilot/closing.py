"""Steps 21 to 24 for every survivor: the two panel readings, the structural batch and the stop batch in SQX."""

import shutil
from pathlib import Path

import pandas as pd

from core.paths import DATA, project_dir
from core.study import identity
from ledger import gate
from pipeline.autopilot import call, survivors, variants
from sqx.curate import apply_verdict
from sqx.variants import legs as legmod
from ui.daemon.launch import run as launcher

# What step 23 reads of the three legs `execute` retests: build and oos1, never oos2.
STRUCTURE = ("build", "oos1")


def reading(project: str, key: str, databank: str, mothers: pd.DataFrame) -> str:
    """Step 21 or 22: one strategy study per mother, on the databank the owner named."""
    who = survivors.about(project)
    # A mother carries her last databank's name («…(1)» after a retest); the study reads the
    # panel databank's cosecha, which knows her by its own (📓 2026-10-05, step 22, IndexError).
    spelt = identity.spelt(project, databank, list(mothers["identity"]))
    names = [spelt.get(m.identity, m.strategy) for m in mothers.itertuples()]
    jobs = call.window(key, project, databank, who["symbol"], names)
    for argv in jobs:
        call.run(argv)
    return f"{key} sobre {databank}: {len(jobs)} madre(s)"


def copies(mothers: pd.DataFrame, folder: Path) -> Path:
    """The mothers' `.sqx` copied out of SQX, each under her name: what a batch is made from.

    The folder is emptied first: the factories take every `.sqx` in it as a mother.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.sqx"):
        old.unlink()
    for m in mothers.itertuples():
        shutil.copy2(m.file, folder / f"{m.strategy}.sqx")
    return folder


def wire(project: str, role: str, symbol: str) -> None:
    """The three WFC legs the only active tasks again (step 19 left the WFM on): hard rule
    5 first, then `variants.wire`, which honours hard rule 4 with a live session."""
    call.run(["-m", "core.assets", symbol])
    variants.wire(project, role)


def retest(project: str, role: str, work: Path) -> str:
    """One batch through the project's three legs: `sqx.variants.execute` starts the worker,
    runs them and stops it. The project is copied aside first (hard rule 1) and the copy
    goes only when no databank the legs do not write lost a file.
    """
    folder = project_dir(project, apply_verdict.install_of(role))
    kept, before = launcher.snapshot(folder), launcher.counts(folder)
    call.again(lambda: call.run(["-m", "sqx.variants.execute", "--work", str(work),
                                 "--project", project]))
    own = {leg["databank"] for leg in legmod.legs()} | {legmod.source()}
    return launcher.compare(before, launcher.counts(folder), own, kept)


def export(project: str, role: str, tag: str, banks: list[str]) -> None:
    """The legs' trades in one SQX start, tagged so 23 and 24 never overwrite each other."""
    call.run(["-m", "sqx.export.export_retest", "--project", project, "--role", role,
              "--batch", tag, *(x for b in banks for x in ("--databank", b))])


def clear(project: str) -> None:
    """Empty the batch's input and the three legs, worker stopped: the next batch loads clean."""
    call.run(["-m", "sqx.variants.execute", "--project", project, "--clear"])


def structural(project: str, role: str, mothers: pd.DataFrame, stamp: str) -> str:
    """Step 23: per mother an ablation per entry condition and the inversion, retested and read.

    Args:
        project: The workflow's own project (hard rule 10), holding the three WFC legs.
        role: Its worker.
        mothers: `survivors.mothers`.
        stamp: The autopilot run's folder name: the batch is `structural/<project>/<stamp>/`.

    Returns:
        The batch and what the retest did to the databanks.
    """
    who = survivors.about(project)
    for segment in STRUCTURE:
        gate.allow(23, segment, who["symbol"])
    root = DATA / "structural" / project
    held, work = copies(mothers, root / "mothers"), root / stamp
    banks = [leg["databank"] for leg in legmod.legs() if leg["segment"] in STRUCTURE]
    wire(project, role, who["symbol"])
    call.run(["-m", "sqx.structural.make", "--mothers", str(held), "--out", str(work)])
    said = retest(project, role, work)
    call.run(["-m", "sqx.structural.keep", "--work", str(work)])
    export(project, role, "structure", banks)
    call.run(["-m", "studies.readings.structure.report", "--work", str(work), "--project",
              project, "--databank", *banks, "--feed", who["feed"], "--symbol", who["symbol"]])
    clear(project)
    return f"{len(mothers)} madre(s) en {work}; {said}"


def stop(project: str, role: str, mothers: pd.DataFrame, stamp: str) -> str:
    """Step 24: X read from the MAE, then SQX's cost and stability around it — two passes.

    Args:
        project, role, mothers: As `structural`.
        stamp: The batch is `atrCalculator/<project>/<stamp>/pass1` and `pass2`.

    Returns:
        The batch and what each retest did to the databanks. Pass 1 retests the original and
        the X = 1000 probe and its report writes `stopgrid.csv`; pass 2 retests that grid. The
        study asks the door and signs one ledger row per segment, each pass: it reads oos2.
    """
    who = survivors.about(project)
    banks = [leg["databank"] for leg in legmod.legs()]
    for leg in legmod.legs():
        gate.allow(24, leg["segment"], who["symbol"])
    root = DATA / "atrCalculator" / project
    held, work = copies(mothers, root / "mothers"), root / stamp
    report = ["-m", "studies.closing.atrCalculator.report", "--project", project, "--databank",
              *banks, "--feed", who["feed"], "--symbol", who["symbol"], "--timeframe",
              who["timeframe"], *(["--family", who["family"]] if who["family"] else [])]
    grid = work / "pass1" / "estudios" / "atrCalculator" / "stopgrid.csv"
    wire(project, role, who["symbol"])
    said = []
    try:
        for batch, extra in ((work / "pass1", []), (work / "pass2", ["--grid", str(grid)])):
            call.run(["-m", "sqx.variants.stopgrid", "--mothers", str(held), "--out",
                      str(batch), *extra])
            said.append(retest(project, role, batch))
            export(project, role, "stopgrid", banks)
            call.run([*report, "--work", str(batch)])
            clear(project)
    except BaseException:
        # Pass 1's report alone makes the rail call step 24 done, and step 25 then died on the
        # missing pass 2 (🔬 2026-10-05): a half batch goes to the run's folder, out of the rail.
        if work.exists():
            shutil.move(work, DATA / "autopilot" / project / stamp / "paso-24-abortado")
        raise
    return f"{len(mothers)} madre(s) en {work}; " + "; ".join(said)

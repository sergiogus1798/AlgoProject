#!/usr/bin/env python3
"""Export every new or stale databank of an install's custom projects, right after it stops.

Owner, 2026-09-28: «si un test de SQX es runeado, inmediatamente cuando termine se exporten las
correspondientes estrategias y resultados al databank correspondiente» — for every run, the
window's and the skills'. Every SQX job ends in `bin/sqx-worker.sh stop`, which calls this once
the process is gone; the pieces and their commands are the loader's own (`state.commands`), run
one after another here instead of queued in the daemon. While it runs, `MARK` makes the loader
say «SQX is writing» for that install, so a window open at the time does not ask the same
`orderstocsv` twice.

    python3 -m ui.daemon.loader.afterrun --role custodian
"""

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from core.assetdata import doctrine
from core.paths import DATA, ROOT
from studies.breakage.mcRetest.inputs.tasks import DATABANK as MCR
from ui.daemon import progress, workerguard
from ui.daemon.loader import find, state

MARK = find.AFTERRUN                     # <role>.pid while this runs: the loader waits
OWN = ("Test_", "Trade_")                # hard rule 6: every custom project, never the stock ones
# The eight MC Retest databanks' trades: no study reads them (step 14 reads the MCR_All ingest
# and the build's harvest), and each cost a ~14 s orderstocsv JVM at every stop (📓 2026-10-01,
# 7 × 14 s of step 13's export). Owner, 2026-10-01: «deja de exportarlos innecesariamente».
# The window still exports them on demand when one is opened.
UNREAD_TRADES = set(MCR.values())


def skipped() -> set[str]:
    """The WFC batch and its three legs: `sqx.variants` harvests them itself (`equity`,
    `collect`) and empties them per mother, so every stop of a variant run re-exported
    thousands of variants on the conductor for nobody (📓 2026-09-30, minutes per stop)."""
    wfc = doctrine()["wfc"]
    return {wfc["input"], *(t["databank"] for t in wfc["tasks"])}


def banks(top: object, only: str | None = None) -> list[tuple[str, str]]:
    """(project, databank) of every custom project on the install with strategies on disk —
    or of `only` — but the variant batches' (`skipped`)."""
    root, off = top / "user" / "projects", skipped()
    return [(p.name, d.name) for p in sorted(root.iterdir()) if p.name.startswith(OWN)
            and (only is None or p.name == only)
            for d in sorted((p / "databanks").glob("*"))
            if d.is_dir() and d.name not in off and any(d.glob("*.sqx"))]


# The exports a step's analysis reads that are not the loader's pieces: without them the
# analysis ran on the last export a skill had made, or said «necesita el export» (📓
# 2026-09-29: the step-13 run of the window was never ingested, so step 14 read 09-27's).
# Name → (source databanks, export databank, what marks one export, argv after `-m`).
EXTRA = {
    # The marker is each export's manifest.json, which every export rewrites: a folder's date
    # does not move when a second export of the day overwrites its files, and the WFM was
    # re-exported (918k trades, ~8 min) at every stop for it (📓 2026-09-29).
    "ingesta MC Retest": (tuple(MCR.values()), "MCR_All", "*/manifest.json",
                          ["studies.breakage.mcRetest.ingest", "--databank", "MCR_All"]),
    "SPP IS": (("SPP IS",), "SPP_IS", "*/spp/manifest.json",
               ["sqx.export.export_spp", "--databank", "SPP IS"]),
    "SPP OOS": (("SPP OOS",), "SPP_OOS", "*/spp/manifest.json",
                ["sqx.export.export_spp", "--databank", "SPP OOS"]),
    "WFM": (("WFM",), "WFM", "*/wfm/manifest.json",
            ["sqx.export.export_wfm", "--databank", "WFM"]),
}


def extras(project: str, role: str, top: Path) -> list[tuple[str, list[str]]]:
    """The EXTRA exports this project needs: a source databank changed since its last one
    (`state.age`: by content, not by the dates SQX's resave moves).

    Returns:
        (name, argv) per stale export. The MC ingest is immutable per day, so a second one
        on the same day goes under `<day>-2`, `-3`… (the runner reads the last in name order).
    """
    out = []
    banks = top / "user" / "projects" / project / "databanks"
    for name, (sources, target, marker, argv) in EXTRA.items():
        files = [f for b in sources for f in (banks / b).glob("*.sqx")]
        if not files:
            continue
        root = DATA / "raw" / project / target
        done = sorted(root.glob(marker))
        if state.age(done[-1] if done else None, files) == "fresh":
            continue            # the same strategies, whatever SQX's resave did to the dates
        cmd = ["-m", *argv, "--project", project, "--role", role]
        if target == "MCR_All":
            day, n = date.today().isoformat(), 1
            while (root / (day if n == 1 else f"{day}-{n}") / "sims").exists():
                n += 1
            cmd += ["--day", day if n == 1 else f"{day}-{n}"]
        out.append((name, cmd))
    return out


def export(role: str) -> int:
    """Run what the loader would queue for each databank of the project that ran; return the
    failures. The launcher marks that project (`workerguard.mark`) and the mark outlives this
    export; a stop with no mark (a skill's own start) exports the whole install as before.
    🔬 2026-10-01: an autopilot stop spent 13 min re-exporting another session's 1,404-strategy
    project that nobody had run — owner: «qué coño estás exportando».
    """
    top = progress.installs()[role]
    ran = (workerguard.marked(role) or {}).get("project")
    failed = 0
    for project, databank in banks(top, ran):
        todo = state.commands(project, state.status(project, databank))
        for piece in ("metrics", "trades", "harvest"):       # the harvest reads the trades
            if piece not in todo or (piece == "trades" and databank in UNREAD_TRADES):
                continue
            print(f"exportando {piece} de {project} / {databank}", flush=True)
            got = subprocess.run([sys.executable, *todo[piece][1]], cwd=ROOT)
            failed += got.returncode != 0
    for project in sorted({p for p, _ in banks(top, ran)}):
        for name, cmd in extras(project, role, top):
            print(f"exportando {name} de {project}", flush=True)
            got = subprocess.run([sys.executable, *cmd], cwd=ROOT)
            failed += got.returncode != 0
    sign(top, ran)
    return failed


def sign(top: Path, ran: str | None = None) -> None:
    """Record, beside every export now up to date, what its strategies are (`state.age` writes
    the `.sources.sig` when it finds an export fresh). Without it the next stop found SQX's
    resave newer than the export and no signature to tell it was a resave: every stop
    re-exported the whole install (📓 2026-09-29, 8 min after a 6-min task)."""
    for project, databank in banks(top, ran):
        state.status(project, databank)
    for project in sorted({p for p, _ in banks(top, ran)}):
        extras(project, "", top)          # `age` signs each fresh EXTRA export; argv unused


def main() -> None:
    """Export after a stop; `ALGO_NO_EXPORT=1` skips it (a cancel that must end fast)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--role", required=True, help="el install que se acaba de parar")
    a = ap.parse_args()
    if os.environ.get("ALGO_NO_EXPORT") == "1" or a.role == "master":
        return
    if find.worker.holding(progress.installs()[a.role]):
        sys.exit(f"{a.role} sigue arrancado: no se exporta nada a medio escribir")
    MARK.mkdir(parents=True, exist_ok=True)
    mark = MARK / f"{a.role}.pid"
    mark.write_text(str(os.getpid()))
    try:
        failed = export(a.role)
    finally:
        mark.unlink(missing_ok=True)
    print(f"export tras la parada del {a.role}: " + (f"{failed} pieza(s) fallaron" if failed
                                                    else "todo al día"), flush=True)


if __name__ == "__main__":
    main()

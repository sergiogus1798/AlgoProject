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
import runpy
import sys
import traceback
from datetime import date
from pathlib import Path

from core.assetdata import doctrine
from core.paths import DATA, ROOT
from core.phases import phase
from studies.breakage.mcRetest.inputs.tasks import DATABANK as MCR
from sqx.projects import live
from sqx.projects.workflow import CROSSTF
from ui.daemon import progress
from sqx.worker import guard as workerguard
from ui.daemon.loader import find, state
from ui.daemon.loader.extrasdef import EXTRA, SMOKE_SHARE

MARK = find.AFTERRUN  # <role>.pid while this runs: the loader waits
OWN = (
    "Test_",
    "Trade_",
    "Research_",
)  # hard rule 6: every custom project, never the stock ones
# The eight MC Retest databanks' trades: no study reads them (step 14 reads the MCR_All ingest
# and the build's harvest), and each cost a ~14 s orderstocsv JVM at every stop (📓 2026-10-01,
# 7 × 14 s of step 13's export). Owner, 2026-10-01: «deja de exportarlos innecesariamente».
# The window still exports them on demand when one is opened. `CrossTF_Input` too (2026-10-13):
# Python fills it and no task backtests it there, so a scaled sibling's `.sqx` carries its
# mother's stored result and SQX's memory none -- its `.abk` never matched, and nothing reads it.
UNREAD_TRADES = set(MCR.values()) | {CROSSTF["input"]}


def skipped() -> set[str]:
    """The WFC batch and its three legs: `sqx.variants` harvests them itself (`equity`,
    `collect`) and empties them per mother, so every stop of a variant run re-exported
    thousands of variants on the conductor for nobody (📓 2026-09-30, minutes per stop)."""
    wfc = doctrine()["wfc"]
    return {wfc["input"], *(t["databank"] for t in wfc["tasks"])}


def banks(top: Path, only: str | None = None) -> list[tuple[str, str]]:
    """(project, databank) of every custom project on the install with strategies on disk —
    or of `only` — but the variant batches' (`skipped`)."""
    root, off = top / "user" / "projects", skipped()
    return [
        (p.name, d.name)
        for p in sorted(root.iterdir())
        if p.name.startswith(OWN) and (only is None or p.name == only)
        for d in sorted((p / "databanks").glob("*"))
        if d.is_dir() and d.name not in off and any(d.glob("*.sqx"))
    ]


def extras(
    project: str, role: str, top: Path, names: set[str] | None = None
) -> list[tuple[str, list[str]]]:
    """The EXTRA exports this project needs: a source databank changed since its last one
    (`state.age`: by content, not by the dates SQX's resave moves).

    Returns:
        (name, argv) per stale export; with `names`, only those reading one of those databanks.
        The MC ingest is immutable per day, so a second one
        on the same day goes under `<day>-2`, `-3`… (the runner reads the last in name order).
    """
    out = []
    banks = top / "user" / "projects" / project / "databanks"
    for name, (sources, target, marker, argv) in EXTRA.items():
        files = [f for b in sources for f in (banks / b).glob("*.sqx")]
        if not files or (names is not None and not {norm(b) for b in sources} & names):
            continue
        root = DATA / "raw" / project / target
        # By date, not by name: `<day>-10` sorts before `<day>-2`, and from the tenth ingest of a
        # day on the `-9` was read for ever and the ingest repeated at every step.
        done = max(root.glob(marker), key=lambda f: f.stat().st_mtime, default=None)
        if state.age(done, files) == "fresh":
            continue  # the same strategies, whatever SQX's resave did to the dates
        cmd = ["-m", *argv, "--project", project, "--role", role]
        if target == "MCR_All":
            day, n = date.today().isoformat(), 1
            while (root / (day if n == 1 else f"{day}-{n}") / "sims").exists():
                n += 1
            cmd += ["--day", day if n == 1 else f"{day}-{n}"]
            if (
                os.environ.get("ALGO_SMOKE") == "1"
            ):  # `autopilot --smoke`, a Test_ project
                cmd += ["--set", f"recon.systematic_share={SMOKE_SHARE}"]
        out.append((name, cmd))
    return out


def norm(name: str) -> str:
    """A databank's name in either spelling (`Retest Markets` / `Retest_Markets`)."""
    return name.replace(" ", "_")


def scope(
    top: Path, ran: str | None, names: set[str] | None
) -> dict[tuple[str, str], bool]:
    """(project, databank) to export, with whether all its pieces (True) or only its harvest.

    Without `names` every databank of the project (or install), as ever. With them -- the
    outputs and filled databanks of the step that just ran (`liverun.export`) -- those alone,
    plus the build whose retest one of them is: its harvest reads both, so it goes stale with
    the retest. Whatever else is stale stays stale, for the stop's export (`state.age` reads
    the files, and nothing here signs a databank it did not export).
    """
    every = banks(top, ran)
    if names is None:
        return {b: True for b in every}
    names = {norm(n) for n in names}
    mine = {b for b in every if norm(b[1]) in names}
    return {
        **{b: True for b in mine},
        **{
            b: False
            for b in every
            if b not in mine and (b[0], find.partner(top, *b)) in mine
        },
    }


def piece(argv: list[str]) -> int:
    """Run one loader command (`-m module args…`) in this process; its return code.

    One process for the whole export: ~50 interpreters each paid their imports and a cold
    fingerprint (`sqx.databank.fingerprint.SEEN`), which the pieces now share. A piece that raises or exits with
    a message is a failure, as its non-zero exit was.
    """
    mod, saved = argv[1], sys.argv
    sys.argv = [mod, *argv[2:]]
    try:
        runpy.run_module(mod, run_name="__main__", alter_sys=True)
        return 0
    except SystemExit as stop:
        if isinstance(stop.code, str):
            print(stop.code, file=sys.stderr, flush=True)
        return stop.code if isinstance(stop.code, int) else int(stop.code is not None)
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        sys.argv = saved


def export(role: str, only: str | None = None, names: set[str] | None = None) -> int:
    """Run what the loader would queue for each databank of the project that ran; return the
    failures. The launcher marks that project (`workerguard.mark`) and the mark outlives this
    export; a stop with no mark (a skill's own start) exports the whole install as before.
    🔬 2026-10-01: an autopilot stop spent 13 min re-exporting another session's 1,404-strategy
    project that nobody had run — owner: «qué coño estás exportando».

    Builds go first and a databank asks the loader again after its harvest: `harvest --exports`
    (asked whenever either side's trades are stale, so a step-scoped harvest carries the retest's
    too) writes the trade exports of both sides when it took them whole, and the trades piece that
    was stale a moment ago is not any more.
    """
    top = progress.installs()[role]
    names = names and {norm(n) for n in names}
    ran = only or (workerguard.marked(role) or {}).get("project")
    sel = scope(top, ran, names)
    failed = 0
    for project, databank in sorted(sel, key=lambda b: find.partner(top, *b) is None):

        def plan() -> dict[str, tuple[str, list[str]]]:
            """What this databank still needs, asked of the loader now."""
            full = sel[project, databank]  # noqa: B023 called this iteration
            todo = state.commands(
                project,
                state.status(project, databank),  # noqa: B023 called this iteration
                exports=databank not in UNREAD_TRADES,
            )  # noqa: B023 called this iteration
            return {
                k: v
                for k, v in todo.items()
                if (full or k == "harvest")  # noqa: B023 called this iteration
                and not (k == "trades" and databank in UNREAD_TRADES)
            }  # noqa: B023 called this iteration

        todo = plan()
        if "harvest" in todo:
            print(f"exportando harvest de {project} / {databank}", flush=True)
            with phase("export.harvest", f"{project}/{databank}"):
                failed += piece(todo["harvest"][1]) != 0
            todo = plan()  # its --exports may have made the trades fresh
            todo.pop("harvest", None)
        for kind in ("metrics", "trades"):
            if kind in todo:
                print(f"exportando {kind} de {project} / {databank}", flush=True)
                with phase(f"export.{kind}", f"{project}/{databank}"):
                    failed += piece(todo[kind][1]) != 0
    for project in sorted({p for p, f in sel if sel[p, f]}):
        for name, cmd in extras(project, role, top, names):
            print(f"exportando {name} de {project}", flush=True)
            with phase("export.extra", f"{project}/{name}"):
                failed += piece(cmd) != 0
    sign(top, ran, names)
    return failed


def sign(top: Path, ran: str | None = None, names: set[str] | None = None) -> None:
    """Record, beside every export now up to date, what its strategies are (`state.age` writes
    the `.sources.sig` when it finds an export fresh). Without it the next stop found SQX's
    resave newer than the export and no signature to tell it was a resave: every stop
    re-exported the whole install (📓 2026-09-29, 8 min after a 6-min task)."""
    names = names and {norm(n) for n in names}
    chosen = [b for b, full in scope(top, ran, names).items() if full]
    for project, databank in chosen:
        state.status(project, databank)
    for project in sorted({p for p, _ in chosen}):
        extras(
            project, "", top, names
        )  # `age` signs each fresh EXTRA export; argv unused


def main() -> None:
    """Export after a stop; `ALGO_NO_EXPORT=1` skips it (a cancel that must end fast). Exit 1
    when a piece failed."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--role", required=True, help="el install que se acaba de parar")
    ap.add_argument(
        "--live",
        action="store_true",
        help="sesión GUI arriba con sus databanks recién sincronizados (sqx.projects.live)",
    )
    ap.add_argument(
        "--project", help="solo este proyecto: el que acaba de correr en la sesión viva"
    )
    ap.add_argument(
        "--databank",
        action="append",
        help="solo este databank (repetible): las salidas del paso que acaba de correr",
    )
    a = ap.parse_args()
    if os.environ.get("ALGO_NO_EXPORT") == "1" or a.role == "master":
        return
    if find.worker.holding(progress.installs()[a.role]) and not (
        a.live and live.mine(a.role)
    ):
        sys.exit(f"{a.role} sigue arrancado: no se exporta nada a medio escribir")
    os.chdir(ROOT)  # the pieces ran with cwd=ROOT as subprocesses
    MARK.mkdir(parents=True, exist_ok=True)
    mark = MARK / f"{a.role}.pid"
    mark.write_text(str(os.getpid()))
    try:
        with phase("export"):
            failed = export(
                a.role, a.project, *([set(a.databank)] if a.databank else [])
            )
    finally:
        mark.unlink(missing_ok=True)
    print(
        f"export tras la parada del {a.role}: "
        + (f"{failed} pieza(s) fallaron" if failed else "todo al día"),
        flush=True,
    )
    if failed:  # `liverun.export` runs this with check=True: the step ends here, not on a study reading the old export
        sys.exit(1)


if __name__ == "__main__":
    main()

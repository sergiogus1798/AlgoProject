"""«Lanzar en SQX» on a GUI session already up: configure a copy, push it, run, mirror to disk, export — no restart."""

import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from core.datapaths import tmp_dir
from core.phases import phase
from core.paths import ROOT, bank_dir
from ledger import steprows
from sqx.export import membank
from sqx.projects import crosstfload, exiting, live, stage
from ui.daemon import progress
from ui.daemon.advance.run import say
from ui.daemon.launch import configure, preflight
from ui.daemon.launch import run as launcher
from ui.daemon.launch import steps as launchsteps
from ui.daemon.loader import afterrun, find, state
from ui.daemon.launch.run import assets, compare, counts, record, snapshot


# The tasks that run slow in a session hours old, and at their speed in one just opened
# (🔬 2026-10-05, same project, SQX's own task time: WFM 1,837 s aged, 1,275 s fresh, 1,222 s on
# the restart route; SPP IS 894 against 442). Reopening costs ~100 s. The cause is not known.
AGED = {*stage.titles("spp"), *stage.titles("wfm")}


def dump(role: str, project: str, banks: set[str] | None) -> dict[str, int]:
    """The `.abk` of every databank the step's export pieces call stale, and only those.

    Same freshness as the pieces themselves (`state.commands`): a stale harvest takes its build and
    its retest in "main"; a stale trades piece takes its bank in "all" when it carries
    cross-check markets (`find.cross_market`), else "main". One mode per bank file: the harvest
    never reads a cross-market bank (its retest is a single-market `OOS`), so no bank needs both.
    Names are SQX's own (`status()["databank"]`), what `membank.take` and the consumers use.
    """
    top, want = progress.installs()[role], {}
    for (p, db), full in afterrun.scope(top, project, banks).items():
        now = state.status(p, db)
        todo = state.commands(p, now, exports=db not in afterrun.UNREAD_TRADES)
        if "harvest" in todo:
            want[now["databank"]] = want[now["partner"]] = "main"
        if full and "trades" in todo and db not in afterrun.UNREAD_TRADES:
            want.setdefault(now["databank"], "all" if find.cross_market(find.files(top, p, now["databank"])) else "main")
    wrote = membank.run(role, project, want) if want else {}
    if want and not wrote:
        print(f"sin .abk de {sorted(want)}: la instalación no tiene su proyecto de herramientas o sus snippets sin compilar", flush=True)
    return wrote


def export(role: str, project: str, banks: set[str] | None = None) -> None:
    """The export a stop would run, on the files the sync just wrote (`afterrun --live`), of this
    project alone: unmarked, it read every project of the install at each step (🔬 2026-10-05,
    ~60 s a step and another session's databanks re-exported).

    Only after the step's «Project finished» and the forced sync (`dump` starts a task in the
    session). The trades go first, from the session's memory (`dump`: the AlgoBank snippet's
    `.abk`); the consumers take them, and a live session has no other route (orderstocsv is
    refused there), so a failure carries the reasons the consumers printed. The dump folder is
    removed whatever happens: it is RAM.

    `banks`: the databanks the step wrote or filled -- only those are exported (and the build
    whose retest one is, for the harvest). The project's other stale databanks wait for the
    session's close: a load-and-resave moves their fingerprint, and each step re-exported
    `Results` (10,000 strategies, ~155 s) that no task had touched (🔬 2026-10-12, 4 of 4 runs)."""
    why = []
    try:
        with phase("export.memoria"):
            wrote = dump(role, project, banks)
        print(f"operaciones desde memoria: {wrote or 'ninguna (orderstocsv)'}", flush=True)
        run = subprocess.Popen([sys.executable, "-m", "ui.daemon.loader.afterrun", "--role", role, "--live",
                                "--project", project, *[a for b in sorted(banks or ()) for a in ("--databank", b)]],
                               cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in run.stdout:
            print(line, end="", flush=True)
            if "no vale" in line:
                why.append(line.strip())
        if run.wait():
            raise SystemExit(f"{project}: la exportación falló (código {run.returncode})"
                             + (f"; .abk descartados: {' | '.join(why)}" if why else ""))
    finally:
        shutil.rmtree(bank_dir(project, role), ignore_errors=True)


def close(role: str, project: str, failed: dict | None = None) -> None:
    """End the session: this project's export, then the stop without the script's own, which
    unmarked read the whole install (🔬 2026-10-05: 229 s of a 243 s stop re-exporting another
    project's databanks).

    `failed`: the SQX action (`run.merged`'s, with its `steps`) the run died in — a cancel or
    a task past its deadline. Its memory is partial, so no sync and no export: the session is
    made to exit and killed by PID once the other projects saved (`exiting.stop`), and the
    action's output databanks are emptied on disk and the project log of that start set
    aside (`.descartado`), because the rail reads any file there, or today's «TASK FINISHED»
    in that log, as the step done, and a resume would skip it (owner, 2026-10-06: the step
    is run again).
    """
    if failed is None:
        try:
            live.sync(role, project)
            export(role, project)
        finally:
            live.stop(role, export=False)
        return
    was = signal.signal(signal.SIGTERM, signal.SIG_IGN)   # the loop's STOP hit this close half-way and
    try:                                                  # left outputs the rail took for a done step
        print(exiting.stop(role, project), flush=True)    # (🔬 2026-10-06); it waits on us instead
    finally:
        live.stop(role, export=False)                  # the script's own cleanup: lock, Xvfb
    held = preflight.tasks(project)
    titles = {t for s in failed["steps"] for t in launchsteps.of_step(s["n"], held["cfx"])["titles"]}
    for task in held["tasks"]:
        if task["title"] in titles:
            for f in (held["cfx"].parent / "databanks" / task["output"]).glob("*.sqx"):
                f.unlink()
    newest = max((held["cfx"].parent / "log").glob("global_log_*.log"), key=lambda f: f.stat().st_mtime,
                 default=None)      # no log yet: a ValueError here hid the real failure (📓 2026-10-11)
    if newest is None or newest.stat().st_mtime < failed["since"]:   # the step never started: that log is an earlier step's
        newest = None
    else:
        newest.rename(newest.with_suffix(".log.descartado"))
    print(f"vaciadas en disco las salidas del paso {failed['n']} y apartado {newest.name if newest else 'ningún log'}: se repetirá al reanudar", flush=True)
    signal.signal(signal.SIGTERM, was)


def execute(pre: dict, project: str) -> dict:
    """`run.execute` for a live session: same checks and records, SQX never stopped.

    Args:
        pre: What `preflight.check` returned, ok.
        project: Project name.

    Returns:
        The output databanks' counts before and after, by title: {title: (before, after)}.
    """
    role, chosen, held = pre["role"], pre["chosen"], pre["cfx"]
    titles = [t["title"] for t in chosen]
    say(2, f"comprobando {pre['row']['symbol']} (regla 5)")
    assets(pre["row"]["symbol"])
    with phase("sync", "antes"):
        live.sync(role, project)             # disk == memory before the copy and the counts
    if AGED & set(titles):
        with phase("reapertura"):            # disk == memory: the stop loses nothing
            live.stop(role, export=False)
            live.start(role)
    with phase("snapshot"):
        kept, before = snapshot(held.parent), counts(held.parent)
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmp:
        staged = Path(tmp) / "project.cfx"
        shutil.copy2(held, staged)
        for bank in pre.get("fill", []):         # writes the copy and the databank's folder
            say(9, f"llenando {bank}")
            with phase("fill", bank):
                print(crosstfload.fill(bank, project, role, staged), flush=True)
        off = configure.run({**pre, "cfx": staged, "databanks": held.parent / "databanks"}, say)   # after the fill
        titles = [t for t in titles if t not in off]
        if live.added(staged, held):
            # A project built before the CrossTF tasks were made at step 5: the fill added
            # tasks, which only a closed SQX takes (hard rule 4). Restart chain, then reopen.
            live.stop(role, export=False)
            try:
                return launcher.execute(pre, project)
            finally:
                live.start(role)
        titles += crosstfload.separate_titles(staged) if "CrossTF" in titles else []
        say(10, f"activando solo {', '.join(titles)}")
        stage.just(staged, titles)
        with phase("configure", "push"):
            config = live.push(role, project, staged, held)  # SQX rewrites `held` with the tasks
    for bank in pre.get("fill", []):
        with phase("fill", bank):
            print(f"{bank}: {live.load(role, project, bank)} en memoria", flush=True)
        before = counts(held.parent)
    say(60, f"{', '.join(titles)} lanzada(s)")
    began = time.time()
    with phase("sqx", " + ".join(titles)):
        live.run(role, project, config)      # returns on «Project finished» alone: `live.wait` raises on every abort line
    with phase("sync", "después"):
        live.sync(role, project, force={t["output"] for t in chosen if t["output"]})   # rewritten at one count
    outputs = {t["output"] for t in chosen}
    with phase("compare"):
        after = counts(held.parent)
        print(compare(before, after, outputs, kept), flush=True)
    for t in chosen:
        if t["type"] == preflight.BUILD:
            print(record(pre, project, after.get(t["output"], 0)), flush=True)
            print(steprows.log_build(project, held.parent / "log", began), flush=True)
    export(role, project, {b for b in outputs | set(pre.get("fill", [])) if b} or None)
    moved = {t["title"]: (before.get(t["output"], 0), after.get(t["output"], 0)) for t in chosen}
    say(100, " · ".join(f"«{t}»: {n0} → {n1}" for t, (n0, n1) in moved.items()))
    return moved

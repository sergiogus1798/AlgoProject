"""«Lanzar en SQX» on a GUI session already up: configure a copy, push it, run, mirror to disk, export — no restart."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from core.datapaths import tmp_dir
from core.paths import ROOT
from sqx.projects import crosstfload, live, stage
from ui.daemon.advance.run import say
from ui.daemon.launch import configure, preflight
from ui.daemon.launch import run as launcher
from ui.daemon.launch.run import assets, compare, counts, record, snapshot


def export(role: str) -> None:
    """The export a stop would run, on the files the sync just wrote (`afterrun --live`)."""
    subprocess.run([sys.executable, "-m", "ui.daemon.loader.afterrun", "--role", role, "--live"],
                   cwd=ROOT, check=True)


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
    live.sync(role, project)                 # disk == memory before the copy and the counts
    kept, before = snapshot(held.parent), counts(held.parent)
    with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmp:
        staged = Path(tmp) / "project.cfx"
        shutil.copy2(held, staged)
        off = configure.run({**pre, "cfx": staged}, say)
        titles = [t for t in titles if t not in off]
        for bank in pre.get("fill", []):         # writes the copy and the databank's folder
            say(9, f"llenando {bank}")
            print(crosstfload.fill(bank, project, role, staged), flush=True)
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
        config = live.push(role, project, staged, held)    # SQX rewrites `held` with the tasks
    for bank in pre.get("fill", []):
        print(f"{bank}: {live.load(role, project, bank)} en memoria", flush=True)
        before = counts(held.parent)
    say(60, f"{', '.join(titles)} lanzada(s)")
    end = live.run(role, project, config)
    if "Error" in end:
        sys.exit(f"SQX: {end}")
    live.sync(role, project)
    after = counts(held.parent)
    outputs = {t["output"] for t in chosen}
    print(compare(before, after, outputs, kept), flush=True)
    for t in chosen:
        if t["type"] == preflight.BUILD:
            print(record(pre, project, after.get(t["output"], 0)), flush=True)
    export(role)
    moved = {t["title"]: (before.get(t["output"], 0), after.get(t["output"], 0)) for t in chosen}
    say(100, " · ".join(f"«{t}»: {n0} → {n1}" for t, (n0, n1) in moved.items()))
    return moved

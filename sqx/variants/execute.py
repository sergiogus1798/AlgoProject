#!/usr/bin/env python3
"""Retest a fabricated batch on the custodian and read the IS/OOS panel back out."""

import argparse
import json
import math
import re
import sys
import time
import zipfile
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import worker
from core.paths import worker_dir
from core.phases import phase
from sqx.projects import live, loadwait
from sqx.variants import banks, inputs, legs as legmod, livexec

TESTED, IN_BANK = banks.TESTED, banks.IN_BANK      # `spp` reads TESTED from here
LOAD_S = 60         # s to wait for SQX's «Strategies loaded» line after `load`, plus PER_FILE_S per file (then it fails loudly)
PER_FILE_S = 0.05   # 10x the one timing taken (0.26 s for 50 files); not measured at 5,000-10,000: re-time on the custodian
STOCK = {"Builder", "Retester"}   # SQX's own projects: never a harness (hard rule 10)


def _call(command: str, cfg: dict) -> str:
    """One sqcli command against the install `cfg` (the `execute` block) names; its reply."""
    return worker.call(command, role=cfg["role"])


def awake(cfg: dict) -> bool:
    """Bring the install up if it is not already, and say whether this call did it.

    Args:
        cfg: The `execute` block of config.yaml.

    Returns:
        True when this call started it, so the caller knows to put it back. An install
        that was already awake is left awake, and is used only when its owner lock names
        this holder: SystemExit otherwise, before a `clear` or a `load` reaches a run that
        is another session's (hard rule 3).

        The port answers for about twenty seconds before the CLI does, replying
        `Error: CLI not ready.` in the meantime. That is normal and is polled through, not
        treated as a failure.
    """
    try:
        up = "not ready" not in _call("-project action=list", cfg)
    except OSError:
        up = False
    if up:
        held = worker.lock(worker_dir(cfg["role"])) or {"holder": "nadie: no hay OWNER"}
        if held["holder"] != worker.holder():
            raise SystemExit(
                f'el {cfg["role"]} ya está arriba y lo tiene «{held["holder"]}»; tú eres '
                f"«{worker.holder()}». No se le manda nada: espera a que termine o pregunta "
                "al owner (regla dura 3)")
        return False
    worker.start(cfg["role"])
    for _ in range(bound := max(1, math.ceil(cfg["ready_tries"] * cfg["poll_seconds"]))):   # polled every second
        time.sleep(1)
        if "not ready" not in _call("-project action=list", cfg):
            return True
    raise SystemExit(f'{cfg["role"]} no respondio tras {bound} s')


def load(folder: Path, cfg: dict) -> None:
    """Put the batch into the harness's input databank, and nothing else with it.

    Args:
        folder: Directory of fabricated `.sqx`.
        cfg: The `execute` block.

    Returns:
        Nothing. The input and every leg's output databank are cleared first so the count afterwards is the batch and
        not the batch plus whatever the last run left. Loading twice does NOT de-duplicate (`P00000(1)`).
    """
    source = legmod.source()
    for bank in [source] + [leg["databank"] for leg in legmod.legs()]:       # `clear` is synchronous (~10 ms, 🔬 2026-10-13)
        worker.checked(_call(command := f'-databank action=clear project={cfg["project"]} name={bank}', cfg), command)
    since = live.mark(cfg["role"])     # before the call: only a line written after it counts
    command = f'-databank action=load project={cfg["project"]} name={source} folder={folder}'
    worker.checked(_call(command, cfg), command)
    loadwait.loaded(cfg["role"], since, LOAD_S + PER_FILE_S * len(list(folder.glob("*.sqx"))), 0.25, source)   # the line, not the count: nothing compares it with the files


def run(expected: int, cfg: dict, progress: Callable[[int, str], None]) -> int:
    """Run the harness's retest task and wait for it.

    Args:
        expected: How many retests the legs have to return between them.
        cfg: The `execute` block.
        progress: Called with a percentage and a status line as the run advances.

    Returns:
        How many strategies SQX reports as tested, fewer than `expected` when its log says
        «Project finished» first. SystemExit when SQX refuses the start or aborts the project,
        when a status reply carries no count, or past `worker.MAX_HOURS`.

        ⚠️ `action=startOnlyTask` is NOT used: on this install it reports the project
        started and then tests nothing, silently, forever. `action=start` runs every ACTIVE
        task and skips the rest (🔬 2026-09-25), which is why `main` refuses unless the three
        WFC legs are the only ones switched on.
    """
    project = cfg["project"]
    # In a workflow project the other steps' databanks count too: measure from here.
    base = banks.in_bank(_call(f"-project action=status name={project}", cfg), project)
    logs = worker_dir(cfg["role"]) / "user/log/StrategyQuant"
    seen, began = banks.mark(logs), time.monotonic()
    reply = _call(f"-project action=start name={project}", cfg)
    if "rror" in reply or "Cannot start" in reply:      # as ui/daemon/launch/run.py: unresolved
        raise SystemExit(f"SQX no arrancó {project}: {reply.strip()}")
    done, end = 0, None
    while done < expected and not end:
        time.sleep(cfg["poll_seconds"])
        end = banks.ended(logs, seen)      # read before the status: a finished run's count is final
        if end == banks.ABORTED:
            raise SystemExit(f"SQX abortó {project} («Error while running project», "
                             f"ver {logs}) con {done} de {expected} reteseadas")
        if time.monotonic() - began > worker.MAX_HOURS * 3600:
            raise SystemExit(f"{project} sigue en {done} de {expected} tras {worker.MAX_HOURS} h")
        done = banks.tested(_call(f"-project action=status name={project}", cfg), project, base)
        progress(done * 100 // expected, f"{done} de {expected} reteseadas")
    return done


def panel(out: Path, cfg: dict, databank: str, stem: str) -> Path:
    """Export one retested databank as a CSV.

    Args:
        out: Directory to write into.
        cfg: The `execute` block.
        databank: Which databank to export — one leg's output.
        stem: File name without the extension, e.g. "retest_oos1".

    Returns:
        Path to the CSV. `action=export` is the only safe reader: `action=count` runs a
        sync-from-files first and destroys what `action=load` put in memory.
    """
    csv = out / f"{stem}.csv"
    command = f'-databank action=export project={cfg["project"]} name={databank} file={csv}'
    worker.checked(_call(command, cfg), command)
    return csv


def synced(expected: int, cfg: dict, databank: str) -> tuple[Path, int]:
    """Flush one retested databank onto disk and wait until the writing has finished.

    Args:
        expected: How many strategies the retest returned.
        cfg: The `execute` block.
        databank: Which databank to flush — one leg's output.

    Returns:
        The databank's folder inside the install, and how many `.sqx` it now holds;
        raises `SystemExit` when the poll runs out with fewer than `expected` on disk.

        SQX writes a retested strategy to disk lazily: measured 2026-09-22, a finished run
        of 2,000 had 962 files on disk. Every per-period equity curve lives inside those
        files, so without this the harvest reads half a batch. Safe here and only here --
        the install has the whole batch in memory, which is the condition hard rule 1
        turns on.

        ⚠️ A poll, not a sleep: syncing 962 `.sqx` took 21.95 s (2026-09-23), and the cost
        grows with the batch — a fixed wait returns a folder still filling.
    """
    command = f'-databank action=synctofiles project={cfg["project"]} name={databank}'
    worker.checked(_call(command, cfg), command)
    folder = legmod.bank_dir(cfg["role"], cfg["project"], databank)
    # 🔬 2026-10-05: SQX writes ~9 MB/s — 3,952 IS variants with 11 extra markets took 166 s,
    # 24 a second; the wait grows with the batch at a quarter of that, never under the floor.
    for _ in range(max(cfg["sync_tries"], expected // (6 * max(1, cfg["poll_seconds"])))):
        time.sleep(cfg["poll_seconds"])
        on_disk = len(list(folder.glob("*.sqx")))
        if on_disk >= expected:
            return folder, on_disk
    raise SystemExit(f"{databank}: {on_disk} of {expected} on disk when the wait ran out")


def main() -> None:
    """Load one batch, retest it, and leave the raw panel beside it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, help="the batch directory: sqx/ and manifest.parquet")
    ap.add_argument("--project", required=True,
                    help="the custom project holding the three WFC legs: the workflow's own "
                         "(`builder --workflow`), or one built with --tasks Retest")
    ap.add_argument("--clear", action="store_true",
                    help="empty the four databanks off the disk, install stopped, and exit")
    a = ap.parse_args()

    cfg = inputs.load()["execute"]
    cfg["project"] = a.project
    if a.project in STOCK:
        raise SystemExit(f"{a.project} es un proyecto de serie: regla dura 10, todo run en un "
                         "custom project. Usa el del workflow o crea uno con sqx.projects.builder.")
    be = livexec.backend(cfg)      # this holder's live GUI session, or the restart route
    if a.clear:
        gone = (livexec.clear if be is livexec else banks.clear)(cfg)
        print(f"{gone} .sqx borrados de {cfg['project']}: entrada y los tres tramos")
        return
    legs, folder = legmod.legs(), a.work / "sqx"
    n = len(list(folder.glob("*.sqx")))

    cfx = worker_dir(cfg["role"]) / "user/projects" / a.project / "project.cfx"
    with zipfile.ZipFile(cfx) as z:
        on = re.findall(r'active="true"[^>]*title="([^"]*)"', z.read("config.xml").decode())
    if be is not livexec and sorted(on) != sorted(leg["title"] for leg in legs):
        raise SystemExit(f"{a.project} tiene activas {on}: `action=start` las correria todas. "
                         f"python3 -m sqx.projects.stage --cfx {cfx} --step wfc")
    print(f"PROGRESS 2 despertando el {cfg['role']}", flush=True)
    ours = be.awake(cfg)

    def say(pct: int, line: str) -> None:
        """Fold the retest's own percentage into the stage's, after the load."""
        print(f"PROGRESS {5 + pct * 90 // 100} {line}", flush=True)

    # One job, then the install goes back down -- but only if this run is what woke it.
    # A worker left running is a worker that will auto-sync, and a sync deletes the .sqx
    # it does not hold in memory (hard rule 1).
    try:
        print(f"PROGRESS 5 cargando {n} variantes en {cfg['project']}/{legmod.source()}", flush=True)
        with phase("execute.sqx"):
            be.load(folder, cfg)
            # One `action=start` runs the project's three active retest tasks in chain --
            # build, oos1, oos2 -- so the progress counter passes `n` twice on its way. It is
            # the last leg that has to finish, and that is what `expected` counts here.
            done = be.run(n * len(legs), cfg, say) // len(legs)
        harvest = []
        for leg in legs:
            print(f"PROGRESS 92 exportando {leg['databank']}", flush=True)
            csv = be.panel(a.work, cfg, leg["databank"], f"retest_{leg['segment']}")
            with phase("execute.sync"): bank, on_disk = be.synced(done, cfg, leg["databank"])
            harvest.append(leg | {"panel": csv.name, "databank_dir": str(bank),
                                  "n_on_disk": on_disk})
    finally:
        if ours:
            worker.stop(cfg["role"], export=False)   # only WFC databanks: `afterrun.skipped`

    print(f"PROGRESS 100 {done} variantes x {len(legs)} tramos, "
          + ", ".join(f"{h['segment']}: {h['n_on_disk']} en disco" for h in harvest),
          flush=True)
    (a.work / "ran.json").write_text(
        json.dumps({"n_loaded": n, "n_returned": done, "legs": harvest}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()

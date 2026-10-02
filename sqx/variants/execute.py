#!/usr/bin/env python3
"""Retest a fabricated batch on the custodian and read the IS/OOS panel back out."""

import argparse
import json
import re
import sys
import time
import zipfile
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import worker
from core.paths import worker_dir
from sqx.variants import banks, inputs, legs as legmod, livexec

TESTED = re.compile(r"Total tested\s+(\d+)")
# A project whose tasks are all Retest reports no "Total tested" line; what moves is the
# record count across its databanks, the loaded batch plus every leg's output so far.
IN_BANK = re.compile(r"In databank\s+(\d+)")
SETTLE = 8          # seconds SQX needs after `load` before the databank answers for them all

STOCK = {"Builder", "Retester"}   # SQX's own projects: never a harness (hard rule 10)


def _call(command: str, cfg: dict) -> str:
    """One sqcli command against the install that holds the batch.

    Args:
        command: The sqcli command line.
        cfg: The `execute` block of config.yaml.

    Returns:
        Whatever the worker printed.
    """
    return worker.call(command, role=cfg["role"])


def awake(cfg: dict) -> bool:
    """Bring the install up if it is not already, and say whether this call did it.

    Args:
        cfg: The `execute` block of config.yaml.

    Returns:
        True when this call started it, so the caller knows to put it back. An install
        that was already awake is left awake: somebody else is using it.

        The port answers for about twenty seconds before the CLI does, replying
        `Error: CLI not ready.` in the meantime. That is normal and is polled through, not
        treated as a failure.
    """
    try:
        if "not ready" not in _call("-project action=list", cfg):
            return False
    except OSError:
        pass
    worker.start(cfg["role"])
    for _ in range(cfg["ready_tries"]):
        time.sleep(cfg["poll_seconds"])
        if "not ready" not in _call("-project action=list", cfg):
            return True
    raise SystemExit(f'{cfg["role"]} no respondio tras '
                     f'{cfg["ready_tries"] * cfg["poll_seconds"]} s')


def load(folder: Path, cfg: dict) -> None:
    """Put the batch into the harness's input databank, and nothing else with it.

    Args:
        folder: Directory of fabricated `.sqx`.
        cfg: The `execute` block.

    Returns:
        Nothing. The input and every leg's output databank are cleared first so the count afterwards is the batch and
        not the batch plus whatever the last run left. Loading the same folder twice does
        NOT de-duplicate -- SQX renames the second copy `P00000(1)` and keeps both.
    """
    source = legmod.source()
    for bank in [source] + [leg["databank"] for leg in legmod.legs()]:
        _call(f'-databank action=clear project={cfg["project"]} name={bank}', cfg)
        time.sleep(2)
    _call(f'-databank action=load project={cfg["project"]} name={source} '
          f"folder={folder}", cfg)
    time.sleep(SETTLE)


def run(expected: int, cfg: dict,
        progress: Callable[[int, str], None]) -> int:
    """Run the harness's retest task and wait for it.

    Args:
        expected: How many retests the legs have to return between them.
        cfg: The `execute` block.
        progress: Called with a percentage and a status line as the run advances.

    Returns:
        How many strategies SQX reports as tested.

        ⚠️ `action=startOnlyTask` is NOT used: on this install it reports the project
        started and then tests nothing, silently, forever. `action=start` runs every ACTIVE
        task and skips the rest (🔬 2026-09-25), which is why `main` refuses unless the three
        WFC legs are the only ones switched on.
    """
    # In a workflow project the other steps' databanks count too: measure from here.
    base = int(IN_BANK.search(_call(f'-project action=status name={cfg["project"]}', cfg))
               .group(1))
    log = worker_dir(cfg["role"]) / "user/log/StrategyQuant" / f"log_{time.strftime('%Y_%m_%d')}.log"
    since = log.stat().st_size if log.exists() else 0
    if "Cannot start" in (reply := _call(f'-project action=start name={cfg["project"]}', cfg)):
        raise SystemExit(f"SQX no arrancó {cfg['project']}: {reply.strip()}")   # unresolved
    done = 0
    while done < expected:
        time.sleep(cfg["poll_seconds"])
        if banks.aborted(log, since):
            raise SystemExit(f"SQX abortó {cfg['project']} («Error while running project», "
                             f"ver {log}) con {done} de {expected} reteseadas")
        status = _call(f'-project action=status name={cfg["project"]}', cfg)
        tested = TESTED.search(status)
        done = (int(tested.group(1)) if tested
                else int(IN_BANK.search(status).group(1)) - base)
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
    _call(f'-databank action=export project={cfg["project"]} name={databank} '
          f"file={csv}", cfg)
    return csv


def synced(expected: int, cfg: dict, databank: str) -> tuple[Path, int]:
    """Flush one retested databank onto disk and wait until the writing has finished.

    Args:
        expected: How many strategies the retest returned.
        cfg: The `execute` block.
        databank: Which databank to flush — one leg's output.

    Returns:
        The databank's folder inside the install, and how many `.sqx` it now holds.

        SQX writes a retested strategy to disk lazily: measured 2026-09-22, a finished run
        of 2,000 had 962 files on disk. Every per-period equity curve lives inside those
        files, so without this the harvest reads half a batch. Safe here and only here --
        the install has the whole batch in memory, which is the condition hard rule 1
        turns on.

        ⚠️ A poll, not a sleep: syncing 962 `.sqx` took 21.95 s (2026-09-23), and the cost
        grows with the batch — a fixed wait returns a folder still filling.
    """
    _call(f'-databank action=synctofiles project={cfg["project"]} name={databank}', cfg)
    folder = legmod.bank_dir(cfg["role"], cfg["project"], databank)
    for _ in range(cfg["sync_tries"]):
        time.sleep(cfg["poll_seconds"])
        on_disk = len(list(folder.glob("*.sqx")))
        if on_disk >= expected:
            break
    return folder, on_disk


def main() -> None:
    """Load one batch, retest it, and leave the raw panel beside it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path,
                    help="the batch directory: holds sqx/ and manifest.parquet")
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
    legs = legmod.legs()
    folder = a.work / "sqx"
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
        print(f"PROGRESS 5 cargando {n} variantes en "
              f"{cfg['project']}/{legmod.source()}", flush=True)
        be.load(folder, cfg)
        # One `action=start` runs the project's three active retest tasks in chain --
        # build, oos1, oos2 -- so the progress counter passes `n` twice on its way. It is
        # the last leg that has to finish, and that is what `expected` counts here.
        done = be.run(n * len(legs), cfg, say) // len(legs)
        harvest = []
        for leg in legs:
            print(f"PROGRESS 92 exportando {leg['databank']}", flush=True)
            csv = be.panel(a.work, cfg, leg["databank"], f"retest_{leg['segment']}")
            bank, on_disk = be.synced(done, cfg, leg["databank"])
            harvest.append(leg | {"panel": csv.name, "databank_dir": str(bank),
                                  "n_on_disk": on_disk})
    finally:
        if ours:
            worker.stop(cfg["role"])

    print(f"PROGRESS 100 {done} variantes x {len(legs)} tramos, "
          + ", ".join(f"{h['segment']}: {h['n_on_disk']} en disco" for h in harvest),
          flush=True)
    (a.work / "ran.json").write_text(
        json.dumps({"n_loaded": n, "n_returned": done, "legs": harvest}, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()

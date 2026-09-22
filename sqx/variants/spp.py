#!/usr/bin/env python3
"""Run one mother's SPP reconnaissance on the custodian and export the permutation table."""

import argparse
import json
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import worker
from core.paths import WORKERS, worker_dir
from sqx.variants import execute, harness, inputs

STAGED = "spp_in"


def stop(role: str) -> None:
    """Shut the install down so its project.cfx can be rewritten.

    Args:
        role: Worker role.

    Returns:
        Nothing. SQX rewrites a project.cfx on exit, so a harness edited while the install
        is up is lost in silence -- hard rule 4. The harness has to change between the
        in-sample and the out-of-sample run, so this happens twice per mother.
    """
    if f':{WORKERS[role]["port"]} ' in subprocess.run(
            ["ss", "-ltn"], capture_output=True, text=True).stdout:
        worker.stop(role)
        time.sleep(3)


def stage(mother: Path, work: Path) -> Path:
    """Put one mother in a folder of its own for loading.

    Args:
        mother: The `.sqx` to reconnoitre.
        work: The strategy's work directory.

    Returns:
        The folder. `-databank action=load` takes a folder, not a file, so a mother that
        shares a directory with anything else would drag it in.
    """
    folder = work / STAGED
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("*.sqx"):
        stale.unlink()
    (folder / mother.name).write_bytes(mother.read_bytes())
    return folder


def wait(cfg: dict, timeout: int,
         progress: Callable[[int, str], None]) -> tuple[int, float]:
    """Follow the harness until its one strategy has been tested.

    Args:
        cfg: The `execute` block of config.yaml.
        timeout: Seconds to allow before giving up.
        progress: Called with a percentage and a status line.

    Returns:
        (how many were tested, seconds taken). An SPP reports nothing at all until it
        finishes -- there is no per-permutation progress on the status endpoint -- so the
        only honest progress signal is elapsed time against the cap, plus the JVM's memory,
        which climbs while it accumulates results.
    """
    started = time.time()
    while time.time() - started < timeout:
        time.sleep(cfg["poll_seconds"])
        status = worker.call(f'-project action=status name={cfg["project"]}', cfg["role"])
        done = int(execute.TESTED.search(status).group(1))
        spent = time.time() - started
        if done:
            return done, spent
        progress(min(95, int(spent * 100 / timeout)),
                 f"SPP en marcha, {spent:.0f} s de {timeout} s")
    raise SystemExit(f"el SPP no termino en {timeout} s")


def main() -> None:
    """Rebuild the harness for one SPP, run it, and leave the profile where export finds it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--mother", required=True, type=Path, help="the .sqx to reconnoitre")
    ap.add_argument("--kind", required=True, choices=["spp_is", "spp_oos"])
    # `=` and not a space: pipeline/recipe.yaml splits a command on whitespace before it
    # fills the placeholders, so an argument that contains one becomes three.
    ap.add_argument("--chart", action="append", required=True,
                    help="repeatable, main first: SYMBOL=TIMEFRAME=SPREAD")
    a = ap.parse_args()

    settings = inputs.load()
    cfg, spp = settings["execute"], settings["spp"]
    folder = stage(a.mother, a.work)

    print(f"PROGRESS 2 preparando el arnes {a.kind}", flush=True)
    stop(cfg["role"])
    charts = [f'<Chart symbol="{p[0]}" timeframe="{p[1]}" spread="{p[2]}" />'
              for p in (c.replace("=", " ").split() for c in a.chart)]
    task = harness.ungate(harness.retarget(
        harness.donor_task(a.kind), charts, (cfg["input"], cfg["output"])))
    task = harness.cross_check(task, "OptProfileSysParamPermutation", True)
    task = harness.spp(task, spp["spread_pct"], spp["step_pct"], spp["max_tests"])
    harness.write(cfg["project"], task, cfg["role"])

    print("PROGRESS 5 despertando el custodio", flush=True)
    execute.awake(cfg)
    execute.load(folder, cfg)

    def say(pct: int, line: str) -> None:
        """Fold the wait's percentage into the stage's."""
        print(f"PROGRESS {5 + pct * 90 // 100} {line}", flush=True)

    worker.call(f'-project action=start name={cfg["project"]}', cfg["role"])
    done, spent = wait(cfg, spp["timeout_s"], say)

    # The profile is attached to the strategy, and nothing writes it to disk on its own:
    # `syncDatabanksAfterTaskDone` is false on this install, so the sync is explicit.
    for bank in (cfg["input"], cfg["output"]):
        worker.call(f'-databank action=synctofiles project={cfg["project"]} name={bank}',
                    cfg["role"])
        time.sleep(spp["sync_s"])
    worker.stop(cfg["role"])

    where = worker_dir(cfg["role"]) / "user/projects" / cfg["project"] / "databanks"
    found = {b: sorted((where / b).glob("*.sqx")) for b in (cfg["input"], cfg["output"])}
    print(f"PROGRESS 100 {done} reteseada en {spent:.0f} s", flush=True)
    (a.work / f"{a.kind}.json").write_text(json.dumps(
        {"tested": done, "wall_s": round(spent, 1), "kind": a.kind,
         "max_tests": spp["max_tests"], "spread_pct": spp["spread_pct"],
         "step_pct": spp["step_pct"],
         "in_databank": {b: [f.name for f in v] for b, v in found.items()}},
        indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

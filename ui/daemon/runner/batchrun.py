"""Run one study's per-strategy commands in one process: import once, fork a worker per core."""

import argparse
import importlib
import json
import os
import runpy
import sys
from pathlib import Path

# One BLAS thread per worker, set before numpy loads: OpenBLAS starts one per core in each
# process otherwise, and forty workers would fight over thousands (core/fanout.py).
for var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(var, "1")

NICE = 10        # below the window and the daemon, which then keep answering at full load
TAIL = 6         # lines of a failed task's log printed into the batch's own log


def one(task: tuple[int, dict, str]) -> tuple[str, int, list[str]]:
    """Run one strategy's command in this worker, as `python3 -m` would, into its own log.

    Args:
        task: (position, `{strategy, argv}` from the plan, the folder of the per-task logs).

    Returns:
        (strategy, exit code, the last TAIL lines of its log).
    """
    i, item, folder = task
    log = Path(folder) / f"{i:04d}.log"
    with open(log, "wb") as out:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(out.fileno(), 1)
        os.dup2(out.fileno(), 2)
        module, args = item["argv"][1], item["argv"][2:]
        sys.argv = [module, *args]
        try:
            runpy.run_module(module, run_name="__main__", alter_sys=True)
            rc = 0
        except SystemExit as stop:
            rc = stop.code if isinstance(stop.code, int) else (0 if stop.code is None else 1)
        except Exception:                     # noqa: BLE001 — a task's crash is its exit code
            import traceback
            traceback.print_exc()
            rc = 1
        sys.stdout.flush()
        sys.stderr.flush()
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    return item["strategy"], rc, lines[-TAIL:]


def main() -> None:
    """Import the study once, fork the workers, print PROGRESS as each strategy lands."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", required=True, type=Path, help="the JSON `runner.batch.fold` wrote")
    ap.add_argument("--workers", required=True, type=int, help="forked processes")
    a = ap.parse_args()
    if hasattr(os, "nice"):
        os.nice(NICE)
    items = json.loads(a.plan.read_text(encoding="utf-8"))
    for module in sorted({it["argv"][1] for it in items}):
        importlib.import_module(module)       # every report.py guards its main(): safe
    folder = a.plan.with_suffix("")
    folder.mkdir(parents=True, exist_ok=True)
    from core import fanout
    print(f"{len(items)} estrategias en {a.workers} procesos; logs por estrategia en {folder}",
          flush=True)
    _TASKS.update({i: (i, it, str(folder)) for i, it in enumerate(items)})
    done, failed = 0, []
    for _, (strategy, rc, tail) in fanout.run(_work, {i: len(items) - i for i in _TASKS},
                                              a.workers):
        done += 1
        if rc:
            failed.append(strategy)
            print(f"FALLÓ {strategy} (código {rc}):", *tail, sep="\n  ", flush=True)
        print(f"PROGRESS {100 * done / len(items):.0f} {done}/{len(items)} estrategias"
              + (f" · {len(failed)} fallaron" if failed else ""), flush=True)
    print(f"terminado: {len(items) - len(failed)} bien, {len(failed)} fallaron", flush=True)
    sys.exit(1 if failed and len(failed) == len(items) else 0)


_TASKS: dict = {}


def _work(key: int) -> tuple[str, int, list[str]]:
    """`fanout.run`'s module-level worker: the task at that position, from the forked state."""
    return one(_TASKS[key])


if __name__ == "__main__":
    main()

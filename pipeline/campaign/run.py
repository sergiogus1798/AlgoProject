"""The campaign's loop: take the next cell of the ledger, run its whole workflow, keep it, go on — until STOP."""

import argparse
import fcntl
import os
import shutil
import subprocess
import time
from pathlib import Path

import yaml

from core.assetoverride import PRECISION
from core.datapaths import campaign_dir, template_dir
from core.paths import DATA, ROOT, project_dir, worker_dir
from core.researchpaths import autopilot_runs
from pipeline.campaign import keep, ledger, palette

HERE = Path(__file__).parent
WORKFLOW = [str(ROOT / "bin" / "workflow.sh")]
WORKER = [str(ROOT / "bin" / "sqx-worker.sh"), "--role", "custodian", "stop"]
AUTOPILOT = "pipeline.autopilot.run --project {} "     # what SIGTERM is sent to: it stops SQX itself
POLL = 30                                               # seconds between two looks at the STOP file
BOOT = 5                                                # seconds between two tries while the autopilot is not up yet


def _stop_file() -> Path:
    """The file whose presence ends the loop: the owner's veto."""
    return campaign_dir() / "STOP"


def _command(cell: dict, cfg: dict, tries: int) -> list[str]:
    """What to launch: `template` while the project does not exist, `run` once it does, `--restart` on the third try.

    A test cell runs `--smoke`: only the readability rules judge, so its draw reaches the last step.
    Every try says `--own-log`: the custodian's recent log is this loop's own (a retry, or the cell
    before); without it the worker counted as busy for 15 min and the try was refused (🔬 2026-10-06, twice).
    """
    smoke = (["--smoke"] if cell.get("test") else []) + ["--own-log"]   # the custodian's log is always the loop's own
    if not (project_dir(cell["project"], worker_dir("custodian")) / "project.cfx").exists():
        return WORKFLOW + ["template", cell["project"], cell["symbol"], cell["timeframe"],
                           str(template_dir(cell["template"]) / "template.sqx"),
                           cell["palette"], f"Campaña: {cell['template']} en {cell['symbol']} "
                           f"{cell['timeframe']} {cell['direction']} (familia {cell['family']})",
                           str(cell.get("strategies", cfg["strategies"])), str(cell.get("minutes", cfg["minutes"]))] + smoke
    return WORKFLOW + ["run", cell["project"]] + smoke + (["--restart"] if tries == 2 else [])


def _attempt(command: list[str], project: str, precision: int | None = None) -> int | None:
    """Run one workflow command to its end. None when STOP arrived: the autopilot was told to leave and SQX is down.

    `precision` (a test cell's) puts every task of the project on it, the build included.
    """
    env = {**os.environ, **({PRECISION: str(precision)} if precision else {})}
    proc = subprocess.Popen(command, cwd=ROOT, env=env)
    while proc.poll() is None:
        if _stop_file().exists():
            while proc.poll() is None and subprocess.run(
                    ["pkill", "-TERM", "-f", AUTOPILOT.format(project)]).returncode:
                time.sleep(BOOT)                        # still creating the project: no autopilot to tell yet
            proc.wait()
            subprocess.run(WORKER, cwd=ROOT)
            return None
        time.sleep(POLL)
    return proc.returncode


def _newest(project: str) -> Path | None:
    """The project's latest autopilot run folder that has a `resumen.md` — the try with data, not a
    refused retry's empty folder (🔬 2026-10-06) — else the latest at all, None when none began."""
    runs = sorted((autopilot_runs() / project).glob("*")) if (autopilot_runs() / project).exists() else []
    return next((r for r in reversed(runs) if (r / "resumen.md").exists()), runs[-1] if runs else None)


def once(cell: dict, cfg: dict) -> str:
    """One cell from start to kept: three tries (the skill's routine), then its folder and its ledger line.

    Returns:
        The state it ended in: done, failed, interrupted, or question when the palette's expert
        asked one — the cell is set aside for the owner and the loop goes on.
    """
    if cell["palette"] == "experto":
        chosen, why = palette.choose(cell)
        if chosen is None:
            ledger.mark(cell, "question", question=why)
            print(f"{cell['project']}: apartada — {why}", flush=True)
            return "question"
        cell = {**cell, "palette": chosen}
    ledger.mark(cell, "running", palette=cell["palette"])
    started, code = time.time(), 1
    for tries in range(3):
        code = _attempt(_command(cell, cfg, tries), cell["project"], cell.get("precision"))
        if code in (0, None):
            break
    state = {0: "done", None: "interrupted"}.get(code, "failed")
    facts = keep.keep(cell, _newest(cell["project"]), state)
    ledger.mark(cell, state, wall_minutes=round((time.time() - started) / 60, 1), tries=tries + 1, **facts)
    print(f"{cell['project']}: {state} · {facts['steps_minutes']} min · {facts['finalists']} finalista(s) · "
          f"{facts['folder']}", flush=True)
    return state


def loop() -> None:
    """Cells one after another until the ledger is empty, STOP exists, the disk is short or failures pile up."""
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    campaign_dir().mkdir(parents=True, exist_ok=True)
    lock = (campaign_dir() / "loop.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)        # a second loop dies here
    failed = 0
    while (cell := ledger.following()) and not _stop_file().exists():
        free = shutil.disk_usage(DATA).free / 1e9
        if free < cfg["min_free_gb"]:
            print(f"PARADO: quedan {free:.0f} GB libres, menos de {cfg['min_free_gb']}", flush=True)
            return
        failed = failed + 1 if once(cell, cfg) == "failed" else 0
        if failed >= cfg["failures_in_a_row"]:
            print(f"PARADO: {failed} celdas fallidas seguidas", flush=True)
            return
    print("PARADO: STOP" if _stop_file().exists() else "PARADO: no quedan celdas pendientes", flush=True)


def main() -> None:
    """`--stop` asks the running loop to end (SQX stopped, the cell kept as interrupted); `--go` lifts it; bare, the loop."""
    p = argparse.ArgumentParser(prog="python3 -m pipeline.campaign.run")
    p.add_argument("--stop", action="store_true", help="para el bucle y SQX; guarda lo que haya")
    p.add_argument("--go", action="store_true", help="quita el STOP para poder arrancar de nuevo")
    args = p.parse_args()
    if args.stop:
        campaign_dir().mkdir(parents=True, exist_ok=True)
        _stop_file().touch()
        print(f"STOP puesto en {_stop_file()}: el bucle para en menos de {POLL} s y la celda queda «interrupted»")
    elif args.go:
        _stop_file().unlink(missing_ok=True)
        print("STOP quitado")
    else:
        loop()


if __name__ == "__main__":
    main()

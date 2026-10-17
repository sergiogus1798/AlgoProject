"""The SQX half of a check: a Test_ project on the conductor, one retest per firm, the EA exported."""

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

from core import exportdrv, proc, trades, worker
from core.paths import ROOT, WORKERS, databank_dir, worker_dir
from sqx import log as sqxlog
from sqx.projects import live, loadwait
from sqx.worker import guard as workerguard
from sqx.worker import session


def say(pct: int, line: str) -> None:
    """One progress line for the window's job strip."""
    print(f"PROGRESS {pct} {line}", flush=True)


def build(
    name: str, strategy: Path, asset: str, timeframe: str, role: str, members: list[str]
) -> dict[str, Any]:
    """Clone the frozen donor into a Test_ project with only the retests this check reuses.

    Through the builder's own command, so the project gets its registry row and every check
    the builder runs (hard rules 6 and 10). The strategy is its `--template`: the builder
    wants one, and no Build task is kept to read it.
    """
    argv = [
        sys.executable,
        "-m",
        "sqx.projects.builder",
        name,
        "--purpose",
        f"MT5 Bridge: {strategy.stem} en SQX con las condiciones de cada "
        "empresa, para compararlo con su backtest en MT5",
        "--template",
        str(strategy),
        "--symbol",
        asset,
        "--role",
        role,
        "--timeframe",
        timeframe,
        "--tasks",
        "Retest",
        "--only",
        ",".join(members),
        "--silence",
        "Retest",
        "--json",
    ]
    got = proc.run(
        argv, cwd=ROOT, capture_output=True, text=True, check=False, timeout=1800
    )
    if got.returncode:
        raise SystemExit(
            f"el builder no creó {name}:\n{(got.stderr or got.stdout)[-2000:]}"
        )
    return json.loads(got.stdout[got.stdout.index("{") :])


def synced(folder: Path, cfg: dict) -> bool:
    """Whether `folder` holds .sqx files, all non-empty and unchanged across two consecutive polls.

    The folder is read right after `synctofiles`: a file SQX is still writing is not taken (its
    size moves or is 0). False after `sync_tries` polls of `poll_s` s."""
    last: dict[str, int] | None = None
    for _ in range(cfg["sync_tries"]):
        now = {f.name: f.stat().st_size for f in folder.glob("*.sqx") if f.exists()}
        if now and 0 not in now.values() and now == last:
            return True
        last = now
        time.sleep(cfg["poll_s"])
    return False


def run(
    project: str,
    role: str,
    strategy: Path,
    work: Path,
    outputs: dict[str, str],
    cfg: dict,
) -> dict[str, Path]:
    """Load the strategy, run the project, and flush each firm's result to disk.

    Args:
        project: The configured project.
        role: Its worker, which this job starts and stops.
        strategy: The .sqx to verify.
        work: The check's folder; the strategy is staged under `in/`.
        outputs: {firm: output databank}.
        cfg: The `sqx` block of config.yaml.

    Returns:
        {firm: the output databank's folder}. Only `-project action=status` goes to the
        worker between the start and «Project finished» (hard rule 3); the worker is stopped
        in a `finally`, and refused beforehand if someone else has it up.
    """
    top, port = WORKERS[role]["path"], WORKERS[role]["port"]
    staged = work / "in"
    staged.mkdir(parents=True, exist_ok=True)
    shutil.copy2(strategy, staged / strategy.name)
    workerguard.refuse_if_up(role, top, port)
    folders = {}
    try:
        say(20, f"arrancando el {role}")
        worker.start(role)
        workerguard.mark(role, project)
        session.ready(project, role)
        since = live.mark(role)
        load = f"-databank action=load project={project} name={cfg['input']} folder={staged}"
        worker.checked(worker.call(load, role), load)
        loadwait.loaded(role, since, cfg["load_s"], cfg["poll_s"], cfg["input"])
        offsets = sqxlog.mark(top)
        worker.started(
            worker.call(f"-project action=start name={project}", role), project
        )
        say(30, "retest en SQX con las condiciones de cada empresa")
        session.watch(project, role, offsets)
        for firm, bank in outputs.items():
            worker.call(
                f"-databank action=synctofiles project={project} name={bank}", role
            )
            folder = databank_dir(project, bank, worker_dir(role))
            if not synced(
                folder, cfg
            ):  # a load or a sync that failed must never read as «SQX did not trade»
                raise SystemExit(
                    f"{bank} ({firm}): nada en disco tras el sync de {project} en "
                    f"{cfg['sync_tries'] * cfg['poll_s']} s: el retest no dejó su "
                    "estrategia; no se compara nada"
                )
            folders[firm] = folder
    finally:
        worker.stop(role, export=False)
        left = workerguard.stopped(role, top, port)
    if left:
        raise SystemExit(f"el {role} no se paró ({left}): no se sigue")
    return folders


def firm_trades(folders: dict[str, Path], work: Path) -> dict[str, pd.DataFrame]:
    """Every trade each firm's retest made, exported with the worker down.

    Returns:
        {firm: trades in SQX's export shape}. An empty databank is an empty frame — one `run`
        no longer returns: it raises when a firm's retest left nothing on disk.
    """
    out = {}
    for firm, folder in folders.items():
        found = sorted(folder.glob("*.sqx"))
        dest = work / "sqx" / firm
        shutil.rmtree(dest, ignore_errors=True)
        if not found:
            out[firm] = pd.DataFrame(
                columns=[
                    "Type",
                    "Open time",
                    "Open price",
                    "Size",  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
                    "Close time",
                    "Close price",
                    "Profit/Loss",
                ]
            )
            continue
        # The folder, never the file: given one .sqx, orderstocsv writes `<output>.csv` beside
        # the folder it was told to write into (🔬 2026-09-29).
        exportdrv.trades(folder, dest)
        csv = dest / f"{found[0].stem}.csv"
        got = trades.read(csv)
        got = got[got["Close price"].notna()]  # an unfilled pending order at the end
        got.to_parquet(dest / "trades.parquet", index=False)
        out[firm] = got
    return out


def retire(project: str, role: str) -> str:
    """Retire the Test_ project with its worker down (hard rule 6); its .cfx is archived.
    `--own`: this job built it minutes ago, so the freshness wait does not apply."""
    got = proc.run(
        [
            sys.executable,
            "-m",
            "sqx.projects.retire",
            project,
            "--role",
            role,
            "--yes",
            "--own",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    return (
        (got.stdout or got.stderr).strip().splitlines()[-1]
        if (got.stdout or got.stderr)
        else ""
    )

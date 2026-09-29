#!/usr/bin/env python3
"""The command: read each .sqx once, reconcile it against SQX, and write the study's parquet."""

import argparse
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from core import fanout, manifest, sqxfile, sqxretest, sqxstats
from core.paths import MASTER, databank_dir, worker_dir
from studies.breakage.mcRetest.inputs import config, tasks
from studies.breakage.mcRetest.measure import integrity, originals, store
from studies.breakage.mcRetest.model import recon


def one(path: Path, task: str, cfg: dict) -> dict:
    """Everything one strategy's run under one task contributes to the parquet.

    Args:
        path: The .sqx to read.
        task: One of tasks.TASKS.
        cfg: What inputs.config.load() returned.

    Returns:
        The four frames it produces plus its provenance and its reconciliation. Raises
        rather than returning a flag when the databank does not hold the task it claims:
        numbers written under a false label are worse than no numbers.
    """
    got = tasks.provenance(path)
    broken = tasks.verify(got, task)
    assert not broken, "; ".join(broken)
    strategy = path.stem.replace("Strategy ", "")
    capital = cfg["ingest"]["capital"]

    sims = sqxretest.simulations(path)
    stored = sqxretest.levels(path)
    metrics = recon.frame(sims["pnl"], sims["offsets"], capital)
    original = recon.frame(sqxretest.original(path),
                           np.array([0, sqxretest.original(path).size]), capital)
    usable = tasks.usable(got)

    keys = {"task": task, "strategy": strategy}
    sim_rows = pd.DataFrame({**keys, "sim": sims["index"],
                             **{name: values.astype(np.float32)
                                for name, values in metrics.items()}})
    level_rows = pd.DataFrame([{**keys, "level": level, "metric": name,
                                "value": float(value), "usable": usable}
                               for level, blob in stored.items() for name, value in blob.items()])
    pnl_rows = pd.DataFrame({**keys,
                             "sim": np.repeat(sims["index"], np.diff(sims["offsets"])),
                             "pnl_cents": sims["pnl"]})
    # The daily equity of the ORIGINAL, once per strategy, from the full-sample task: it is the
    # only dated series here -- a simulation carries no dates -- and the only possible input to a
    # correlation between strategies, which the effective number of bets needs.
    equity = sqxstats.equity(path) if task == "stress" else None
    returns = (pd.DataFrame({"strategy": strategy, "date": equity.index,
                             "ret": equity.diff().fillna(0.0).to_numpy()})
               if equity is not None else pd.DataFrame(columns=["strategy", "date", "ret"]))

    return {**keys, "sims": sim_rows, "levels": level_rows, "pnl": pnl_rows, "returns": returns,
            "original": pd.DataFrame([{**keys, **{k: float(v[0]) for k, v in original.items()}}]),
            "provenance": {**got, "usable": usable, "stored_only": integrity.stored_only(stored),
                           "identity": sqxfile.identity(path)},
            "reconciliation": integrity.reconcile(metrics, stored, cfg) if usable else {}}


def _job(args: tuple) -> dict:
    """Run one() in a worker process, and write its per-simulation P&L from there.

    Args:
        args: (path, task, cfg, staging), because a process pool maps over one argument.

    Returns:
        What one() returned, with `pnl` replaced by its row count. The P&L of every trade
        of every simulation is the one big table of an ingest, and each (task, strategy) is
        exactly one of its partitions: written by the worker that built it, it never
        travels back. 🔬 2026-09-25, returning it made the parent hold all of them at once.
    """
    path, task, cfg, staging = args
    got = one(path, task, cfg)
    got["pnl"] = store.write(got["pnl"], staging, ["task", "strategy"],
                             cfg["ingest"]["compression"])
    return got


def collect(project: str, cfg: dict, limit: int | None, staging: Path,
            install: Path = MASTER) -> list[dict]:
    """Read every strategy of every task, in parallel.

    Args:
        project: SQX project name.
        cfg: What inputs.config.load() returned.
        limit: Keep only this many strategies per task, for a smoke run.
        staging: Where the workers write the P&L dataset until the ingest is accepted.
        install: Which install holds the project; the master by default.

    Returns:
        One entry per (task, strategy). Memory stays bounded by one strategy's simulations
        per worker, so a databank of hundreds costs wall-clock and disk, never RAM.
    """
    jobs, absent = [], []
    for task in tasks.TASKS:
        found = sorted(databank_dir(project, tasks.DATABANK[task], install).glob("*.sqx"))
        # A task with no .sqx is a task the project could not run, not a broken ingest:
        # MinDistance never applies to a population of market orders, and a perturbation
        # whose range the owner has not decided is not written at all. The study reads the
        # perturbations that exist and says which are missing.
        if not found:
            absent.append(tasks.DATABANK[task])
            continue
        jobs += [(path, task, cfg, staging) for path in found[:limit]]
    required = [t for t in ("bar", "stress") if tasks.DATABANK[t] in absent]
    assert not required, (f"faltan las tareas {', '.join(required)}, que no son opcionales: "
                          "`bar` es el denominador de toda comparación y `stress` es la que "
                          "ordena las estrategias por su cola")
    if absent:
        print(f"sin correr, se leen las demás: {', '.join(absent)}")
    with ProcessPoolExecutor(max_workers=min(len(jobs), cfg["ingest"]["workers"]
                                             or fanout.CORES)) as pool:
        return list(pool.map(_job, jobs))


def report(results: list[dict], share: float) -> tuple[list[str], list[str], dict]:
    """What the reconciliation found, and what to record about it.

    Args:
        results: What collect() returned.
        share: Fraction of a metric's runs that must fail before the formula itself is
            called wrong, from `recon.systematic_share`.

    Returns:
        (fatal, isolated, summary). A metric that misses on `share` of its runs or more is
        a WRONG FORMULA and the ingest refuses: every number downstream is that
        reconstruction. A single run missing on a metric that reconciles everywhere else is
        one unreadable cell, and it is excluded and recorded — the same treatment the
        truncated confidence tables already get, for the same reason.

    🔬 That distinction is what the three formula bugs of 2026-09-24 looked like: WinningPct,
    KellyFormula and ZScore missed on 31 to 71 runs each, never on one.
    """
    worst, seen, missed = {}, {}, {}
    for entry in results:
        for name, got in entry["reconciliation"].items():
            worst[name] = max(worst.get(name, 0.0), got["worst_ratio"])
            seen[name] = seen.get(name, 0) + 1
            if not got["passed"]:
                missed.setdefault(name, []).append(
                    f"{entry['task']}/{entry['strategy']}: {name} "
                    f"at {got['worst_ratio']:.2f}x its tolerance")
    fatal = [line for name, lines in missed.items()
             if len(lines) >= max(2, share * seen[name]) for line in lines]
    isolated = [line for name, lines in missed.items()
                if len(lines) < max(2, share * seen[name]) for line in lines]
    return fatal, isolated, {"metrics_checked": len(worst), "unreconciled_cells": isolated,
                             "worst_ratio_by_metric": {k: round(v, 4)
                                                       for k, v in sorted(worst.items())}}


def main() -> None:
    """Read the eight task databanks and write one dated, immutable export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", default="MCR_All", help="name for this ingest run")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--limit", type=int, help="strategies per task, for a smoke run")
    parser.add_argument("--role", help="headless install holding the project; "
                        "omit for the master")
    parser.add_argument("--harvest-databank", default="Results",
                        help="the build databank studies.screening.gate.harvest paired, "
                             "for the original trades footprint() benchmarks against")
    parser.add_argument("--set", action="append", dest="overrides", metavar="KEY=VALUE")
    args = parser.parse_args()

    cfg = config.load(args.overrides)
    out = store.root(args.project, args.databank, args.day)
    # An export is dated and immutable. Parquet appends rather than replaces, so writing
    # into a directory that already holds one silently doubles every row -- which happened
    # here on 2026-09-18 and read back as 79,992 simulations from 40 runs of 1,000.
    assert not (out / store.SIMS).exists(), (
        f"{out} already holds an ingest; re-ingest under another --day or delete it first")
    install = worker_dir(args.role) if args.role else MASTER
    staging = out.parent / f".{out.name}.{store.PNL}.staging"
    shutil.rmtree(staging, ignore_errors=True)
    results = collect(args.project, cfg, args.limit, staging, install)
    failures, isolated, summary = report(results, cfg["recon"]["systematic_share"])
    if failures:
        shutil.rmtree(staging)
        print(f"ingest: REFUSING to write — {len(failures)} reconstructions disagree with SQX "
              "on a metric that misses systematically, which is a wrong formula")
        for line in failures[:20]:
            print("  ", line)
        sys.exit(1)
    for line in isolated:
        print(f"celda sin reconciliar, excluida y anotada: {line}")

    codec = cfg["ingest"]["compression"]
    counts = {}
    for name, parts in (("sims", ["task", "strategy"]), ("levels", ["task"]),
                        ("original", []), ("returns", [])):
        frame = pd.concat([entry[name] for entry in results], ignore_index=True)
        counts[name] = store.write(frame, out / name, parts, codec)
    shutil.move(staging, out / store.PNL)
    counts["pnl"] = sum(entry["pnl"] for entry in results)

    # The original trade list is a fact about the strategy, not about a task: one copy per
    # strategy, priced from its own harvest (OPEN.md #71), never per (task, strategy) like
    # everything above.
    identities = {e["strategy"]: e["provenance"]["identity"]
                 for e in results if e["task"] == "stress"}
    sample = next(iter(sorted(databank_dir(args.project, tasks.DATABANK["stress"],
                                           install).glob("*.sqx"))))
    symbol, feed = originals.feed_of(sample)
    point_value = originals.asset_point_value(symbol)
    harvested = originals.read(args.project, args.harvest_databank, identities, point_value)
    counts["trades"] = store.write(harvested, out / store.TRADES, ["strategy"], codec)
    missing = sorted(set(identities) - set(harvested["strategy"].unique()))
    if missing:
        print(f"  sin operaciones originales (no emparejadas en su cosecha): "
              f"{', '.join(missing)}")

    short = [f"{e['task']}/{e['strategy']}" for e in results if not e["provenance"]["usable"]]
    manifest.write(out,
                   {"install": str(install), "project": args.project,
                    "tasks": {e["task"] + "/" + e["strategy"]: e["provenance"] for e in results},
                    "unusable_level_tables": short, "asset": {"symbol": symbol, "feed": feed,
                                                              "point_value": point_value},
                    "harvest_databank": args.harvest_databank,
                    "integrity": summary, "config": config.flatten(cfg)},
                   " ".join(sys.argv), counts)
    print(f"ingest: {len(results)} runs, {counts['sims']} simulations -> {out}")
    print(f"  reconciled {summary['metrics_checked']} metrics against SQX, 0 disagreements")
    print(f"  level tables unusable (run cut short): {len(short)}"
          + (f" — {', '.join(short)}" if short else ""))


if __name__ == "__main__":
    main()

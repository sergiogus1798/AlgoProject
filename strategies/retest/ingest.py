#!/usr/bin/env python3
"""The command: read each .sqx once, reconcile it against SQX, and write the study's parquet."""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import manifest, sqxretest, sqxstats
from core.paths import databank_dir
from strategies.retest.inputs import config, tasks
from strategies.retest.measure import integrity, store
from strategies.retest.model import recon


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
            "provenance": {**got, "usable": usable, "stored_only": integrity.stored_only(stored)},
            "reconciliation": integrity.reconcile(metrics, stored, cfg) if usable else {}}


def _job(args: tuple) -> dict:
    """Run one() in a worker process.

    Args:
        args: (path, task, cfg), because a process pool maps over one argument.

    Returns:
        What one() returned.
    """
    return one(*args)


def collect(project: str, cfg: dict, limit: int | None) -> list[dict]:
    """Read every strategy of every task, in parallel.

    Args:
        project: SQX project name.
        cfg: What inputs.config.load() returned.
        limit: Keep only this many strategies per task, for a smoke run.

    Returns:
        One entry per (task, strategy). Memory stays bounded by one strategy's simulations
        per worker, so a databank of hundreds costs wall-clock and disk, never RAM.
    """
    jobs = []
    for task in tasks.TASKS:
        found = sorted(databank_dir(project, tasks.DATABANK[task]).glob("*.sqx"))
        assert found, f"{tasks.DATABANK[task]}: no .sqx found"
        jobs += [(path, task, cfg) for path in found[:limit]]
    with ProcessPoolExecutor(max_workers=cfg["ingest"]["workers"]) as pool:
        return list(pool.map(_job, jobs))


def report(results: list[dict]) -> tuple[list[str], dict]:
    """What the reconciliation found, and what to record about it.

    Args:
        results: What collect() returned.

    Returns:
        (failures, summary). A failure is a metric whose reconstruction fell outside the
        order statistics SQX could have reported; the ingest refuses to write when there is
        one, because every number downstream is that reconstruction.
    """
    worst, failures = {}, []
    for entry in results:
        for name, got in entry["reconciliation"].items():
            worst[name] = max(worst.get(name, 0.0), got["worst_ratio"])
            if not got["passed"]:
                failures.append(f"{entry['task']}/{entry['strategy']}: {name} "
                                f"at {got['worst_ratio']:.2f}x its tolerance")
    return failures, {"metrics_checked": len(worst),
                      "worst_ratio_by_metric": {k: round(v, 4) for k, v in sorted(worst.items())}}


def main() -> None:
    """Read the eight task databanks and write one dated, immutable export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", default="MCR_All", help="name for this ingest run")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--limit", type=int, help="strategies per task, for a smoke run")
    parser.add_argument("--set", action="append", dest="overrides", metavar="KEY=VALUE")
    args = parser.parse_args()

    cfg = config.load(args.overrides)
    out = store.root(args.project, args.databank, args.day)
    # An export is dated and immutable. Parquet appends rather than replaces, so writing
    # into a directory that already holds one silently doubles every row -- which happened
    # here on 2026-09-18 and read back as 79,992 simulations from 40 runs of 1,000.
    assert not (out / store.SIMS).exists(), (
        f"{out} already holds an ingest; re-ingest under another --day or delete it first")
    results = collect(args.project, cfg, args.limit)
    failures, summary = report(results)
    if failures:
        print(f"ingest: REFUSING to write — {len(failures)} reconstructions disagree with SQX")
        for line in failures[:20]:
            print("  ", line)
        sys.exit(1)

    codec = cfg["ingest"]["compression"]
    counts = {}
    for name, parts in (("sims", ["task", "strategy"]), ("levels", ["task"]),
                        ("pnl", ["task", "strategy"]), ("original", []), ("returns", [])):
        frame = pd.concat([entry[name] for entry in results], ignore_index=True)
        counts[name] = store.write(frame, out / name, parts, codec)

    short = [f"{e['task']}/{e['strategy']}" for e in results if not e["provenance"]["usable"]]
    manifest.write(out,
                   {"install": "master", "project": args.project,
                    "tasks": {e["task"] + "/" + e["strategy"]: e["provenance"] for e in results},
                    "unusable_level_tables": short,
                    "integrity": summary, "config": config.flatten(cfg)},
                   " ".join(sys.argv), counts)
    print(f"ingest: {len(results)} runs, {counts['sims']} simulations -> {out}")
    print(f"  reconciled {summary['metrics_checked']} metrics against SQX, 0 disagreements")
    print(f"  level tables unusable (run cut short): {len(short)}"
          + (f" — {', '.join(short)}" if short else ""))


if __name__ == "__main__":
    main()

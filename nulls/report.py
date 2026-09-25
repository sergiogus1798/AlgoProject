"""Run the null study over every strategy of one export and say what survives chance."""

import argparse
import json
import os
from datetime import date
from pathlib import Path

import pandas as pd

from core import fanout
from core.manifest import write as write_manifest
from core.paths import DATA, report_dir
from nulls import inputs, model, simulate, verdict


def newest(project: str, databank: str) -> Path:
    """The most recent dated trade export of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its `trades.parquet`. Exports are dated and immutable, so the newest is the one
        with the most strategies in it, never a partially refreshed older one.
    """
    folder = DATA / "raw" / project / databank.replace(" ", "_")
    return sorted(folder.glob("*/trades.parquet"))[-1]


# What the workers read, set before the pool forks: the bars, the config and every
# strategy's trades on the sample, each handed over without pickling.
_SHARED: dict = {}


def one(name: str) -> dict:
    """Every rung, every statistic and every warning for one strategy.

    Args:
        name: The strategy, whose trades, bars and config the fork handed over.

    Returns:
        One row: the real statistics, the p of each statistic under each rung, the
        attribution of the headline statistic, and the reasons to distrust all of it.
    """
    trades, frame, cfg = _SHARED["sample"][name], _SHARED["frame"], _SHARED["cfg"]
    kept = simulate.fixed(trades, frame, cfg)
    names = cfg["statistics"]["report"]
    seen = simulate.real(kept, names)
    per_rung = {rung: simulate.nulls(kept, rung, cfg, name) for rung in cfg["nulls"]["rungs"]}
    head = cfg["nulls"]["headline"]
    found = {name: verdict.pvalue(seen[name], per_rung[head][name], name) for name in names}
    row = {"n": len(trades), "reconcile": kept["checks"]["corr"]}
    row |= {f"real_{name}": seen[name] for name in names}
    row |= {f"p_{rung}_{name}": verdict.pvalue(seen[name], values[name], name)
            for rung, values in per_rung.items() for name in names}
    row |= {f"edge_{key}": value
            for key, value in verdict.attribute(seen, per_rung, names[0]).items()}
    row["distrust"] = " | ".join(verdict.distrust(kept, found, len(trades), cfg))
    return row


def main() -> None:
    """Run every strategy of one export through every rung and write the panel."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--timeframe", default="M30")
    ap.add_argument("--sample", default="OOS1", help="IST in sample, OOS1 out of it")
    ap.add_argument("--limit", type=int, default=0, help="first N strategies only, for a trial")
    ap.add_argument("--set", action="append", default=[], help="section.key=value")
    ap.add_argument("--workers", type=int, default=os.cpu_count(),
                    help="strategies run at once; each process holds one strategy's blocks")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    cfg["feed"] = a.feed
    packed = newest(a.project, a.databank)
    frame = inputs.bars(a.feed, a.timeframe)
    # One read and one split, where each strategy used to re-read the whole export: the
    # same rows in the same order as inputs.sample() returns them.
    every = pd.read_parquet(packed)
    every = every[every["Sample type"] == a.sample]
    sample = {str(k): v for k, v in every.groupby("strategy", observed=True)}
    names = sorted(sample)[:a.limit] if a.limit else sorted(sample)
    # Too few trades and there is no p to compute; such a strategy never reaches a worker.
    names = [n for n in names if len(sample[n]) >= cfg["verdict"]["min_trades"]]
    _SHARED.update(sample=sample, frame=frame, cfg=cfg)
    simulate.warm(frame, cfg)
    simulate.prime(simulate.fixed(sample[names[0]], frame, cfg), cfg)

    rows = {}
    costs = {name: len(sample[name]) for name in names}
    for i, (name, row) in enumerate(fanout.run(one, costs, a.workers), 1):
        rows[name] = row
        print(f"PROGRESS {100 * i // len(names)} {i}/{len(names)} {name}", flush=True)

    panel = pd.DataFrame(rows).T.loc[names].rename_axis("strategy")
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "nulls"
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "nulls.csv")
    (out / "rungs.json").write_text(json.dumps(model.RANDOMISES, indent=2), encoding="utf-8")
    write_manifest(out,
                   {"project": a.project, "databank": a.databank, "sample": a.sample,
                    "feed": a.feed, "timeframe": a.timeframe, "trades": str(packed),
                    "draws": cfg["nulls"]["draws"], "rungs": cfg["nulls"]["rungs"]},
                   " ".join(["python3 -m nulls.report", "--project", a.project,
                             "--databank", a.databank, "--feed", a.feed,
                             "--timeframe", a.timeframe, "--sample", a.sample]),
                   {"nulls.csv": len(panel)})
    print(f"\n{len(panel)} estrategias -> {out}")


if __name__ == "__main__":
    main()

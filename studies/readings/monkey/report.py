#!/usr/bin/env python3
"""The null study's command: every strategy of one export against its monkeys, or one alone."""

import argparse
import json
import os
from datetime import date

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output
from core.study.render import markdown
from engines.nulls import inputs, model
from studies.readings.monkey import many, one


def main() -> None:
    """Run one strategy, or every strategy of one export, through every rung."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--strategy", default="", help="one strategy, read in full; all when omitted")
    ap.add_argument("--timeframe", default="M30")
    ap.add_argument("--sample", default="OOS1", help="IST in sample, OOS1 out of it")
    ap.add_argument("--statistic", default="net",
                    help="with --strategy: which one the call and the channels read")
    ap.add_argument("--limit", type=int, default=0, help="first N strategies only, for a trial")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    ap.add_argument("--workers", type=int, default=os.cpu_count(),
                    help="strategies run at once; each process holds one strategy's blocks")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    cfg["feed"] = a.feed
    packed = inputs.newest(a.project, a.databank)
    frame = inputs.bars(a.feed, a.timeframe)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "monkey"
    if a.strategy:
        got = one.run(a.strategy, {"trades": inputs.sample(packed, a.strategy, a.sample),
                                   "frame": frame, "project": a.project,
                                   "databank": a.databank}, cfg, a.statistic)
        title = f"Contra el mono — {a.strategy}"
        print(markdown.render(got, title))
        print(f"-> {output.member(out, got, title, f'Muestra {a.sample}.')}")
        return

    # One read and one split, where each strategy used to re-read the whole export: the
    # same rows in the same order as inputs.sample() returns them.
    every = pd.read_parquet(packed)
    every = every[every["Sample type"] == a.sample]
    sample = {str(k): v for k, v in every.groupby("strategy", observed=True)}
    if a.limit:
        sample = {k: sample[k] for k in sorted(sample)[:a.limit]}
    got = many.run(sample, frame, cfg, a.workers)
    output.population(out, "monkey", got["population"],
                      f"Contra el mono — {a.project} / {a.databank}")
    got["panel"].to_csv(out / "nulls.csv")
    (out / "rungs.json").write_text(json.dumps(model.RANDOMISES, indent=2), encoding="utf-8")
    write_manifest(out,
                   {"project": a.project, "databank": a.databank, "sample": a.sample,
                    "feed": a.feed, "timeframe": a.timeframe, "input": str(packed.resolve()),
                    "draws": cfg["nulls"]["draws"], "rungs": cfg["nulls"]["rungs"],
                    "overrides": a.set},
                   " ".join(["python3 -m studies.readings.monkey.report", "--project", a.project,
                             "--databank", a.databank, "--feed", a.feed,
                             "--timeframe", a.timeframe, "--sample", a.sample]),
                   {"nulls.csv": len(got["panel"])})
    print(f"\n{len(got['panel'])} estrategias -> {out}")


if __name__ == "__main__":
    main()

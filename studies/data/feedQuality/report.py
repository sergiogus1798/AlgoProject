#!/usr/bin/env python3
"""Step 8's feed-quality attribution: how much of each strategy's profit sits on anomalous minutes.

Reads a `studies.screening.gate.harvest` folder — trades IS and OOS, the timeframe, the
databank each .sqx lives in — and the feed's anomalies as step 4's scan wrote them. Runs
after `gate.report` on the same harvest, as the edge-per-cost screen does, and writes
verdict.csv for /curate. Never recomputes a metric without the flagged trades.
"""

import argparse
from datetime import date
from pathlib import Path
from typing import cast

import pandas as pd

from core import fanout, manifest
from core.barstore import read
from core.paths import report_dir
from core.study import output, verdicts
from core.study.render import markdown
from core.study.result import progress
from studies.data.feedQuality import inputs, many, one, template, touch

# What `attribute` reads, set by main() before the fan-out: `fork` hands it to every worker.
STATE: dict = {}


def attribute(identity: str) -> dict | None:
    """One strategy's trades against the feed's anomalies; None when its .sqx is not found."""
    s = STATE
    name, source = s["names"][identity], s["source"]
    sqx = template.find(Path(source["install"]), source["project"], source["oos_databank"], name)
    if sqx is None:
        return None
    rules = template.rules(sqx)
    marked = touch.mark(s["trades"].iloc[s["rows"].get(identity, [])], s["events"], s["index"],
                        s["timeframe"], rules, s["cfg"]["spike"]["include_non_reverting"])
    return one.run(name, identity, marked, rules, s["cfg"])


def main() -> None:
    """Every strategy of one harvest against its feed's anomalies, or one read in full."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the harvest's build databank name")
    ap.add_argument("--feed", required=True, help="SQX feed, e.g. XAUUSD_M1")
    ap.add_argument("--strategy", default="", help="one strategy, read in full; all when omitted")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.harvest(a.project, a.databank)
    source = manifest.read(folder)["source"]
    ev = inputs.events(a.feed, cfg)
    meta = inputs.strategies(folder)
    timeframe = meta["TimeFrame [IS]"].iloc[0]
    index = cast(pd.DataFrame, read(a.feed, timeframe)).index
    trades = inputs.trades(folder)
    names = cast(pd.Series, meta["strategy"])
    wanted = cast(pd.Index, cast(pd.Series, names[names == a.strategy]).index if a.strategy else names.index)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "feedQuality"

    # One process per core: 10,000 strategies one after another were 42 min of step 8
    # (🔬 2026-10-08, DJ30 H1); the reading is deterministic, so the order changes nothing.
    rows = trades.groupby("identity").indices
    STATE.update(names=names, source=source, trades=trades, events=ev,
                 index=index, timeframe=timeframe, cfg=cfg, rows=rows)
    found, done = {}, 0
    for identity, got in fanout.run(attribute, {i: len(rows.get(i, [])) for i in wanted},
                                    fanout.CORES):
        found[identity], done = got, done + 1
        progress(100 * done // len(wanted), cast(str, names[identity]))
    results: dict[str, dict] = {i: found[i] for i in wanted if found[i] is not None}
    unread = [cast(str, names[i]) for i in wanted if found[i] is None]

    if a.strategy:
        got = results[cast(str, wanted[0])]
        title = f"Calidad del feed — {a.strategy}"
        print(markdown.render(got, title))
        print(f"-> {output.member(out, got, title, f'{a.feed}, velas {timeframe}.')}")
        return
    got = many.run(results, names, unread, cfg)
    output.population(out, "feedQuality", got["population"],
                      f"Calidad del feed — {a.project} / {a.databank}")
    command = " ".join(["python3 -m studies.data.feedQuality.report", "--project", a.project,
                        "--databank", a.databank, "--feed", a.feed, *a.set])
    verdicts.write(out, got["panel"].reset_index(), folder / "trades.parquet", command, a.set)
    counts = got["panel"]["alarm"].value_counts().to_dict()
    print(f"{len(got['panel'])} estrategias: {counts} -> {out}")


if __name__ == "__main__":
    main()

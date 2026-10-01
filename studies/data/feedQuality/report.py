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

from core import manifest
from core.barstore import read
from core.paths import report_dir
from core.study import output, verdicts
from core.study.render import markdown
from core.study.result import progress
from studies.data.feedQuality import inputs, many, one, template, touch


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
    index = read(a.feed, timeframe).index
    trades = inputs.trades(folder)
    names = meta["strategy"]
    wanted = names[names == a.strategy].index if a.strategy else names.index
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "feedQuality"

    results, unread = {}, []
    for n, identity in enumerate(wanted):
        sqx = template.find(Path(source["install"]), source["project"], source["oos_databank"],
                            names[identity])
        if sqx is None:
            unread.append(names[identity])
            continue
        rules = template.rules(sqx)
        mine = trades[trades["identity"] == identity]
        marked = touch.mark(mine, ev, index, timeframe, rules, cfg["spike"]["include_non_reverting"])
        results[identity] = one.run(names[identity], identity, marked, rules, cfg)
        progress(100 * (n + 1) // len(wanted), names[identity])

    if a.strategy:
        got = results[wanted[0]]
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

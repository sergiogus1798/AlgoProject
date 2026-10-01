#!/usr/bin/env python3
"""Edge per operation and breakeven cost — encargo 11. Step 8 over a harvest, or step 25 alone.

Reads a `studies.screening.gate.harvest` folder's `trades.parquet`/`metrics.parquet` — the
same shape a step-25 per-strategy trade export carries, so one command serves both places of
the workflow named in `docs/AgentPDFs/WORKFLOW.md`.
"""

import argparse
import json
from datetime import date

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output
from core.study.render import markdown
from studies.readings.edgeCost import costs, inputs, many, one, spread_share


def main() -> None:
    """Every strategy of one harvest against its edge-per-cost bar, or one read in full."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the harvest's build databank name")
    ap.add_argument("--feed", required=True, help="SQX feed, e.g. XAUUSD_M1")
    ap.add_argument("--strategy", default="", help="one strategy, read in full; all when omitted")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.newest(a.project, a.databank)
    asset = costs.asset_for(a.feed)
    timeframe = inputs.timeframe(folder)
    priced = costs.per_trade(inputs.trades(folder), asset, a.feed, timeframe)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "edgeCost"

    if a.strategy:
        names = inputs.names(folder)
        identity = names[names == a.strategy].index[0]
        mine = priced[priced["identity"] == identity]
        got = one.run(a.strategy, mine, costs.reconcile(mine), cfg, asset, identity)
        title = f"Edge por coste — {a.strategy}"
        lede = f"{asset['symbol']}, feed {a.feed}."
        print(markdown.render(got, title))
        print(f"-> {output.member(out, got, title, lede)}")
        return

    print(f"spread realmente cobrado, medido contra la barra {timeframe}: "
         f"{spread_share.measure(inputs.trades(folder), a.feed, timeframe)}")
    names = inputs.names(folder)
    got = many.run(priced, names, cfg, asset)
    recon = costs.reconcile(priced)
    print(f"reconciliación sobre toda la cosecha: corr {recon['corr']:.6f}, n={recon['n']}")
    print(json.dumps(recon["example"], indent=2, ensure_ascii=False))
    output.population(out, "edgeCost", got["population"],
                      f"Edge por coste — {a.project} / {a.databank}")
    got["panel"].to_csv(out / "verdict.csv",
                        columns=["identity", "edge_mean", "edge_median", "n", "verdict"])
    write_manifest(out,
                   {"project": a.project, "databank": a.databank, "feed": a.feed,
                    "input": str((folder / "trades.parquet").resolve())},
                   " ".join(["python3 -m studies.readings.edgeCost.report", "--project",
                             a.project, "--databank", a.databank, "--feed", a.feed]),
                   {"verdict.csv": len(got["panel"])})
    print(f"\n{len(got['panel'])} estrategias -> {out}")


if __name__ == "__main__":
    main()

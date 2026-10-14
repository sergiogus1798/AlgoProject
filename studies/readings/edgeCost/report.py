#!/usr/bin/env python3
"""Edge per operation over the cost paid, oos1 only — encargo 11, redefined by encargo 44. Step 8 or step 25.

Reads a `studies.screening.gate.harvest` folder's `trades.parquet`/`metrics.parquet` — the
same shape a step-25 per-strategy trade export carries, so one command serves both places of
the workflow named in `docs/AgentPDFs/WORKFLOW.md`.
"""

import argparse
from datetime import date

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output
from core.study.render import markdown
from ledger import steprows
from studies.readings.edgeCost import costs, inputs, many, one


def main() -> None:
    """Every strategy of one harvest against its edge-per-cost bar, or one read in full."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--databank", required=True, help="the harvest's build databank name"
    )
    ap.add_argument("--feed", required=True, help="SQX feed, e.g. XAUUSD_M1")
    ap.add_argument(
        "--strategy", default="", help="one strategy, read in full; all when omitted"
    )
    ap.add_argument(
        "--set", action="extend", nargs="+", default=[], help="section.key=value"
    )
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.newest(a.project, a.databank)
    asset = costs.asset_for(a.feed)
    timeframe = inputs.timeframe(folder)
    priced = costs.per_trade(inputs.trades(folder), a.feed, timeframe)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "edgeCost"

    if a.strategy:
        names = inputs.names(folder)
        identity = str(names.loc[names == a.strategy].index[0])
        mine = pd.DataFrame(priced[priced["identity"] == identity])
        got = one.run(a.strategy, mine, cfg, asset, identity)
        title = f"Edge por coste — {a.strategy}"
        lede = f"{asset['symbol']}, feed {a.feed}."
        print(markdown.render(got, title))
        print(f"-> {output.member(out, got, title, lede)}")
        return

    names = inputs.names(folder)
    got = many.run(priced, names, cfg, asset)
    output.population(
        out,
        "edgeCost",
        got["population"],
        f"Edge por coste — {a.project} / {a.databank}",
    )
    got["panel"].to_csv(
        out / "verdict.csv", columns=["identity", "edge_mean", "verdict"]
    )
    write_manifest(
        out,
        {
            "project": a.project,
            "databank": a.databank,
            "feed": a.feed,
            "input": str((folder / "trades.parquet").resolve()),
        },
        " ".join(
            [
                "python3 -m studies.readings.edgeCost.report",
                "--project",
                a.project,
                "--databank",
                a.databank,
                "--feed",
                a.feed,
            ]
        ),
        {"verdict.csv": len(got["panel"])},
    )
    print(
        steprows.log_cut(
            a.project,
            8,
            (len(got["panel"]), int((got["panel"]["verdict"] != "DESCARTAR").sum())),
            "edgeCost: edge por coste (DESCARTAR sólo en modo drop)",
            "studies.readings.edgeCost.report",
        )
    )
    print(f"\n{len(got['panel'])} estrategias -> {out}")


if __name__ == "__main__":
    main()

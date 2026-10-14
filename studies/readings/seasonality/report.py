#!/usr/bin/env python3
"""Seasonality: oos1 by UTC month, weekday and hour against the calendar null — encargo 56 F1. Describes, never filters.

Reads a `studies.screening.gate.harvest` folder's oos1 trades. A strategy's result depending
on one narrow calendar window is a fragility to report; nothing here feeds the builder (rule
15, owner D-1).
"""

import argparse
from datetime import date

import pandas as pd


from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output
from core.study.render import markdown
from studies.readings.seasonality import cells as cal, inputs, many, one


def main() -> None:
    """Every strategy of one harvest by calendar, or one read in full."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--databank", required=True, help="the harvest's build databank name"
    )
    ap.add_argument(
        "--feed", required=True, help="SQX feed, e.g. XAUUSD_M1 (its clock)"
    )
    ap.add_argument(
        "--strategy", default="", help="one strategy, read in full; all when omitted"
    )
    ap.add_argument(
        "--set", action="extend", nargs="+", default=[], help="section.key=value"
    )
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.newest(a.project, a.databank)
    zone, warnings = inputs.clock(a.feed, folder)
    trades = inputs.oos_trades(folder)
    if trades.empty:
        print(
            f"{folder}: ninguna operación de oos1; no hay nada que leer por calendario"
        )
        return
    names = inputs.names(folder)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "seasonality"
    print(f"reloj {zone} -> UTC · semilla {cfg['shuffle']['seed']} · {folder}")

    if a.strategy:
        identity = str(names.loc[names == a.strategy].index[0])
        placed = cal.place(pd.DataFrame(trades[trades["identity"] == identity]), zone)
        got = one.run(
            a.strategy,
            placed,
            cfg,
            identity,
            warnings,
        )
        title = f"Estacionalidad — {a.strategy}"
        print(markdown.render(got, title))
        print(
            f"-> {output.member(out, got, title, f'oos1, reloj {zone} pasado a UTC.')}"
        )
        return

    got = many.run(trades, names, zone, cfg, warnings)
    output.population(
        out,
        "seasonality",
        got["population"],
        f"Estacionalidad — {a.project} / {a.databank}",
    )
    got["panel"].to_csv(
        out / "verdict.csv",
        index=False,
        columns=["strategy", "identity", "verdict", "cell", "rest_pnl"],
    )
    write_manifest(
        out,
        {
            "project": a.project,
            "databank": a.databank,
            "feed": a.feed,
            "zone": zone,
            "seed": cfg["shuffle"]["seed"],
            "overrides": a.set,
            "input": str((folder / "trades.parquet").resolve()),
        },
        " ".join(
            [
                "python3 -m studies.readings.seasonality.report",
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
    print(got["population"]["verdict"]["meaning"])
    print(f"\n{len(got['panel'])} estrategias -> {out}")


if __name__ == "__main__":
    main()

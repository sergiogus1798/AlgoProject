#!/usr/bin/env python3
"""The cross-market study's command: every strategy's breadth verdict, or one strategy in full."""

import argparse
from datetime import date
import os
import sys

from core.paths import report_dir
from core.study import output, verdicts
from studies.transfer.crossmarket import load, many, one
from studies.transfer.crossmarket.inputs import config

LEDE = ("¿El acierto de la entrada se traslada a mercados que la estrategia nunca vio, o sólo "
        "estaba larga mientras subían?")


def main() -> None:
    """Judge every strategy of one export on breadth, or write one strategy's whole study."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank export_retest exported")
    ap.add_argument("--asset", required=True, help="base asset, e.g. USDJPY")
    ap.add_argument("--day", default=date.today().isoformat(), help="export date, YYYY-MM-DD")
    ap.add_argument("--strategy", help="study this one strategy in full instead of the batch")
    ap.add_argument("--only", help="with --strategy: this one market feed alone")
    ap.add_argument("--floor", type=float,
                    help="fraction of markets whose expectancy must clear zero to keep it; "
                         "the same as --set verdict.breadth_floor=")
    ap.add_argument("--set", action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    ap.add_argument("--workers", type=int, default=os.cpu_count(),
                    help="markets studied at once; each holds its own null batches, so "
                         "this is the knob that trades RAM for wall clock")
    a = ap.parse_args()

    overrides = a.set + ([f"verdict.breadth_floor={a.floor}"] if a.floor is not None else [])
    cfg = config.load(overrides)
    inputs = load.load(a.project, a.databank, a.asset, a.day)
    out = report_dir(a.project, a.databank, a.day) / "crossmarket"
    if a.strategy:
        got = one.run(a.strategy, inputs, cfg, a.only)
        path = output.member(out, got, f"Cross-market — {a.strategy}", LEDE)
        print(f"-> {path}")
        return

    print(f"{len(inputs['strategies'])} estrategias x {len(inputs['universe']['markets'])} "
          f"mercados a {cfg['nulls']['draws']:,} sorteos — minutos por estrategia. Bájalos con "
          f"--set nulls.draws=2000 para una prueba.", flush=True)
    got = many.run(inputs, cfg, a.workers)
    output.population(out, "crossmarket", got["population"],
                      f"Cross-market — {a.project} / {a.databank}", LEDE)
    verdicts.write(out, got["table"], inputs["path"], " ".join(sys.argv), overrides)
    kept = int((got["table"].verdict != "DESCARTAR").sum())
    print(f"\n{kept} de {len(got['table'])} pasan el suelo de amplitud -> {out / 'verdict.csv'}")


if __name__ == "__main__":
    main()

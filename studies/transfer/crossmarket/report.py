#!/usr/bin/env python3
"""The cross-market study's command: every strategy measured on «does the logic travel?», or one in full."""

import argparse
from datetime import date
import sys

from core import fanout
from core.paths import report_dir
from core.study import draws, identity, output, verdicts
from studies.transfer.crossmarket import load, many, one
from studies.transfer.crossmarket.inputs import config

LEDE = (
    "¿La lógica de la entrada viaja a mercados que la estrategia nunca vio, o sólo "
    "estaba larga mientras subían? Mide; el juez de criteria.yaml decide."
)


def main() -> None:
    """Measure every strategy of one export on the travel test, or write one strategy's whole study."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--databank", required=True, help="the databank export_retest exported"
    )
    ap.add_argument("--asset", required=True, help="base asset, e.g. USDJPY")
    ap.add_argument(
        "--day", default=date.today().isoformat(), help="export date, YYYY-MM-DD"
    )
    ap.add_argument(
        "--strategy", help="study this one strategy in full instead of the batch"
    )
    ap.add_argument("--only", help="with --strategy: this one market feed alone")
    ap.add_argument(
        "--set", action="extend", nargs="+", default=[], metavar="KEY=VALUE"
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=fanout.CORES,
        help="kept for the callers; the travel run uses every physical core",
    )
    a = ap.parse_args()

    overrides = a.set
    cfg = config.load(overrides)
    inputs = load.load(a.project, a.databank, a.asset, a.day)
    out = report_dir(a.project, a.databank, a.day) / "crossmarket"
    if identity.note(inputs["identity"]):
        print(identity.note(inputs["identity"]), flush=True)
    if inputs["outside"]:
        print(
            f"{inputs['outside']:,} operaciones fuera de la ventana propia de su mercado "
            "(build..oos1 de SU ficha): no se leen",
            flush=True,
        )
    if a.strategy:
        got = one.run(a.strategy, inputs, cfg, a.only, overrides)
        path = output.member(out, got, f"Cross-market — {a.strategy}", LEDE)
        print(f"-> {path}")
        return

    print(
        f"{len(inputs['strategies'])} estrategias x {len(inputs['universe']['markets'])} "
        f"mercados a {cfg['travel']['draws']:,} corridas al azar conjuntas. Bájalas con "
        f"--set travel.draws=500 para una prueba.",
        flush=True,
    )
    got = many.run(inputs, cfg, a.workers, overrides)
    output.population(
        out,
        "crossmarket",
        got["population"],
        f"Cross-market — {a.project} / {a.databank}",
        LEDE,
    )
    table = got["table"].assign(
        note=lambda t: t["identity"].isna().map({True: identity.NOTE, False: ""})
    )
    verdicts.write(out, table, inputs["path"], " ".join(sys.argv), overrides)
    got["markets"].to_parquet(out / "markets.parquet", index=False)
    draws.save(out, got["draws"])
    print(f"\n{len(got['table'])} estrategias medidas -> {out / 'verdict.csv'}")


if __name__ == "__main__":
    main()

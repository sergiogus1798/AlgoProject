#!/usr/bin/env python3
"""Run the Monte Carlo study over every strategy of one databank and write its report."""

import argparse
from datetime import date

import pandas as pd

from core import assets
from core.paths import report_dir
from core.study import output, verdicts
from strategies.monteCarlo import load, many
from strategies.monteCarlo.inputs import config

LEDE = ("Robustez de una estrategia ya aceptada: cuánto de este resultado es suerte, y de "
        "qué tipo.")


def main() -> None:
    """Analyse a databank's exported trades and write the report beside them."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--asset", required=True, help="asset name in assets/, e.g. XAUUSD")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--bars-timeframe", default="M30",
                    help="which exported bars the daily volatility is built from")
    ap.add_argument("--portfolio", action="store_true",
                    help="treat every strategy as one combined trade stream")
    ap.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE",
                    help="override any config value, e.g. global.n_sims=20000")
    a = ap.parse_args()

    print(assets.report(a.asset))
    cfg = config.load(a.set)
    inputs = load.load(a.project, a.databank, a.asset, a.export, cfg, a.bars_timeframe,
                         a.portfolio)
    print(f"{len(inputs['streams'])} streams · estabilidad sobre {inputs['reference']}",
          flush=True)
    got = many.run(inputs, cfg)

    # A portfolio run writes beside the per-strategy one, never over it: they answer
    # different questions about the same databank and both are worth keeping.
    out = (report_dir(a.project, a.databank, date.today().isoformat())
           / ("monteCarlo_portfolio" if a.portfolio else "monteCarlo"))
    title = f"Monte Carlo — {a.project} / {a.databank}"
    for m in got["members"]:
        output.member(out, m, f"Monte Carlo — {m['strategy']}", LEDE)
    output.population(out, "monteCarlo", got["population"], title)
    fired = [{"strategy": m["strategy"], **f} for m in got["members"]
             for f in m["summary"]["fired"]]
    pd.DataFrame(fired, columns=["strategy", "family", "test", "value", "limit", "gate"]
                 ).to_csv(out / "flags.csv", index=False)
    command = (f"python3 -m strategies.monteCarlo.report --project {a.project} --databank "
               f"{a.databank} --asset {a.asset} --export {a.export}"
               + (" --portfolio" if a.portfolio else "")
               + "".join(f" --set {s}" for s in a.set))
    table = many.table(got["members"])
    verdicts.write(out, table, inputs["shared"]["export"], command, a.set)
    print(table[["strategy", "verdict", "composite", "gates"]].to_string(index=False))
    print(f"{len(table)} estrategias → {out}")


if __name__ == "__main__":
    main()

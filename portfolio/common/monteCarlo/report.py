#!/usr/bin/env python3
"""Run the Monte Carlo study over every strategy of one databank and write its report."""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from core import assets
from core.paths import report_dir
from core.study import output, verdicts
from portfolio.common.monteCarlo import load, many, one
from portfolio.common.monteCarlo.inputs import config

LEDE = ("Robustez de una estrategia ya aceptada: cuánto de este resultado es suerte, y de "
        "qué tipo.")


def write_one(out: Path, inputs: dict, cfg: dict, strategy: str) -> Path:
    """One strategy's run: only `estrategias/<name>.json` and its page, as crossTF's
    `--strategy` does — `verdict.csv`, `flags.csv`, `monteCarlo.json` and the manifest are
    the population's, and one strategy must not replace them. Its stability section is the
    export's, measured on the longest strategy, exactly as the population run reads it.

    Args:
        out: The module's report folder.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        strategy: Its name as the export spells it.

    Returns:
        The JSON's path.
    """
    if strategy not in inputs["streams"]:
        raise SystemExit(f"{strategy} no está en {inputs['shared']['export']}")
    got = one.run(strategy, inputs, cfg)
    print(f"{strategy}: {got['summary']['tier']} {got['summary']['composite']:.0f}")
    return output.member(out, got, f"Monte Carlo — {strategy}", LEDE)


def main() -> None:
    """Analyse a databank's exported trades and write the report beside them."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--asset", required=True, help="asset name in assets/, e.g. XAUUSD")
    ap.add_argument("--day", default=date.today().isoformat(), help="export date, YYYY-MM-DD")
    ap.add_argument("--bars-timeframe", default="M30",
                    help="which exported bars the daily volatility is built from")
    ap.add_argument("--portfolio", action="store_true",
                    help="treat every strategy as one combined trade stream")
    ap.add_argument("--strategy", help="one strategy alone, as the export names it: writes "
                    "only estrategias/<name>.json, never the population's files")
    ap.add_argument("--set", action="extend", nargs="+", default=[], metavar="KEY=VALUE",
                    help="override any config value, e.g. global.n_sims=20000")
    a = ap.parse_args()
    if a.strategy and a.portfolio:
        ap.error("--strategy y --portfolio se excluyen: una cartera es todas a la vez")

    print(assets.report(a.asset))
    cfg = config.load(a.set)
    inputs = load.load(a.project, a.databank, a.asset, a.day, cfg, a.bars_timeframe,
                         a.portfolio)
    print(f"{len(inputs['streams'])} streams · estabilidad sobre {inputs['reference']}",
          flush=True)
    # A portfolio run writes beside the per-strategy one, never over it: they answer
    # different questions about the same databank and both are worth keeping.
    out = (report_dir(a.project, a.databank, date.today().isoformat())
           / ("monteCarlo_portfolio" if a.portfolio else "monteCarlo"))
    if a.strategy:
        print(f"-> {write_one(out, inputs, cfg, a.strategy)}")
        return
    got = many.run(inputs, cfg)
    title = f"Monte Carlo — {a.project} / {a.databank}"
    for m in got["members"]:
        output.member(out, m, f"Monte Carlo — {m['strategy']}", LEDE)
    output.population(out, "monteCarlo", got["population"], title)
    fired = [{"strategy": m["strategy"], **f} for m in got["members"]
             for f in m["summary"]["fired"]]
    pd.DataFrame(fired, columns=["strategy", "family", "test", "value", "limit", "gate"]
                 ).to_csv(out / "flags.csv", index=False)
    command = (f"python3 -m portfolio.common.monteCarlo.report --project {a.project} --databank "
               f"{a.databank} --asset {a.asset} --day {a.day}"
               + (" --portfolio" if a.portfolio else "")
               + "".join(f" --set {s}" for s in a.set))
    table = many.table(got["members"])
    verdicts.write(out, table, inputs["shared"]["export"], command, a.set)
    print(table[["strategy", "verdict", "composite", "gates"]].to_string(index=False))
    print(f"{len(table)} estrategias → {out}")


if __name__ == "__main__":
    main()

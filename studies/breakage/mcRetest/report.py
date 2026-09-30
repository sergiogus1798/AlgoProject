#!/usr/bin/env python3
"""The command: every strategy of one ingest, from parquet to a report and a verdict table."""

import argparse
import sys
from datetime import date

from core.paths import report_dir
from core.study import output, verdicts
from studies.breakage.mcRetest import load, many
from studies.breakage.mcRetest.contract import words
from studies.breakage.mcRetest.inputs import config
from studies.breakage.mcRetest.verdict import gates

LEDE = ("Ocho tareas, cada una perturbando una sola cosa, N re-ejecuciones completas del "
        "backtest en cada una (N = `mc_retest.simulations`). La pregunta no es si la curva "
        "fue suerte, sino si habría "
        "existido.")


def main() -> None:
    """Read one ingest and write its report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", default="MCR_All")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--set", action="extend", nargs="+", default=[], dest="overrides",
                        metavar="KEY=VALUE")
    args = parser.parse_args()

    missing = set(gates.VETOES) ^ set(words.SENTENCES)
    assert not missing, f"gates and words disagree about these vetoes: {sorted(missing)}"

    cfg = config.load(args.overrides)
    inputs = load.load(args.project, args.databank, args.day)
    got = many.run(inputs, cfg)

    out = report_dir(args.project, args.databank, args.day) / "mcRetest"
    title = f"Monte Carlo Retest — {args.project} / {args.databank} / {args.day}"
    for m in got["members"]:
        output.member(out, m, f"Monte Carlo Retest — {m['strategy']}", LEDE)
    output.population(out, "mcRetest", got["population"], title, LEDE)
    table = many.table(got["members"])
    verdicts.write(out, table, inputs["folder"], " ".join(sys.argv), args.overrides)
    print(f"report: {len(table)} strategies -> {out}")
    print(table.drop(columns=["identity"]).to_string(index=False, max_colwidth=40))


if __name__ == "__main__":
    main()

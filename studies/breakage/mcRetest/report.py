#!/usr/bin/env python3
"""The command: every strategy of one ingest, from parquet to a report and a verdict table."""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import cast

import pandas as pd

from core.paths import report_dir
from core.study import draws, output, verdicts
from ledger import steprows
from studies.breakage.mcRetest import load, many, one
from studies.breakage.mcRetest.contract import words
from studies.breakage.mcRetest.inputs import config
from studies.breakage.mcRetest.load import Loaded
from studies.breakage.mcRetest.verdict import gates

LEDE = ("Ocho tareas, cada una perturbando una sola cosa, N re-ejecuciones completas del "
        "backtest en cada una (N = `mc_retest.simulations`). La pregunta no es si la curva "
        "fue suerte, sino si habría "
        "existido.")


def named(strategy: str, inputs: Loaded) -> str:
    """The ingest's own spelling of a strategy: it names «1.26.46», the databank «Strategy 1.26.46».

    Args:
        strategy: Either spelling.
        inputs: What load.load() returned.

    Returns:
        The name the ingest's tables carry.
    """
    names = set(inputs["sims"]["strategy"].unique())
    found = [n for n in (strategy, strategy.removeprefix("Strategy "), f"Strategy {strategy}")
             if n in names]
    if not found:
        raise SystemExit(f"{strategy} no está en el ingest {inputs['folder']}")
    return found[0]


def write_one(out: Path, inputs: Loaded, cfg: dict, strategy: str) -> Path:
    """One strategy's run: only `estrategias/<name>.json` and its page, as crossTF's
    `--strategy` does — `verdict.csv`, `mcRetest.json` and the manifest are the population's,
    and the battery's cross-strategy facts (effective bets, multiplicity, rank stability)
    need every strategy; none of them reaches a strategy's own result.

    Args:
        out: The module's report folder.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        strategy: Either spelling of its name.

    Returns:
        The JSON's path. A strategy missing one of the tasks that ran is refused, as
        `run.battery` leaves it out of the report.
    """
    name = named(strategy, inputs)
    sims = inputs["sims"]
    ran = set(sims["task"].unique())
    short = sorted(ran - set(sims.loc[sims["strategy"] == name, "task"].unique()))
    if short:
        raise SystemExit(f"{name} fuera del informe, le faltan tareas: {', '.join(short)}")
    if inputs["trades"] is not None:
        inputs = {**inputs, "trades": cast(pd.DataFrame, inputs["trades"][inputs["trades"]["strategy"] == name])}
    got = one.run(name, inputs, cfg)
    draws.merge(out, got.pop("draws", []), defer=True)
    return output.member(out, got, f"Monte Carlo Retest — {name}", LEDE)


def main() -> None:
    """Read one ingest and write its report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", default="MCR_All")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--strategy", help="one strategy alone, «1.26.46» or «Strategy 1.26.46»: "
                        "writes only estrategias/<name>.json, never the population's files")
    parser.add_argument("--set", action="extend", nargs="+", default=[], dest="overrides",
                        metavar="KEY=VALUE")
    args = parser.parse_args()

    missing = set(gates.VETOES) ^ set(words.SENTENCES)
    assert not missing, f"gates and words disagree about these vetoes: {sorted(missing)}"

    cfg = config.load(args.overrides)
    inputs = load.load(args.project, args.databank, args.day)
    out = report_dir(args.project, args.databank, args.day) / "mcRetest"
    if args.strategy:
        print(f"-> {write_one(out, inputs, cfg, args.strategy)}")
        return
    got = many.run(inputs, cfg)

    title = f"Monte Carlo Retest — {args.project} / {args.databank} / {args.day}"
    for m in got["members"]:
        output.member(out, m, f"Monte Carlo Retest — {m['strategy']}", LEDE)
    output.population(out, "mcRetest", got["population"], title, LEDE)
    draws.save(out, got.get("draws", []))
    table = many.table(got["members"])
    verdicts.write(out, table, inputs["folder"], " ".join(sys.argv), args.overrides)
    print(steprows.log_cut(args.project, 14, (len(table),
                                           int(table["verdict"].isin(["STRONG", "ACCEPTABLE", "MARGINAL"]).sum())),
                           "mcRetest: veredicto de la batería", "studies.breakage.mcRetest.report"))
    print(f"report: {len(table)} strategies -> {out}")
    print(table.drop(columns=["identity"]).to_string(index=False, max_colwidth=40))


if __name__ == "__main__":
    main()

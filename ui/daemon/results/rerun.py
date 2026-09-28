"""One sub-test of a study run again alone, written beside the stored result and never over it (OPEN §54)."""

import argparse
import re
from datetime import date, datetime
from pathlib import Path

from core.paths import report_dir
from core.study import output
from portfolio.common.monteCarlo import load as mc_load
from portfolio.common.monteCarlo import one as mc_one
from portfolio.common.monteCarlo.inputs import config as mc_config
from portfolio.common.monteCarlo.model import stress
from portfolio.common.monteCarlo.simulate import sweeps
from studies.transfer.crossmarket import load as cm_load
from studies.transfer.crossmarket import one as cm_one
from studies.transfer.crossmarket.inputs import config as cm_config
from ui.daemon.results import store


def crossmarket(a: argparse.Namespace) -> dict:
    """One market of the cross-market export, for one strategy (`one.run(only=feed)`).

    Args:
        a: The parsed command; `only` is a feed of the export.

    Returns:
        The partial contract dict: that market's blocks, no verdict.
    """
    return cm_one.run(a.strategy, cm_load.load(a.project, a.databank, a.asset, a.day),
                      cm_config.load(a.set), a.only)


def monte_carlo(a: argparse.Namespace) -> dict:
    """One sub-test of the trade Monte Carlo, named as the explorer's «Prueba» selector names it.

    Args:
        a: The parsed command; `only` is the sub-test's title («Block shuffle, 12 trades»,
            «Costes hasta el doble»…) — the label the window offers — or its internal label.

    Returns:
        The partial contract dict: that sub-test's distributions and tables, no verdict.
    """
    cfg = mc_config.load(a.set)
    inputs = mc_load.load(a.project, a.databank, a.asset, a.day, cfg)
    n = len(inputs["streams"][a.strategy]["pnl"])
    titles = {s["title"]: s["label"] for s in sweeps.plan(n, cfg)}
    titles.update({t: k for k, t in stress.TITLES.items()})
    if a.only not in titles and a.only not in titles.values():
        raise SystemExit(f"«{a.only}» no es una prueba de {a.strategy} con {n} operaciones: "
                         f"elige una de {', '.join(titles)}")
    return mc_one.run(a.strategy, inputs, cfg, titles.get(a.only, a.only))


RUNS = {"crossmarket": crossmarket, "monteCarlo": monte_carlo}


def home(project: str, databank: str, study: str, strategy: str) -> Path:
    """The study folder a partial belongs beside: the newest day with this strategy's full result.

    Args:
        project, databank: Where.
        study: Study key.
        strategy: Strategy name.

    Returns:
        `reports/<P>/<D>/<day>/<study>/` of that day, or today's when no full result exists
        yet — the partial then stands alone, and the window says so by drawing it alone.
    """
    for day in store.days(project, databank, study):
        folder = store.bank(project, databank) / day / study
        if Path(f"{folder / 'estrategias' / strategy}.json").is_file():
            return folder
    return report_dir(project, databank, date.today().isoformat()) / study


def main() -> None:
    """Run one sub-test and write it under `<study>/parciales/<stamp>_<only>/estrategias/`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", required=True, choices=sorted(RUNS))
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--asset", required=True, help="base asset, e.g. USDJPY")
    ap.add_argument("--day", required=True, help="the raw export's date, YYYY-MM-DD")
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--only", required=True, help="the sub-test: a feed, or a Monte Carlo test")
    ap.add_argument("--set", action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()
    got = RUNS[a.study](a)
    got["only"] = a.only
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}_{re.sub(r'[^A-Za-z0-9.-]+', '-', a.only)}"
    out = home(a.project, a.databank, a.study, a.strategy) / "parciales" / stamp
    path = output.member(out, got, f"{a.study} — {a.strategy} — solo {a.only}")
    print(f"-> {path}")


if __name__ == "__main__":
    main()

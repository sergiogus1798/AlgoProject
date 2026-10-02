#!/usr/bin/env python3
"""The command: where on the market-state grid one strategy earns, if anywhere in particular."""

import argparse
from pathlib import Path

from core.study import output
from core.study.render import markdown
from studies.readings.conditionalMap import inputs, one


def main() -> None:
    """Read one strategy's entries against its regime at the time, print it, write it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--harvest", required=True, type=Path,
                    help="a harvest day folder, e.g. AlgoData/harvest/<project>/<databank>/<day>")
    ap.add_argument("--strategy", required=True, help="its name as the harvest spells it")
    ap.add_argument("--set", dest="overrides",
                    action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    got = one.run(a.strategy, a.harvest, cfg)
    run = cfg["run"]
    title = f"Mapa condicional — {a.strategy}"
    lede = ("⚠️ Descriptivo, no un filtro: con varios cortes alguna celda sale significativa "
            "por azar en cualquier estrategia, incluida una sin ninguna ventaja "
            f"(PDF del dueño, item 6). Muestra {run['sample']} · {run['feed']} "
            f"{run['timeframe']} · {got['summary']['clasificadas']} de "
            f"{got['summary']['trades']} operaciones clasificadas; la muestra Completa "
            f"(build + OOS1) tiene {got['summary']['trades_completa']} y se elige en el "
            "desplegable «Muestra».")
    print(markdown.render(got, title))
    out = output.folder(a.harvest / "trades.parquet", "conditionalMap")
    print(f"-> {output.member(out, got, title, lede)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The command: whether one strategy's entry carries information, and what arriving late costs."""

import argparse
from pathlib import Path

from core.study import output
from core.study.render import markdown
from studies.readings.entryQuality import inputs, one


def main() -> None:
    """Read one strategy's entries against the bars, print what they were worth, write it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path, help="a trades.parquet")
    ap.add_argument("--strategy", required=True, help="its name as the export spells it")
    ap.add_argument("--set", dest="overrides",
                    action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    got = one.run(a.strategy, a.export, cfg)
    run = cfg["run"]
    title = f"Calidad de la entrada — {a.strategy}"
    lede = (f"Muestra {run['sample']} · {run['feed']} {run['timeframe']} · "
            f"{got['summary']['full_path']} de {got['summary']['trades']} operaciones con "
            f"camino completo.")
    print(markdown.render(got, title))
    print(f"-> {output.member(output.folder(a.export, 'entryQuality'), got, title, lede)}")


if __name__ == "__main__":
    main()

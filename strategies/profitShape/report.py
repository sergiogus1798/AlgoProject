#!/usr/bin/env python3
"""The command: how few trades, how few periods and which stretch one strategy's result rests on."""

import argparse
from pathlib import Path

from core.study import output
from core.study.render import markdown
from strategies.profitShape import inputs, one


def main() -> None:
    """Read one strategy's trade list, print what its result rests on, and write it down."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path, help="a trades.parquet")
    ap.add_argument("--strategy", required=True, help="its name as the export spells it")
    ap.add_argument("--set", dest="overrides",
                    action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    got = one.run(a.strategy, a.export, cfg)
    title = f"Forma del beneficio — {a.strategy}"
    print(markdown.render(got, title))
    path = output.member(output.folder(a.export, "profitShape"), got, title,
                         f"Muestra {cfg['run']['sample']}, {got['summary']['trades']} "
                         f"operaciones: de qué pocas cosas depende el resultado.")
    print(f"-> {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The command: every mother across timeframes, scaled and not, with what each cell means."""

import argparse
import sys
from pathlib import Path

from core.study import output, verdicts
from core.study.render import markdown
from strategies.crossTF import inputs, many


def main() -> None:
    """Measure every cell of the matrix, print what each scaled one means, and write it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path,
                    help="trades.parquet from sqx/export/export_retest.py")
    ap.add_argument("--scaling", required=True, type=Path,
                    help="scaling.parquet from sqx.variants.scale")
    ap.add_argument("--feed", help="SQX symbol the cells were run on; overrides run.feed, "
                    "which is only a default and belongs to whichever asset was studied last")
    ap.add_argument("--out", type=Path, help="also write every cell here as Parquet")
    ap.add_argument("--set", dest="overrides",
                    action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    feed = a.feed or cfg["run"]["feed"]
    got = many.run(many.load(a.export, a.scaling, feed, cfg), cfg)
    title = f"Cross-timeframe — {feed}"
    print(markdown.render(got["population"], title))
    out = output.folder(a.export, "crossTF")
    output.population(out, "crossTF", got["population"], title)
    got["panel"].to_parquet(out / "cells.parquet", index=False)
    verdicts.write(out, got["table"], a.export, " ".join(sys.argv), a.overrides)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        got["panel"].to_parquet(a.out, index=False)
    print(f"-> {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The command: every mother across timeframes, scaled and not, with what each cell means."""

import argparse
import sys
from datetime import date
from pathlib import Path

from core.assetdata import load
from core.datapaths import crosstf_dir
from core.paths import export_dir
from core.study import output, verdicts
from core.study.render import markdown
from studies.transfer.crossTF import inputs, many


def main() -> None:
    """Measure every cell of the matrix, print what each scaled one means, and write it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", default="CrossTF", help="the databank export_retest exported")
    ap.add_argument("--asset", required=True, help="base asset, e.g. USDJPY; its feed is the one "
                                                   "the cells ran on")
    ap.add_argument("--day", default=date.today().isoformat(), help="export date, YYYY-MM-DD")
    ap.add_argument("--fabricated", help="date sqx.variants.scale wrote the siblings; --day "
                                         "when absent")
    ap.add_argument("--out", type=Path, help="also write every cell here as Parquet")
    ap.add_argument("--set", dest="overrides",
                    action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    feed = load(a.asset)["sqx_symbol"]
    export = export_dir(a.project, a.databank, a.day) / "trades.parquet"
    scaling = crosstf_dir(a.project, a.fabricated or a.day) / "scaling.parquet"
    got = many.run(many.load(export, scaling, feed, cfg), cfg)
    title = f"Cross-timeframe — {feed}"
    print(markdown.render(got["population"], title))
    out = output.folder(export, "crossTF")
    output.population(out, "crossTF", got["population"], title)
    got["panel"].to_parquet(out / "cells.parquet", index=False)
    verdicts.write(out, got["table"], export, " ".join(sys.argv), a.overrides)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        got["panel"].to_parquet(a.out, index=False)
    print(f"-> {out}")


if __name__ == "__main__":
    main()

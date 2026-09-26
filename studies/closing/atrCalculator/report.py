#!/usr/bin/env python3
"""Read an ATR stop loss from the MAE of the IS winners, four percentiles side by side, and what SQX says it costs."""

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from core.paths import report_dir
from core.study import output, result as envelope, verdicts
from core.study.render import markdown
from studies.closing.atrCalculator import grid, inputs, load, one


def main() -> None:
    """§2 on every strategy (or one), writing stopgrid.csv; with --work, the SQX tabs too."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, nargs="+",
                    help="one or more databanks: the three WFC legs of a retest, or one export "
                         "that already spans IS, oos1 and oos2")
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--symbol", required=True, help="asset file name, e.g. XAUUSD")
    ap.add_argument("--timeframe", required=True, help="the strategy's timeframe, e.g. M30")
    ap.add_argument("--strategy", default="", help="one strategy; every one when omitted")
    ap.add_argument("--work", type=Path,
                    help="the stop-loss batch the exports came from (sqx.variants.stopgrid); "
                         "adds the proofs and SQX's cost and stability")
    ap.add_argument("--set", action="extend", nargs="+", default=[], metavar="section.key=value")
    args = ap.parse_args()

    cfg = inputs.config(args.set)
    got = load.load(args.project, args.databank, args.feed, args.symbol, args.timeframe,
                    args.work, cfg)
    out = (args.work / "estudios" / "atrCalculator" if args.work else
           report_dir(args.project, args.databank[0], date.today().isoformat()) / "atrCalculator")
    names = [args.strategy] if args.strategy else got["strategies"]
    rows, grids = [], []
    for i, name in enumerate(names, 1):
        result = one.run(name, got, cfg)
        grids.append(result.pop("grid"))
        output.member(out, result, f"Stop loss ATR — {name}")
        rows.append({"strategy": name, "identity": result["identity"], "verdict": "info",
                     **result["summary"]})
        envelope.progress(100 * i // len(names), name)
        print(markdown.render(result, f"Stop loss ATR — {name}"))
    stopgrid = pd.concat(grids, ignore_index=True)
    stopgrid.to_csv(out / grid.FILE, index=False)
    verdicts.write(out, pd.DataFrame(rows), got["packed"][0], " ".join(sys.argv), args.set)
    print(f"-> {out / grid.FILE}  ({len(stopgrid)} X para sqx.variants.stopgrid --grid)")
    print(f"-> {out / 'verdict.csv'}")


if __name__ == "__main__":
    main()

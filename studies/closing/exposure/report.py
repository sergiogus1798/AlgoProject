#!/usr/bin/env python3
"""Every strategy of one export against buy and hold, priced in the market time it spent."""

import argparse
import sys
from datetime import date

from core.paths import report_dir
from core.study import output, verdicts
from core.study.render import markdown
from studies.closing.exposure import inputs, load, many, one


def main() -> None:
    """Measure one strategy, or every strategy of one export, against buy and hold."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--symbol", required=True, help="asset file name, e.g. XAUUSD")
    ap.add_argument("--strategy", default="", help="one strategy; every one when omitted")
    ap.add_argument("--set", action="extend", nargs="+", default=[], metavar="section.key=value")
    args = ap.parse_args()

    cfg = inputs.config(args.set)
    got = load.load(args.project, args.databank, args.feed, args.symbol, cfg)
    out = report_dir(args.project, args.databank, date.today().isoformat()) / "exposure"
    # One strategy writes only its own files: a single look must never overwrite the table
    # of the whole population that ran the same day.
    if args.strategy:
        result = one.run(args.strategy, got, cfg)
        title = f"Exposición — {args.strategy}"
        print(markdown.render(result, title))
        print(f"-> {output.member(out, result, title)}")
        return
    found = many.run(got, cfg)
    for m in found["members"]:
        output.member(out, m, f"Exposición — {m['strategy']}")
    output.population(out, "exposure", found["population"],
                      f"Exposición — {args.project} / {args.databank}")
    verdicts.write(out, found["table"], got["packed"], " ".join(sys.argv), args.set)
    print(markdown.render(found["population"], "Exposición"))
    print(f"-> {out / 'verdict.csv'}")


if __name__ == "__main__":
    main()

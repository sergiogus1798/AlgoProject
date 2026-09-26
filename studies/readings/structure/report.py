#!/usr/bin/env python3
"""The command: which entry condition carries each mother's edge, and whether it lives in the direction."""

import argparse
import sys
from pathlib import Path

import pandas as pd

from core.study import output, result as envelope, verdicts
from core.study.render import markdown
from studies.readings.structure import inputs, one


def main() -> None:
    """Read a retested structural batch, print each mother's reading, and write it down."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch of sqx.structural.make, run and kept")
    ap.add_argument("--project", required=True, help="the custom project it was retested in")
    ap.add_argument("--databank", required=True, nargs="+",
                    help="the legs to read, by output databank: WFC_Build WFC_OOS1")
    ap.add_argument("--feed", required=True, help="the main market's feed, e.g. USDJPY_DukasM1_the5ers")
    ap.add_argument("--symbol", required=True, help="the asset, e.g. USDJPY")
    ap.add_argument("--set", dest="overrides",
                    action="extend", nargs="+", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    got = inputs.load(a.work, a.project, a.databank, a.feed, a.symbol)
    out = a.work / "estudios" / "structure"
    names = sorted(got["plan"]["strategy"].unique())
    rows = []
    for i, name in enumerate(names, 1):
        result = one.run(name, got, cfg)
        title = f"Estructura — {name}"
        print(markdown.render(result, title))
        output.member(out, result, title, "Qué condición de entrada sostiene el filo, y si "
                      "vive en la dirección de la entrada. Diagnóstico, nunca selección.")
        rows.append({"strategy": name, "identity": result["identity"], "verdict": "info",
                     **result["summary"]})
        envelope.progress(100 * i // len(names), name)
    print(f"-> {verdicts.write(out, pd.DataFrame(rows), a.work, ' '.join(sys.argv), a.overrides)}")


if __name__ == "__main__":
    main()

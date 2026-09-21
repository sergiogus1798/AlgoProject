#!/usr/bin/env python3
"""The command: read one project's Walk-Forward Matrix export and write the report."""

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.paths import report_dir
from strategies.walkForwardMatrix import run
from strategies.walkForwardMatrix.inputs import config
from strategies.walkForwardMatrix.render import text


def main() -> None:
    """Write the report and print one verdict line per strategy."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", default="WFM",
                    help="export folder name, underscores not spaces")
    ap.add_argument("--day", help="export date; default is the most recent one")
    args = ap.parse_args()

    directory = config.export(args.project, args.databank, args.day)
    result = run.read(directory, config.load())

    out = report_dir(args.project, args.databank, date.today().isoformat())
    out.mkdir(parents=True, exist_ok=True)
    (out / "walkforwardmatrix.md").write_text(text.page(result), encoding="utf-8")
    result["cells"].to_csv(out / "cell_correlations.csv", index=False)

    for strategy, got in result["verdicts"].items():
        print(f"{strategy:22s} {got['verdict']:9s} rho={got['rho']:+.3f} "
              f"[{got['low']:+.3f}, {got['high']:+.3f}]  "
              f"celdas={got['cells']:3d}  deriva={got['share_changed']:.0%}")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()

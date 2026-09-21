#!/usr/bin/env python3
"""The command: read one project's SPP export and write the report plus each design brief."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.paths import report_dir
from strategies.sppUltra import run
from strategies.sppUltra.inputs import config, export
from strategies.sppUltra.render import text


def main() -> None:
    """Write the report and one design_brief.json per strategy."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", default="SPP_IS",
                    help="export folder name, underscores not spaces")
    ap.add_argument("--day", help="export date; default is the most recent one")
    ap.add_argument("--strategy", action="append",
                    help="repeatable; default is every strategy in the export")
    args = ap.parse_args()

    directory = config.export(args.project, args.databank, args.day)
    settings = config.load()
    names = args.strategy or export.strategies(directory)

    results = [run.read(directory, name, settings) for name in names]
    out = report_dir(args.project, args.databank, date.today().isoformat())
    out.mkdir(parents=True, exist_ok=True)
    (out / "sppultra.md").write_text(text.page(results), encoding="utf-8")

    for result in results:
        brief = run.brief(result, settings)
        safe = result["strategy"].replace(" ", "_").replace(".", "-")
        (out / f"design_brief_{safe}.json").write_text(
            json.dumps(brief, indent=2), encoding="utf-8")
        print(f"{result['strategy']:24s} {brief['verdict']:8s} "
              f"n_eff={brief['n_eff']:6,d}  "
              f"max {brief['observed_max']:.2f} vs nulo {brief['noise_max']:.2f}  "
              f"vivos={len(brief['parameters'])} congelados={len(brief['frozen'])}")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()

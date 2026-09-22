#!/usr/bin/env python3
"""The command: one design brief in, the .sqx batch and its manifest out. Never touches SQX."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core import assets, sqxfile
from sqx.variants import inputs, manifest
from sqx.variants.build import fabricate
from sqx.variants.design import plan

SQX_DIR = "sqx"


def preflight(parent: Path) -> None:
    """Say which cost overrides apply to the symbol this family trades.

    Args:
        parent: The parent `.sqx`.

    Returns:
        Nothing; it prints. Project rule 5: nothing is authored for a symbol before the
        spread and commission in force have been stated out loud. The symbol is read off
        the parent rather than given on the command line, so it cannot disagree with the
        strategy being varied.
    """
    symbol, _ = sqxfile.symbol(parent)
    print(assets.report(symbol))


def main() -> None:
    """Design one strategy's variants, fabricate them, and write the manifest."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--brief", required=True, type=Path,
                    help="design_brief_<strategy>.json from strategies.sppUltra")
    ap.add_argument("--project", required=True, help="project name, for the output path")
    ap.add_argument("--limit", type=int,
                    help="fabricate only the first N rows of the plan; the design is unchanged")
    ap.add_argument("--sample", type=int,
                    help="fabricate N rows SPREAD across the plan instead of its first N: "
                         "the controls, then evenly spaced picks from every stratum")
    ap.add_argument("--design-only", action="store_true",
                    help="write the plan and stop, without fabricating anything")
    ap.add_argument("--out", type=Path,
                    help="write here instead of the default variants/<project>/<strategy>; "
                         "the pipeline points both of its stages at one strategy's work dir")
    args = ap.parse_args()

    design = inputs.brief(args.brief)
    settings = inputs.load()
    parent = inputs.source(design)
    preflight(parent)

    table, report = plan.build(design, settings, inputs.known(design))
    out = args.out or inputs.out_dir(args.project, design["strategy"])
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "plan.csv", index=False)
    print(f"\n{design['strategy']}  verdict={design['verdict']}  "
          f"live space {report['live_space']:,} tuples, with the frozen {report['full_space']:,}")
    for name, got in report["strata"].items():
        print(f"  {name:14s} budget {got['budget']:5,d}  kept {got['kept']:5,d}")
    print(f"  {'controls':14s}              kept {report['controls']:5,d}")
    print(f"  planned {report['n']:,} of a target {design['n_target']:,} "
          f"(shortfall {report['shortfall']:,})")
    # The plan report is written whether or not fabrication follows, so `--design-only` is a
    # complete stage rather than a preview: what it leaves behind is what the next stage and
    # the pipeline ledger read.
    (out / "design.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.design_only:
        print(f"\n-> {out / 'plan.csv'}")
        return

    rows = plan.spread(table, args.sample) if args.sample else \
        table.head(args.limit) if args.limit else table
    written = fabricate.batch(rows, parent, design["strategy"], out / SQX_DIR,
                              settings["build"]["shape"])
    print(f"\nwrote {written['files']:,} .sqx as '{written['shape']}', "
          f"{written['bytes'] / 1e6:.1f} MB")

    names = ([p["name"] for p in design["parameters"]]
             + [f["name"] for f in design["frozen"]])
    _, checks = manifest.write(rows, out / SQX_DIR, names)
    # Counts for whoever chains this. The manifest says what each variant is; this says how
    # the batch as a whole came out, which is the one thing a ledger wants to record.
    (out / "build.json").write_text(
        json.dumps({"n": written["files"], "bytes": written["bytes"],
                    "shape": written["shape"]} | checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))
    print(f"\n-> {out}")
    broken = checks["missing"] or checks["unexpected"] or checks["tuple_mismatch"]
    if broken or checks["duplicate_tuples"]:
        sys.exit("the batch on disk is not the batch that was planned; do not load it")


if __name__ == "__main__":
    main()

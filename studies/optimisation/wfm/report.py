#!/usr/bin/env python3
"""The command: read one project's Walk-Forward Matrix export and write the report."""

import argparse
import sys
from datetime import date

from core.paths import report_dir
from core.study import draws, output, verdicts
from core.study.render import markdown
from ledger import steprows
from studies.optimisation.wfm import many
from studies.optimisation.wfm.inputs import config


def main() -> None:
    """Write the report and print one verdict line per strategy."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", default="WFM",
                    help="export folder name, underscores not spaces")
    ap.add_argument("--day", help="export date; default is the most recent one")
    ap.add_argument("--strategy", help="one strategy alone, as the export names it: writes "
                    "only estrategias/<name>.json, never the population's files")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    args = ap.parse_args()

    directory = config.export(args.project, args.databank, args.day)
    out = report_dir(args.project, args.databank, date.today().isoformat()) / "wfm"
    if args.strategy:
        # Only its own JSON and page, as crossTF's --strategy: verdict.csv, wfm.json and
        # cell_excess.csv are the population's, and one strategy must not replace them.
        got = many.one(directory, config.load(args.overrides), args.strategy)
        draws.merge(out, got.pop("draws", []))
        print(markdown.render(got, f"Walk-Forward Matrix — {args.strategy}"))
        print(f"-> {output.member(out, got, f'Walk-Forward Matrix — {args.strategy}')}")
        return
    got = many.run(directory, config.load(args.overrides))
    title = f"Walk-Forward Matrix — {args.project} / {args.databank}"
    output.population(out, "wfm", got["population"], title,
                      "¿Reoptimizada, gana en el tramo que nadie miró?")
    for m in got["members"]:
        output.member(out, m, f"Walk-Forward Matrix — {m['strategy']}")
    draws.save(out, got.get("draws", []))
    got["cells"].to_csv(out / "cell_excess.csv", index=False)
    verdicts.write(out, got["table"], directory, " ".join(sys.argv), args.overrides)
    for r in got["table"].itertuples():
        print(f"{r.strategy:22s} {r.verdict:8s} L1={r.l1_mediana_exceso:+10.2f}/año  "
              f"p+={r.l1_p_mas:.3f} p-={r.l1_p_menos:.3f}  L2={r.l2_delta:+10.2f}  "
              f"efectivas={r.celdas_efectivas:4.1f}  area={r.area_celdas:2d}")
    print(steprows.log_wfm(args.project, directory, len(got["table"]), " ".join(sys.argv)))
    print(markdown.render(got["population"], title))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The command: read one project's SPP export and write the report plus each design brief."""

import argparse
import json
from datetime import date

import pandas as pd

from core.paths import report_dir
from core.study import identity, output
from core.study.render import markdown
from studies.breakage.spp import one
from studies.breakage.spp.inputs import config, export

LEDE = ("Etapa 1 del protocolo de robustez: qué mueve el resultado, qué está muerto, y si la "
        "estrategia merece las 5.000 variantes.")


def main() -> None:
    """Write each strategy's page and its design_brief.json into the spp report folder."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", default="SPP_IS",
                    help="export folder name, underscores not spaces")
    ap.add_argument("--day", help="export date; default is the most recent one")
    ap.add_argument("--strategy", action="append",
                    help="repeatable; default is every strategy in the export")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[],
                    metavar="KEY=VALUE")
    args = ap.parse_args()

    directory = config.export(args.project, args.databank, args.day)
    cfg = config.load(args.overrides)
    out = report_dir(args.project, args.databank, date.today().isoformat()) / "spp"
    signed = []
    for name in args.strategy or export.strategies(directory):
        got = one.run(name, directory, cfg)
        signed.append({"strategy": name, "identity": got["identity"],
                       "brief": got["summary"]["verdict"],
                       "note": "" if got["identity"] else identity.NOTE})
        output.member(out, got, f"SPP — {name}", LEDE)
        brief = got["summary"]["brief"]
        safe = name.replace(" ", "_").replace(".", "-")
        (out / f"design_brief_{safe}.json").write_text(json.dumps(brief, indent=2),
                                                       encoding="utf-8")
        print(markdown.render(got, f"SPP — {name}"))
        print(f"{name:24s} {brief['verdict']:8s} n_eff={brief['n_eff']:6,d}  "
              f"max {brief['observed_max']:.2f} vs nulo {brief['noise_max']:.2f}  "
              f"vivos={len(brief['parameters'])} congelados={len(brief['frozen'])}")
    # The briefs are named by a mangled name; this table is what pairs the folder by identity.
    pd.DataFrame(signed).to_csv(out / "strategies.csv", index=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()

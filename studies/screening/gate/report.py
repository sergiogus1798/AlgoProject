#!/usr/bin/env python3
"""The gate over one databank: the cascade, the scorecard, and the verdict SQX can apply."""

import argparse
from datetime import date

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output
from engines.nulls import inputs as null_inputs
from studies.screening.gate import cascade, inputs, many


def main() -> None:
    """Read a databank's newest harvest, run every screen, and write what survived."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="screen.threshold=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.newest(a.project, a.databank)
    data = inputs.load(folder)
    data["null_cfg"] = null_inputs.config([f"nulls.draws={cfg['monkey']['draws']}"])
    data["bars"] = null_inputs.bars(a.feed, cfg["monkey"]["timeframe"])
    print(f"{len(data['metrics'])} emparejadas + {len(data['missing'])} sin OOS, "
          f"ventana {data['split']} -> {data['end']}\n")

    source = {"project": a.project, "databank": a.databank, "feed": a.feed,
              "harvest": str(folder), "split": data["split"], "end": data["end"],
              "missing_oos": len(data["missing"]),
              "screens": [s["name"] for s in cfg["screens"]], "overrides": a.set}
    got = many.run(data, cfg, source)
    scores, funnel = got["scores"], got["funnel"]

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "gate"
    title = f"Puerta OOS — {a.project} / {a.databank}"
    output.population(out, "gate", got["population"], title)
    for m in got["members"]:
        output.member(out, m, f"Puerta OOS — {m['strategy']}")
    scores.to_parquet(out / "scorecard.parquet", compression="zstd")
    cascade.verdict(scores, "strategy").to_csv(out / "verdict.csv", index=False)
    cascade.verdict(scores, "strategy_build").to_csv(out / "verdict_build.csv", index=False)
    funnel.to_csv(out / "funnel.csv", index=False)
    write_manifest(out, source,
                   f"python3 -m studies.screening.gate.report --project {a.project} "
                   f"--databank '{a.databank}' --feed {a.feed}",
                   {"entered": len(scores), "survives": int(scores["survives"].sum())})
    print(f"\n{int(scores['survives'].sum())} de {len(scores)} sobreviven -> {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The gate over one databank: the levels, the scorecard, and the verdict SQX can apply."""

import argparse
import shutil
from datetime import date

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import draws, output
from ledger import tried
from pipeline.autopilot import criteria, judge
from studies.screening.gate import cascade, inputs, many
from studies.screening.gate.levels import LEVELS

SEEDS = {"monkey": "mono_seed", "homogeneity": "q_seed", "drawdown": "dd_seed"}


def main() -> None:
    """Read a databank's newest harvest, run every level, and write what stands."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_M1")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    ap.add_argument("--seed", type=int, default=None,
                    help="one root for the three resamplings (R7, R6, the monkey); omitted, "
                         "each draws a fresh one. The scorecard records the ones used "
                         "(q_seed, dd_seed, mono_seed) and the manifest the --set that "
                         "replays them")
    ap.add_argument("--from-level", default="0", choices=sorted({level for level, _ in LEVELS}),
                    help="resume today's report at this level: the levels before it are "
                         "read back from its scorecard")
    a = ap.parse_args()

    sets = a.set + ([] if a.seed is None else [f"{knob}.seed={a.seed}" for knob in SEEDS])
    cfg = inputs.config(sets)
    folder = inputs.newest(a.project, a.databank)
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "gate"
    data = inputs.load(folder)
    data = inputs.staged(data, a.feed, inputs.timeframe(data["metrics"], cfg, a.set), out)
    # The judge's own rules, read as the judge reads them (smoke mode included): the cascade
    # and the cut cannot disagree.
    rules = criteria.resolved(judge.settings()["steps"]["8"].get("rules") or [],
                              judge.tags(a.project))
    print(tried.note_project_run(a.project, "studies.screening.gate", folder.name, cfg,
                                 f"gate.report --set {' '.join(a.set)}".strip()))
    print(f"{len(data['metrics'])} emparejadas + {len(data['missing'])} sin OOS, "
          f"ventana {data['split']} -> {data['end']}\n")

    source = {"project": a.project, "databank": a.databank, "feed": a.feed,
              "harvest": str(folder), "split": data["split"], "end": data["end"],
              "missing_oos": len(data["missing"]), "levels": [level for level, _ in LEVELS],
              "cascade": cfg["cascade"]["on"], "overrides": a.set}
    if a.from_level == "0":      # a whole run starts clean: no level's rows of an older seed stay
        (out / draws.FILE).unlink(missing_ok=True)
    got = many.run(data, cfg, rules, source, a.from_level)
    scores, funnel = got["scores"], got["funnel"]
    used = {knob: int(scores[column].dropna().iloc[0]) for knob, column in SEEDS.items()
            if scores[column].notna().any()}
    source["seeds"] = used

    title = f"Puerta OOS — {a.project} / {a.databank}"
    output.population(out, "gate", got["population"], title)
    # A rerun the same day lands in this same folder: the last run's strategies go first, or
    # one it no longer read would keep its old file and be read as current (autopilot facts).
    shutil.rmtree(out / "estrategias", ignore_errors=True)
    for m in got["members"]:
        output.member(out, m, f"Puerta OOS — {m['strategy']}")
    scores.to_parquet(out / "scorecard.parquet", compression="zstd")
    cascade.verdict(scores, "strategy").to_csv(out / "verdict.csv", index=False)
    cascade.verdict(scores, "strategy_build").to_csv(out / "verdict_build.csv", index=False)
    funnel.to_csv(out / "funnel.csv", index=False)
    replay = " ".join(a.set + [f"{knob}.seed={seed}" for knob, seed in used.items()])
    write_manifest(out, source,
                   f"python3 -m studies.screening.gate.report --project {a.project} "
                   f"--databank '{a.databank}' --feed {a.feed}"
                   + (f" --set {replay}" if replay else ""),
                   {"entered": len(scores), "survives": int(scores["survives"].sum())})
    print(f"\n{int(scores['survives'].sum())} de {len(scores)} siguen, semillas {used} -> {out}")


if __name__ == "__main__":
    main()

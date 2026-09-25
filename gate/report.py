#!/usr/bin/env python3
"""The gate over one databank: the cascade, the scorecard, and the verdict SQX can apply."""

import argparse
from datetime import date

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import report_dir
from gate import cascade, inputs
from nulls import inputs as null_inputs


def render(cfg: dict, source: dict, funnel: pd.DataFrame, scores: pd.DataFrame) -> str:
    """The funnel and what each screen cost, as markdown.

    Args:
        cfg: What inputs.config() returned.
        source: What the manifest records about this run.
        funnel: What cascade.run() returned.
        scores: The scorecard.

    Returns:
        The text of `resumen.md`. Every threshold that was in force is printed with the
        screen, because a funnel read without its thresholds says nothing.
    """
    why = {s["name"]: s for s in cfg["screens"]}
    lines = [f"# Puerta OOS — {source['project']} / {source['databank']}", "",
             f"Cosecha `{source['harvest']}` · ventana fuera de muestra "
             f"{source['split']} → {source['end']} · {len(scores)} estrategias entran "
             f"({source['missing_oos']} de ellas sin resultado OOS), "
             f"**{int(scores['survives'].sum())} salen**.", "",
             "| criba | tipo | entran | pasan | mueren | umbrales |", "|---|---|---|---|---|---|"]
    for row in funnel.itertuples():
        knobs = {k: v for k, v in why[row.screen].items() if k not in ("name", "kind", "why")}
        lines.append(f"| {row.screen} | {row.kind} | {row.entered} | {row.passed} | "
                     f"{row.died} | {knobs} |")
    lines += ["", "## Por qué existe cada criba", ""]
    lines += [f"- **{s['name']}** — {' '.join(s['why'].split())}" for s in cfg["screens"]]
    lines += ["", "⚠️ Los umbrales de arriba son deliberadamente laxos (2026-09-23). "
                  "Este informe dice cuánta población mata cada criba, no qué estrategia "
                  "conservar.", ""]
    return "\n".join(lines)


def main() -> None:
    """Read a databank's newest harvest, run every screen, and write what survived."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--set", action="append", default=[], help="screen.threshold=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    folder = inputs.newest(a.project, a.databank)
    data = inputs.load(folder)
    data["null_cfg"] = null_inputs.config([f"nulls.draws={cfg['monkey']['draws']}"])
    data["bars"] = null_inputs.bars(a.feed, cfg["monkey"]["timeframe"])
    print(f"{len(data['metrics'])} emparejadas + {len(data['missing'])} sin OOS, "
          f"ventana {data['split']} -> {data['end']}\n")

    scores, funnel = cascade.run(data, cfg)

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "gate"
    out.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(out / "scorecard.parquet", compression="zstd")
    cascade.verdict(scores, "strategy").to_csv(out / "verdict.csv", index=False)
    cascade.verdict(scores, "strategy_build").to_csv(out / "verdict_build.csv", index=False)
    funnel.to_csv(out / "funnel.csv", index=False)
    source = {"project": a.project, "databank": a.databank, "feed": a.feed,
              "harvest": str(folder), "split": data["split"], "end": data["end"],
              "missing_oos": len(data["missing"]),
              "screens": [s["name"] for s in cfg["screens"]], "overrides": a.set}
    (out / "resumen.md").write_text(render(cfg, source, funnel, scores), encoding="utf-8")
    write_manifest(out, source,
                   f"python3 -m gate.report --project {a.project} "
                   f"--databank '{a.databank}' --feed {a.feed}",
                   {"entered": len(scores), "survives": int(scores["survives"].sum())})
    print(f"\n{int(scores['survives'].sum())} de {len(scores)} sobreviven -> {out}")


if __name__ == "__main__":
    main()

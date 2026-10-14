#!/usr/bin/env python3
"""Nightly canary: a frozen USATEC H1 harvest of 10+1 strategies through the whole step-8 gate
without SQX; a changed verdict or number means a seam broke.

The route is the exported trades to the gate's verdict, the way `studies.screening.gate.report`
walks it, minus the ledger write and minus AlgoData: bars, costs and feed quality come from
`fixtures/canary/`. The config and the rules are frozen there too (`cfg.json`, `rules.json`), so
editing `criteria.yaml` does not fail the nightly; `--update` rewrites them and `golden.json` from
the live config. The last check is the live seam: every step-8 rule in `criteria.yaml` is still
placed in a level by `cascade.placed`.
"""

import json
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, judge
from studies.screening.gate import cascade, inputs, many

FIX = Path(__file__).resolve().parent / "fixtures/canary"
GOLDEN = FIX / "golden.json"
SEEDS = ["monkey.seed=20261014", "homogeneity.seed=20261014", "drawdown.seed=20261014",
         "monkey.draws=100000"]
CONTEXT = {"H1", "USATEC", "no_forex"}
NUMBERS = ["sanidad_value", "estaticas_value", "edge_mean_oos", "t_b", "e_fin", "retraso_ret_min",
           "retraso_t_delta", "q_p", "dd_p", "z_mono", "drift_excess_t", "trade_t"]


def live_rules() -> list[dict]:
    """The step-8 rules as `criteria.yaml` holds them today, for this market."""
    return criteria.thresholded(
        criteria.resolved(judge.settings()["steps"]["8"]["rules"], CONTEXT), 1)


def run() -> tuple[dict[str, Any], str, str]:
    """The frozen harvest through the gate: `many.run`'s result, the split and the end date."""
    cfg = json.loads((FIX / "cfg.json").read_text())
    rules = json.loads((FIX / "rules.json").read_text())
    frozen = json.loads((FIX / "inputs.json").read_text())
    data = inputs.load(FIX)
    data.update(bars=pd.read_parquet(FIX / "bars_H1.parquet"), market=frozen["market"],
                costs=frozen["costs"], costs_build=frozen["costs_build"],
                quality=FIX / "quality", feed="USATEC_M1")
    with tempfile.TemporaryDirectory() as tmp:
        data["out"] = Path(tmp)
        got = many.run(data, cfg, rules, {"harvest": "canary", "split": data["split"],
                                          "end": data["end"], "missing_oos": len(data["missing"])})
    return got, data["split"], data["end"]


def facts(text: Any) -> list[str]:
    """Fact names in a rule text, values stripped: `gate.scorecard.q_p=0.1` gives `q_p`."""
    return sorted(set(re.findall(r"gate\.scorecard\.(\w+)=", text))) if isinstance(text, str) else []


def num(value: Any) -> float | None:
    """A number rounded to 6 dp, None for NaN or missing."""
    return None if value is None or pd.isna(value) else round(float(value), 6)


def summary(scores: pd.DataFrame, funnel: pd.DataFrame, split: str, end: str) -> dict[str, Any]:
    """What the golden file holds: the funnel and each identity's verdict, fall and numbers."""
    verdict = cascade.verdict(scores, "strategy_build").set_index("identity")["verdict"]
    each = {}
    for ident, row in scores.iterrows():
        each[ident] = {"verdict": verdict.get(ident), "cayo_nivel": row["cayo_nivel"],
                       "cayo_regla": facts(row["cayo_regla"]), "limbo": facts(row["limbo"]),
                       **{k: num(row[k]) for k in NUMBERS}}
    return {"split": split, "end": end, "p_fdr_all_nan": bool(scores["p_fdr"].isna().all()),
            "funnel": funnel[["level", "screen", "entered", "limbo", "died"]].values.tolist(),
            "strategies": each}


def differences(got: Any, want: Any, path: str = "") -> list[str]:
    """Every place `got` differs from `want`; numbers by isclose, everything else exactly."""
    if isinstance(want, dict) and isinstance(got, dict):
        keys = sorted(set(want) | set(got), key=str)
        return [d for k in keys for d in differences(got.get(k, "<absent>"), want.get(k, "<absent>"),
                                                     f"{path}/{str(k)[:8]}")]
    if isinstance(want, list) and isinstance(got, list) and len(want) == len(got):
        return [d for i, (g, w) in enumerate(zip(got, want, strict=True)) for d in differences(g, w, f"{path}[{i}]")]
    if isinstance(want, float) and isinstance(got, float) and math.isclose(
            got, want, rel_tol=1e-4, abs_tol=1e-3):
        return []
    return [] if got == want else [f"{path}: got {got!r}, golden {want!r}"]


def main() -> None:
    """Compare the run with the golden, then check the live criteria still place; exit 1 on any."""
    if "--update" in sys.argv:
        (FIX / "cfg.json").write_text(json.dumps(inputs.config(SEEDS), indent=1, default=str))
        (FIX / "rules.json").write_text(json.dumps(live_rules(), indent=1, default=str))
    got, split, end = run()
    now = summary(got["scores"], got["funnel"], split, end)
    if "--update" in sys.argv:
        GOLDEN.write_text(json.dumps(now, indent=1))
        print("cfg.json, rules.json and golden.json rewritten from the live config")
        return
    want = json.loads(GOLDEN.read_text())
    diffs = differences(now, want)
    live = live_rules()
    placed = sum(len(v) for v in cascade.placed(live).values())
    if placed != len(live):
        diffs.append(f"live criteria.yaml: {len(live) - placed} of {len(live)} step-8 rules no level places")
    for line in diffs:
        print("  FAIL", line)
    print("canary:", "FAILED" if diffs else "ok", f"({len(want['strategies'])} strategies)")
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()

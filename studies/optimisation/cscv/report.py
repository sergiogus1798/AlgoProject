#!/usr/bin/env python3
"""Is the way this grid's parameters get chosen prone to overfitting? The CSCV, by rule."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from core import fanout
from core.study import output, result as envelope
from core.study.config import fingerprint
from core.surface import trials as counting
from engines.variants import look, panel
from studies.optimisation.cscv import contract
from studies.optimisation.cscv.inputs import config
from studies.optimisation.cscv.measure import cscv, rules
from studies.optimisation.cscv.verdict import cost, summary, trials

PARAM = "param_"
STEP = 18
# The CSCV cuts the whole joined curve, so every look reads all three segments — oos2 included,
# which `assets/_policy.yaml` grants it since 2026-09-27 (owner, encargo 24 Q11).
READS = panel.SEGMENTS
# Both scores run always, so the window's "Sharpe / Sortino" selector switches without a
# second call to the study (owner, 2026-09-30 §8.4; CONTRACT §1 «selectors»). The verdict and
# `cscv.json`'s flat keys stay on `cscv.score` alone — only the tabs carry the other one too.
SCORE_KEYS = ("sharpe", "sortino")

# What the rule workers read, set before the fork.
_SHARED: dict = {}


def grid_of(metrics: pd.DataFrame, columns: pd.Index) -> pd.DataFrame:
    """Each variant's parameter tuple, in the panel's own column order.

    Args:
        metrics: Contract C3.
        columns: The panel's columns, which are variant identifiers.

    Returns:
        One row per panel column. The order is load-bearing: every rule receives scores
        as a positional array and answers with a position, so a grid in a different order
        would silently name a different variant.
    """
    named = [c for c in metrics.columns if c.startswith(PARAM)]
    return metrics.set_index("variant_id")[named].reindex(columns)


def flat(name: str, found: dict) -> dict:
    """One rule's numbers under keys a threshold can name.

    Args:
        name: The rule.
        found: What `summary.everything` returned, plus the rule's measured cost.

    Returns:
        `pbo_argmax`, `slope_argmax` and so on. `pipeline/stages/verdict.py` reads
        scalars out of this file by name, and a gate that has to walk into a sub-object
        is a gate nobody adds the next one to.
    """
    return {f"{k}_{name}": v for k, v in found.items() if not isinstance(v, (dict, list))}


def _rule(key: tuple[str, str]) -> tuple[pd.DataFrame, dict]:
    """One selection rule's CSCV and its measured cost, under one score, in a worker of its own.

    Args:
        key: (a key of `rules.RULES`, a key of `SCORE_KEYS`).

    Returns:
        (its partitions, what `summary.everything` and `cost.cost` found).
    """
    name, score_key = key
    got = _SHARED
    run = cscv.run(got["wide"], got["knobs"]["blocks"], rules.RULES[name], got["grid"],
                   np.random.default_rng(got["knobs"]["seed"]), score_key)
    return run, summary.everything(run) | cost.cost(
        got["inside"], got["outside"], got["grid"], name, got["knobs"] | {"score": score_key})


def main() -> None:
    """Run the CSCV once per selection rule and write the verdict beside the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet and equity.parquet")
    ap.add_argument("--blocks", type=int,
                    help="blocks to cut the history into, overriding the ledger's 16 "
                         "(C(16,8) = 12,870 partitions); 12 gives 924, 10 gives 252")
    ap.add_argument("--family", required=True,
                    help="la familia de plantillas del lote: la tercera parte del estudio del "
                         "ledger, donde se apunta la mirada, un renglón por tramo")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()

    started = time.time()
    cfg = config.load(a.overrides)
    knobs = cfg["cscv"]
    if a.blocks:
        knobs["blocks"] = a.blocks
    score = cscv.SCORES[knobs["score"]]
    comp = panel.SHORTCUTS[cfg["split_mode"]]
    cols = panel.columns(comp)
    # A batch collected before sqx.variants.collect wrote per-segment columns (issue 67, e.g.
    # pipeline/XAUUSD/Strategy_17-9-39) has neither segments.parquet nor the "NetProfit
    # (<segment>)" / "NumberOfTrades (<segment>)" columns cols names, and would otherwise die
    # mid-run on a KeyError or a FileNotFoundError several calls deep in engines/variants. It
    # is still good for the parameter cloud (studies/optimisation/cloud), so this only skips
    # the CSCV -- never touches or re-harvests the batch.
    if not (a.work / "segments.parquet").exists():
        raise SystemExit(f"{a.work}: no segments.parquet -- predates the per-segment "
                         f"collection, so the CSCV cannot read it; re-harvest it or retire it "
                         f"(knowhow/research/cscv-always-reads-oos2.md)")
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    absent = [cols[k] for k in ("is", "oos", "trades_is", "trades_oos")
             if cols[k] not in metrics.columns]
    if absent:
        raise SystemExit(f"{a.work}: metrics.parquet has no {', '.join(absent)} -- predates "
                         f"the per-segment collection, so '{cfg['split_mode']}' cannot be "
                         f"measured; re-harvest it or retire it "
                         f"(knowhow/research/cscv-always-reads-oos2.md)")
    symbol, timeframe = look.market(a.work)
    look.admit(STEP, READS, symbol)
    print(f"PROGRESS 5 {symbol} {timeframe}: {', '.join(READS)} permitidos por el ledger",
          flush=True)
    print("PROGRESS 10 construyendo la matriz de rendimientos diarios", flush=True)
    wide = panel.usable(panel.panel(a.work, knobs["period"]), metrics, cfg["min_trades"],
                        cols)
    grid = grid_of(metrics, wide.columns)
    # The PBO itself ignores this boundary: `cscv.run` cuts the history its own way.
    # It is the four chronological numbers below -- rule cost, deflated Sharpe, trial
    # count, drift -- that are read at the split the config declares.
    inside, outside = panel.windows(wide, panel.split(symbol, comp))

    print(f"PROGRESS 20 {', '.join(knobs['rules'])}: "
          f"{len(cscv.partitions(knobs['blocks']))} particiones sobre {wide.shape[1]} "
          "variantes", flush=True)
    # The rules share nothing and each seeds its own generator, so they run side by side
    # and give exactly what they gave one after another. Every rule runs under both scores
    # (SCORE_KEYS) so the window's selector switches instantly; only `knobs["score"]`'s copy
    # feeds the verdict and `cscv.json`'s flat keys, unchanged from before this ran twice.
    _SHARED.update(wide=wide, grid=grid, inside=inside, outside=outside, knobs=knobs)
    tasks = [(name, sk) for name in knobs["rules"] for sk in SCORE_KEYS]
    done = dict(fanout.run(_rule, {t: 1 for t in tasks}, len(tasks)))
    runs_by_score = {sk: {name: done[(name, sk)][0] for name in knobs["rules"]}
                     for sk in SCORE_KEYS}
    found_by_score = {sk: {name: done[(name, sk)][1] for name in knobs["rules"]}
                      for sk in SCORE_KEYS}
    found = found_by_score[knobs["score"]]

    print("PROGRESS 80 contando cuantas pruebas independientes hay de verdad", flush=True)
    independent = counting.independent(inside, knobs["cluster_k_max"])
    best = rules.argmax(score(inside.to_numpy()), grid, None)
    deflated = trials.deflated(inside, best, independent["n_clusters"])
    moved = cost.drift(inside, outside, grid, score)

    print("PROGRESS 90 dibujando", flush=True)
    result = {"n": int(wide.shape[1]), "periods": int(wide.shape[0]),
              "period": knobs["period"], "blocks": knobs["blocks"],
              "score": knobs["score"], "partitions": len(cscv.partitions(knobs["blocks"])),
              "dsr": deflated["dsr"], "sharpe_benchmark": deflated["benchmark"],
              "n_clusters": independent["n_clusters"], "levels_max": moved["levels_max"],
              # The carry-over slope is fitted across every variant of a partition, so it
              # is a property of the surface and identical for all three rules. Stated
              # once here; the per-rule copies below are the same number three times.
              "slope": found[knobs["rules"][0]]["slope"],
              "r2": found[knobs["rules"][0]]["r2"],
              **{k: v for name in knobs["rules"] for k, v in flat(name, found[name]).items()},
              "rules": found, "trials": independent, "sharpe": deflated, "drift": moved}
    (a.work / "cscv.json").write_text(json.dumps(result, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    output.population(a.work / "estudios", "cscv", envelope.envelope(
        "studies.optimisation.cscv.report", a.work.name, None, cfg, started,
        contract.tabs(runs_by_score, found_by_score, result, knobs["score"]),
        contract.verdict(found, result),
        glossary=contract.GLOSSARY), f"CSCV — {a.work.name.replace('_', ' ')}")
    head = knobs["rules"][0]
    look.log(a.work, a.family, {
        "step": STEP, "launched_by": "cscv", "config_hash": fingerprint(cfg),
        "n_in": len(metrics), "n_out": len(metrics), "criterion": "cscv/pbo",
        "thresholds": {"blocks": knobs["blocks"], "min_trades": cfg["min_trades"]},
        "note": f"PBO {head} {found[head]['pbo']:.3f} DSR {deflated['dsr']:.3f} sobre "
                f"{wide.shape[1]} variantes · {result['periods']} periodos {knobs['period']} · "
                f"cronología {panel.label(comp)}"}, READS)

    print(f"PROGRESS 100 PBO {found[head]['pbo']:.1%} con {head}, DSR {deflated['dsr']:.2f}",
          flush=True)
    for name in knobs["rules"]:
        low, high = found[name]["ci95"]
        print(f"  {name:20s} PBO {found[name]['pbo']:6.1%}  percentil OOS "
              f"{found[name]['pct_oos']:5.1f} [{low:.0f}, {high:.0f}]  "
              f"pierde {found[name]['prob_loss']:.1%}")
    print(f"\n{wide.shape[1]} variantes que valen {independent['n_clusters']} pruebas "
          f"independientes; el orden se conserva con pendiente {result['slope']:+.2f}")
    print(f"-> {a.work / 'estudios' / 'cscv.html'}")


if __name__ == "__main__":
    main()

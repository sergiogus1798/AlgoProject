#!/usr/bin/env python3
"""The command: how small an edge the market profile can see — planted, tested, and widened."""

import argparse
import json
import os
import time

import pandas as pd

from core import assetdata, fanout, manifest
from core.researchpaths import research_profiles_dir
from core.study import output, result
from core.study.config import fingerprint
from studies.research.marketProfile import ledgerrows as profile_ledger
from studies.research.memory.sources import CONFIG as MEMORY
from studies.research.profilePower import (analytic, contract, inputs, ledgerrows, many, one,
                                            store)

STATE = {}
TITLE = "Potencia del perfil de mercado"
LEDE = ("Qué tamaño de edge ve el perfil: se planta uno conocido en copias sin dirección de "
        "las barras de build y se le pasa la misma prueba, con la misma nula y los mismos "
        "sorteos.")
LEVELS = [1, 2, 5]
HIT = ("inside", "engulfing", "run")    # the profile's measures judged by a hit rate, not a t
EVERY = 100     # replications between two writes of runs.parquet


def replication(key: tuple) -> dict:
    """One replication, from the bars the parent loaded before forking."""
    cell = key[:2]
    return one.run(key, STATE["bars"][cell], assetdata.load(key[0]), STATE["cfg"])


def measure(cfg: dict, force: bool) -> tuple[pd.DataFrame, int]:
    """Run the replications not stored yet; returns every one under this cut, and how many ran.

    The fan-out is cut to `run.budget_bytes`; runs.parquet is rewritten every EVERY rows, so
    a run that is stopped keeps what it finished.
    """
    cut, draws, how = cfg["judge"]["cut"], cfg["profile"]["nulls"]["draws"], cfg["plant"]["how"]
    old = store.runs(cut, draws)
    done = set() if force else set(map(tuple, old[store.KEY].to_numpy()))
    keys = [(s, t, m, d, float(e), r) for s, t in inputs.cells(cfg)
            for m in cfg["plant"]["measures"] for d in cfg["plant"]["directions"]
            for e in cfg["plant"]["effects"] for r in range(cfg["plant"]["replications"])]
    todo = [k for k in keys if (*k, how) not in done]
    STATE.update(cfg=cfg, bars={c: inputs.bars(*c) for c in {k[:2] for k in todo}})
    costs = {k: len(STATE["bars"][k[:2]]) * (1 + k[4]) for k in todo}
    workers = min(cfg["run"]["workers"], cfg["run"]["budget_bytes"] // cfg["run"]["process_bytes"])
    rows = old.to_dict("records")
    for n, (key, got) in enumerate(fanout.run(replication, costs, workers), 1):
        rows.append({**got, "cut": cut, "seed": cfg["run"]["seed"]})
        if n % EVERY == 0 or n == len(todo):
            store.save(pd.DataFrame(rows))
            result.progress(90 * n // len(todo), f"{n} de {len(todo)} réplicas")
    return pd.DataFrame(rows), len(todo)


def judge(runs: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    """Every table of the study from the replications and the map on disk."""
    classes, cut, target = MEMORY["asset_class"], cfg["judge"]["cut"], cfg["judge"]["power"]
    judged = many.judged(runs[runs["how"] == cfg["plant"]["how"]], cfg)
    judged["asset_class"] = judged["symbol"].map(classes)
    by, by_class = ["family", "measure", "timeframe"], ["asset_class", "measure", "timeframe"]
    curve = many.curve(judged, by)
    profiles = research_profiles_dir()
    hit = [m["name"] for m in cfg["profile"]["measures"] if m["fn"] in HIT]
    wide = analytic.widened(pd.read_csv(profiles / "measures.csv"),
                            pd.read_csv(profiles / "context.csv"), classes, cut, target, hit)
    return {"runs_judged": judged, "curve": curve, "mde": many.minimum(curve, by, target),
            "curve_class": many.curve(judged, by_class),
            "mde_class": many.minimum(many.curve(judged, by_class), by_class, target),
            "calibration": analytic.calibrated(judged, cut, hit), "widened": wide,
            "reach": analytic.reachable(wide, ["family", "timeframe"], LEVELS),
            "reach_class": analytic.reachable(wide, ["asset_class", "timeframe"], LEVELS)}


def main() -> None:
    """Run the replications asked for, judge every one stored, print and write the tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge-only", action="store_true", help="no replications, only the tables")
    ap.add_argument("--force", action="store_true", help="run again what is already stored")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[],
                    metavar="KEY=VALUE")
    a = ap.parse_args()
    started = time.time()
    os.nice(19)
    cfg = inputs.config(a.overrides)
    if a.judge_only:
        runs, fresh = store.runs(cfg["judge"]["cut"], cfg["profile"]["nulls"]["draws"]), 0
    else:
        runs, fresh = measure(cfg, a.force)
    tables = judge(runs, cfg)
    judged = tables.pop("runs_judged")
    out = store.write(tables)
    if fresh:
        new = judged[judged["seed"] == cfg["run"]["seed"]]
        profile_ledger.append(out / "ledger.jsonl", ledgerrows.rows(new, cfg))
    output.population(out, "power", contract.build(tables, cfg, started), TITLE, LEDE)
    (out / "run.json").write_text(json.dumps({
        "code_version": manifest.code_version(), "config_hash": fingerprint(cfg),
        "seed": cfg["run"]["seed"], "cut": cfg["judge"]["cut"], "replications": len(judged),
        "fresh": fresh, "core_hours": round(float(judged["wall_s"].sum()) / 3600, 2),
        "wall_s": round(time.time() - started, 1)}, indent=1), encoding="utf-8")
    result.progress(100, "hecho")
    pd.set_option("display.width", 220)
    print(f"\n{len(judged)} réplicas ({judged['wall_s'].sum() / 3600:.1f} horas de núcleo), "
          f"corte p ≤ {cfg['judge']['cut']:.5f}\n")
    print(tables["mde"].round(3).to_string(index=False))
    print("\nLo que el mapa entero puede ver (aproximación normal):")
    print(tables["reach"].round(3).to_string(index=False))
    print(f"-> {out}")


if __name__ == "__main__":
    main()

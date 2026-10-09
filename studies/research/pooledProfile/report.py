#!/usr/bin/env python3
"""The command: the market profile's measures judged per group of assets, jointly resampled."""

import argparse
import json
import os
import time

import pandas as pd

from core import assetdata, fanout, manifest
from core.study import output, result
from core.study.config import fingerprint
from studies.research.board import store as board_store
from studies.research.marketProfile import ledgerrows as profile_ledger
from studies.research.pooledProfile import contract, inputs, ledgerrows, many, one, store

STATE = {}
TITLE = "Perfil agrupado"
LEDE = ("Las medidas del perfil de mercado juzgadas por grupo (clase de activo, marco, "
        "dirección y medida): un estadístico combinado contra una nula que remuestrea los "
        "activos a la vez en el tiempo, y el efecto de cada activo encogido hacia su grupo.")


def asset(key: tuple) -> dict:
    """One asset of one group on one timeframe, measured and written to its own files."""
    group, timeframe, symbol = key
    got = one.run(symbol, group, timeframe, STATE["bars"][group][timeframe][symbol],
                  assetdata.load(symbol), STATE["cfg"])
    store.save(group, timeframe, symbol, got)
    return {"wall_s": got["wall_s"]}


def measure(cfg: dict, force: bool) -> int:
    """Measure every asset of every group not stored yet; returns how many were measured."""
    groups, frames = inputs.groups(cfg), cfg["run"]["timeframes"]
    STATE.update(cfg=cfg, bars={g: inputs.bars(s, frames) for g, s in groups.items()})
    costs = {(g, t, s): len(STATE["bars"][g][t][s]) for g, names in groups.items()
             for t in frames for s in names
             if force or not store.stem(g, t, s).with_suffix(".parquet").exists()}
    for n, (key, got) in enumerate(fanout.run(asset, costs, cfg["run"]["workers"]), 1):
        result.progress(90 * n // len(costs), f"{' '.join(key)}: {got['wall_s']:.0f} s")
    return len(costs)


def judge(cfg: dict) -> tuple[dict, dict]:
    """Every group's cell judged together; also each cell's shared window, for the ledger."""
    cells, windows = [], {}
    for group, symbols in inputs.groups(cfg).items():
        for timeframe in cfg["run"]["timeframes"]:
            rows, sims = store.load(group, timeframe, symbols)
            if sims.nbytes > cfg["run"]["budget_bytes"]:
                raise MemoryError(f"{group} {timeframe}: {sims.nbytes} bytes of null draws, "
                                  f"budget {cfg['run']['budget_bytes']}")
            cells.append(many.cell(rows, sims, cfg))
            windows[(group, timeframe)] = (rows[0]["first_bar"].iloc[0], rows[0]["last_bar"].iloc[0])
    board = board_store.board_dir() / "board.json"
    inside = {(c["symbol"], c["timeframe"], c["direction"], c["family"])
              for c in board_store.read(board)["cells"]} if board.exists() else set()
    return many.run(cells, cfg, inside), windows


def main() -> None:
    """Measure what is missing, judge every group, print and write the tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge-only", action="store_true", help="no measuring, only the tables")
    ap.add_argument("--force", action="store_true", help="measure again, with a new seed")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[],
                    metavar="KEY=VALUE")
    a = ap.parse_args()
    started = time.time()
    os.nice(19)
    cfg = inputs.config(a.overrides)
    cfg["run"]["seed"] = store.seed(cfg["run"]["seed"], a.force)
    fresh = 0 if a.judge_only else measure(cfg, a.force)
    judged, windows = judge(cfg)
    tests, cells, fake = judged["tests"], judged["board"], judged["placebo"]
    out = store.write({k: judged[k] for k in ("tests", "assets", "board")})
    if fresh:
        profile_ledger.append(out / "ledger.jsonl", ledgerrows.rows(tests, cfg, windows))
    got = contract.build(judged, cfg, started)
    output.population(out, "pooled", got, TITLE, LEDE)
    (out / "run.json").write_text(json.dumps({
        "code_version": manifest.code_version(), "config_hash": fingerprint(cfg),
        "seed": cfg["run"]["seed"], "measured": fresh, **got["summary"],
        "windows": {" ".join(k): v for k, v in windows.items()},
        "wall_s": round(time.time() - started, 1)}, indent=1), encoding="utf-8")
    result.progress(100, "hecho")
    pd.set_option("display.width", 220)
    named = tests[tests["significant"]].sort_values("q")
    print(f"\n{len(named)} de {len(tests)} pruebas de grupo pasan (BH al "
          f"{cfg['judge']['alpha']:.0%}); en mundos sin nada el procedimiento nombra algo el "
          f"{fake['any_named']:.1%} de las veces ({fake['worlds']} placebos)\n")
    print(named[contract.TESTS].round(4).to_string(index=False))
    print(f"\nCeldas-familia que traerían: {len(cells)} (vía amplia), "
          f"{int(cells['strict'].sum())} (vía estricta); nuevas en el tablero: "
          f"{int(cells['new'].sum())} y {int((cells['new'] & cells['strict']).sum())}; "
          f"{int(cells['alone'].sum())} ya pasaban solas la significancia")
    print(f"-> {out}")


if __name__ == "__main__":
    main()

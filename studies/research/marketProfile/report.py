#!/usr/bin/env python3
"""The command: the market profile of every asset on its build segment, measured and judged."""

import argparse
import json
import time
from datetime import datetime

import pandas as pd

from core import assetdata, fanout, manifest
from core.researchpaths import research_profiles_dir
from core.study import output, result
from core.study.config import fingerprint
from studies.research.marketProfile import (bibliography, contract, familias, favourable,
                                             favourablemd, inputs, ledgerrows, many, one, store,
                                             sweep, sweepjudge, variance)

STATE = {}
TITLE = "Perfil de mercado"
LEDE = ("Qué familia de comportamiento hay en cada activo, marco y dirección, medida sólo en "
        "el tramo build y contra la misma serie remuestreada por bloques.")


def measure(symbol: str) -> dict:
    """One asset on every timeframe, written to its own file.

    Returns:
        {"status": "ok", "bars": {timeframe: n}, "wall_s": {timeframe: s}, "from", "to"}, or
        a status saying why the asset was skipped: no build window, or a feed being rewritten.
    """
    cfg = STATE["cfg"]
    try:
        lo, hi = inputs.span(symbol)
    except ValueError as error:
        return {"status": f"sin tramo build: {error}"}
    m1 = inputs.minute_bars(symbol, cfg["run"]["fresh_minutes"])
    if m1 is None:
        return {"status": "feed modificado hace poco o durante la lectura"}
    asset, got, bars = assetdata.load(symbol), [], {}
    for timeframe in cfg["run"]["timeframes"]:
        frame = inputs.bars(m1, timeframe)
        bars[timeframe] = len(frame)
        got.append(one.run(symbol, timeframe, frame, asset, cfg))
    walls = {g["context"]["timeframe"]: round(g["wall_s"], 1) for g in got}
    store.save(symbol, got, {
        "symbol": symbol, "build_from": str(lo), "build_to": str(hi), "wall_s": walls,
        "first_bar": str(m1.index[0]), "last_bar": str(m1.index[-1]), "bars": bars,
        "seed": cfg["nulls"]["seed"], "config_hash": fingerprint(cfg),
        "computed_at": datetime.now().isoformat("T", "seconds")})
    return {"status": "ok", "bars": bars, "wall_s": walls, "from": str(m1.index[0]),
            "to": str(m1.index[-1])}


def sweep_cell(key: tuple) -> pd.DataFrame:
    """One cell of the sweep, from the bars the parent loaded before forking."""
    symbol, timeframe = key
    return sweep.run(symbol, timeframe, STATE["bars"][key], assetdata.load(symbol), STATE["cfg"])


RAW = ["symbol", "timeframe", "direction", "family", "entry", "param", "exit", "measure", "stat",
       "null_mean", "null_sd", "z", "n_trades", "effect", "cost", "multiple", "years",
       "years_with_sign", "per_year", "trades_per_year", "wall_s"]


def sweep_all(cfg: dict, symbols: list[str], judge_only: bool) -> None:
    """The exit and parameter sweep on every cell, judged apart from the map, in `sweep/`.

    With `judge_only` nothing is measured: the stored variants are judged again.
    """
    out = research_profiles_dir() / "sweep"
    out.mkdir(parents=True, exist_ok=True)
    if judge_only:
        old = pd.read_parquet(out / "variants.parquet")
        return sweep_write(old[RAW].assign(p=old.get("p_empirical", old["p"])), cfg, False)
    STATE.update(cfg=cfg, bars={})
    for symbol in symbols:
        m1 = inputs.minute_bars(symbol, 0)
        for timeframe in cfg["run"]["timeframes"]:
            STATE["bars"][(symbol, timeframe)] = inputs.bars(m1, timeframe)
    costs = {k: len(v) for k, v in STATE["bars"].items()}
    parts = []
    for n, (key, got) in enumerate(fanout.run(sweep_cell, costs, cfg["sweep"]["workers"]), 1):
        parts.append(got)
        result.progress(95 * n // len(costs), f"{key[0]} {key[1]}: {got['wall_s'].iloc[0]:.0f} s")
    sweep_write(pd.concat(parts, ignore_index=True), cfg, True)


def sweep_write(rows: pd.DataFrame, cfg: dict, ledger: bool) -> None:
    """Judge the sweep's variant rows and write its tables; its ledger rows when just measured."""
    out = research_profiles_dir() / "sweep"
    variants = sweepjudge.judged(rows, cfg)
    top = sweepjudge.best(variants)
    variants.to_parquet(out / "variants.parquet", index=False)
    top.to_csv(out / "best.csv", index=False)
    table = sweepjudge.counts(top, pd.read_csv(research_profiles_dir() / "scores.csv"))
    table.to_csv(out / "counts.csv")
    if ledger:
        ledgerrows.append(out / "ledger.jsonl", ledgerrows.rows(variants.assign(
            measure="sweep/" + variants["measure"]), cfg))
    print(sweepjudge.summary(variants))
    print(table.to_string())
    print(f"-> {out}: variants.parquet, best.csv, counts.csv, ledger.jsonl")


def familias_document(cfg: dict) -> None:
    """Write `assets/FAMILIAS.md` from the judged map, the sweep and the variance ratios."""
    out = research_profiles_dir()
    if not (out / "variance_ratio.csv").exists():
        variance.table(assetdata.symbols(), cfg["run"]["timeframes"]).to_csv(
            out / "variance_ratio.csv", index=False)
    familias.TARGET.write_text(familias.document(out, cfg), encoding="utf-8")
    print(f"-> {familias.TARGET}")


def favourable_tables() -> None:
    """Print the tables of `assets/FAMILIAS.md` from the map on disk and write them beside it."""
    out = research_profiles_dir()
    scores, measures = pd.read_csv(out / "scores.csv"), pd.read_csv(out / "measures.csv")
    favourable.ranked(scores).to_csv(out / "favourable.csv", index=False)
    favourable.avoided(scores).to_csv(out / "avoid.csv", index=False)
    favourable.by_timeframe(scores).to_csv(out / "by_timeframe.csv", index=False)
    favourable.clocked(measures).to_csv(out / "clock.csv", index=False)
    print(favourablemd.markdown(scores, measures))
    print(f"-> {out}: favourable.csv, avoid.csv, by_timeframe.csv, clock.csv")


def main() -> None:
    """Measure the assets asked for, then judge every asset measured so far together."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="+", default=assetdata.symbols())
    ap.add_argument("--force", action="store_true", help="measure again what is already stored")
    ap.add_argument("--judge-only", action="store_true", help="no measuring, only the tables")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[],
                    metavar="KEY=VALUE")
    ap.add_argument("--favourable", action="store_true",
                    help="only the ranked families per asset, from the map already judged")
    ap.add_argument("--bibliography", action="store_true",
                    help="only the literature file's entries beside what the map measured")
    ap.add_argument("--sweep", action="store_true",
                    help="the exit and parameter sweep, a separate study written to sweep/")
    ap.add_argument("--familias", action="store_true",
                    help="only rewrite assets/FAMILIAS.md from the map, the sweep and the prior")
    a = ap.parse_args()
    if a.familias:
        return familias_document(inputs.config(a.overrides))
    if a.sweep:
        return sweep_all(inputs.config(a.overrides), a.symbols, a.judge_only)
    if a.favourable:
        return favourable_tables()
    if a.bibliography:
        measures = pd.read_csv(research_profiles_dir() / "measures.csv")
        return print(bibliography.markdown(measures, inputs.config(a.overrides)))
    started = time.time()
    cfg = inputs.config(a.overrides)
    STATE["cfg"] = cfg
    todo = [] if a.judge_only else [s for s in a.symbols if a.force or s not in store.done()]
    status = {}
    for k, (symbol, got) in enumerate(fanout.run(measure, {s: 1 for s in todo},
                                                 cfg["run"]["workers"]), 1):
        status[symbol] = got
        result.progress(90 * k // len(todo), f"{symbol}: {got['status']} {got.get('wall_s', '')}")
    stored = store.load()
    judged = many.run(stored["rows"], cfg)
    out = store.write(judged, stored)
    measured = [s for s, g in status.items() if g["status"] == "ok"]
    fresh = judged["measures"][judged["measures"]["symbol"].isin(measured)]
    ledgerrows.append(out / "ledger.jsonl", ledgerrows.rows(fresh, cfg))
    got = contract.build(judged, stored["context"], cfg, started)
    output.population(out, "profile", got, TITLE, LEDE)
    (out / "run.json").write_text(json.dumps({
        "code_version": manifest.code_version(), "config_hash": fingerprint(cfg),
        "seed": cfg["nulls"]["seed"], "segment": inputs.SEGMENT, "status": status,
        "assets_judged": store.done(), "tests": len(judged["measures"]),
        "wall_s": round(time.time() - started, 1)}, indent=1), encoding="utf-8")
    result.progress(100, "hecho")
    table = judged["scores"]
    shown = table[table["passes"] | table["fragile"]].sort_values("multiple", ascending=False)
    pd.set_option("display.width", 220)
    print(f"\n{len(store.done())} activos, {len(judged['measures'])} pruebas, "
          f"{int(table['passes'].sum())} de {len(table)} celdas-familia pasan los cuatro filtros, "
          f"{int(table['fragile'].sum())} frágiles; con la corrección alternativa (por familia) "
          f"pasan {int(table['passes_family'].sum())}")
    print(shown[contract.SHOWN[:10]].round(4).to_string(index=False))
    for symbol, g in status.items():
        if g["status"] != "ok":
            print(f"SALTADO {symbol}: {g['status']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()

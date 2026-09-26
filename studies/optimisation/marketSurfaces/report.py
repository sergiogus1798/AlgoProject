#!/usr/bin/env python3
"""The market surfaces of one variant batch: one per market, compared pair by pair, and the call."""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from core import assetdata
from core.study import output, result as envelope, verdicts
from core.study.config import fingerprint
from ledger import gate, record, study
from studies.optimisation.marketSurfaces import one
from studies.optimisation.marketSurfaces.contract.tabs import short
from studies.optimisation.marketSurfaces.inputs import config, surfaces


def ledger_rows(m: dict, cfg: dict, symbol: str, family: str, command: str,
                work: Path) -> list[dict]:
    """One ledger line per segment read: how many markets and variants were looked at.

    Args:
        m: What `one.measure` returned.
        cfg: The config it ran under.
        symbol: The main asset.
        family: The template family the batch belongs to.
        command: The command line.
        work: The batch directory, named in the note.

    Returns:
        The rows as written. Nothing is removed, so n_out = n_in: the search is the
        looking itself — markets and periods are searches too, and the count of them is
        what makes a shared region interpretable afterwards.
    """
    sid = study.study_id(symbol, m["timeframe"], family)
    n = int(m["cells"]["variant_id"].nunique())
    rows = []
    for segment in cfg["segments"]:
        passed = int((m["rows"].query("segment == @segment")["state"] == "pass").sum())
        rows.append(record.log(sid, {
            "step": cfg["step"], "launched_by": command, "config_hash": fingerprint(cfg),
            "symbol": symbol, "timeframe": m["timeframe"], "segment": segment,
            "n_in": n, "n_out": n,
            "criterion": f"marketSurfaces: {len(m['order'])} mercados (principal + "
                         f"{len(m['order']) - 1} de {len(m['declared'])} declarados) x {n} "
                         f"variantes, {cfg['metric']}; {passed} pasan",
            "thresholds": {k: cfg[k] for k in ("rho_floor", "j_quantile", "min_share",
                                               "top_share", "min_trades")},
            "note": f"lote {work}; costs_provisional="
                    f"{any(m['provisional'].values())}; ausentes={m['absent']}"}))
    return rows


def main() -> None:
    """Refuse a reserved segment, measure the batch, write the result, record the look."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="el lote de variantes: segments.parquet, metrics.parquet, "
                         "equity.parquet, equity_markets.parquet")
    ap.add_argument("--family", required=True,
                    help="la familia de plantillas del lote, para la fila del ledger")
    ap.add_argument("--out", type=Path,
                    help="dónde escribir; por defecto <work>/estudios, como el WFC")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()

    started = time.time()
    cfg = config.load(a.overrides)
    symbol = assetdata.symbol_for(surfaces.main_feed(a.work)[0])
    for segment in cfg["segments"]:
        gate.allow(cfg["step"], segment, symbol)
    envelope.progress(5, f"{symbol}: {', '.join(cfg['segments'])} permitidos por el ledger")

    m = one.measure(a.work, cfg, symbol)
    res = one.result(m, cfg, started, a.work.name)
    out = a.out or a.work / "estudios"
    output.population(out, "marketSurfaces", res,
                      f"Superficies por mercado — {a.work.name}",
                      f"{symbol} {m['timeframe']} contra {len(m['declared'])} mercados de "
                      f"_markets.yaml, tramos {', '.join(cfg['segments'])}.")
    m["pairs"].to_csv(out / "pairs.csv", index=False)
    m["checks"].to_csv(out / "checks.csv", index=False)
    command = " ".join(sys.argv)
    verdicts.write(out, pd.DataFrame([{"strategy": a.work.name, "identity": None,
                                       "verdict": res["summary"]["call"]}]),
                   a.work, command, a.overrides)
    ledger_rows(m, cfg, symbol, a.family, command, a.work.resolve())

    envelope.progress(100, f"{res['verdict']['label']} — {res['summary']['passed']}")
    for w in res["warnings"]:
        print(f"[{w['state']}] {w['text']}")
    shown = m["rows"][["segment", "market", "n_eff", "rho", "rho_lo", "rho_hi", "rho_neutral",
                       "j", "j0", "j_hi", "origin_pct", "state"]].assign(market=lambda f: f["market"].map(short))
    print(shown.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\n{res['verdict']['meaning']}\n-> {out / 'marketSurfaces.html'}")


if __name__ == "__main__":
    main()

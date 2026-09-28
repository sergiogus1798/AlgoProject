#!/usr/bin/env python3
"""The walk forward correlation of one strategy's parameter grid, as a result and a verdict."""

import argparse
import json
import shutil
import time
from pathlib import Path

import pandas as pd

from core.study import output, result as envelope
from core.study.config import fingerprint
from engines.variants import look, panel
from studies.optimisation.wfc.contract import wfc
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import correlation

MODULE = "studies.optimisation.wfc"
STEP = 17
EXTS = ("json", "html", "md")


def chosen(a: argparse.Namespace, cfg: dict) -> tuple[tuple, tuple]:
    """The composition this run reads: the flags, a named shortcut, or config.yaml's.

    Args:
        a: The parsed command line.
        cfg: The loaded config.

    Returns:
        What `engines.variants.panel.composition` returned.
    """
    if a.inside:
        return panel.composition(a.inside.split(","), a.outside.split(","))
    return panel.SHORTCUTS[a.split or cfg["split_mode"]]


def parse() -> argparse.Namespace:
    """The command line: the batch, the family, and which composition of the split."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet (contract C3)")
    ap.add_argument("--family", required=True,
                    help="la familia de plantillas del lote: la tercera parte del estudio del "
                         "ledger, donde se apunta cada composición leída")
    ap.add_argument("--inside", help="tramos dentro de muestra: build o build,oos1")
    ap.add_argument("--outside", help="tramos fuera de muestra: lo que queda — oos1, oos2 o "
                                      "oos1,oos2 con --inside build; oos2 con build,oos1")
    ap.add_argument("--split", choices=sorted(panel.SHORTCUTS),
                    help="atajo con nombre: `oos1_oos2` = IS build, OOS oos1+oos2; "
                         "`oos2_only` = IS build+oos1, OOS oos2. Por defecto, config.yaml")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()
    if bool(a.inside) != bool(a.outside) or (a.inside and a.split):
        ap.error("--inside y --outside van juntos, y excluyen --split")
    return a


def main() -> None:
    """Ask the door, measure the grid, say what it licenses, write it and record the look."""
    a = parse()
    started = time.time()
    cfg = config.load(a.overrides)
    comp = chosen(a, cfg)
    name = panel.label(comp)
    symbol, timeframe = look.market(a.work)
    look.admit(STEP, comp[0] + comp[1], symbol)
    cols = panel.columns(comp)
    envelope.progress(20, f"{symbol} {timeframe}: IS={cols['is_label']}, "
                          f"OOS={cols['oos_label']}, permitidos por el ledger")
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    kept = panel.points(metrics, cfg["min_trades"], cols)
    dropped = len(metrics) - len(kept)
    envelope.progress(55, f"{len(kept)} puntos utiles de {len(metrics)}")
    found = correlation.correlation(kept, cols)
    said = correlation.verdict(found, cfg["rho_floor"])
    thin = json.loads((a.work / "collected.json").read_text(encoding="utf-8"))
    note = (f"{dropped} de {len(metrics)} combinaciones descartadas por operar menos de "
            f"{cfg['min_trades']} veces en alguna de las dos muestras. Antes de eso, "
            f"{thin.get('thin', 0)} variantes ya habían quedado fuera del panel por no "
            f"llegar a {thin.get('floor', '?')} operaciones en todo el periodo: una "
            f"combinación que apenas opera da un beneficio que mide una o dos operaciones.")
    title = f"WFC — {a.work.name.replace('_', ' ')} — {cols['is_label']} contra {cols['oos_label']}"
    result = envelope.envelope(MODULE, a.work.name, None, cfg, started,
                               [wfc.tab(kept, found, cols, cfg["table_ends"], note)],
                               wfc.verdict(said, found), glossary=wfc.GLOSSARY)
    # One file set per composition, so a second reading never overwrites the first; the
    # plain `wfc.*` is a copy of the newest, which the viewer and step 20 read.
    out = a.work / "estudios"
    output.population(out, f"wfc_{name}", result, title,
                      f"{cols['is_label']} contra {cols['oos_label']}.")
    for ext in EXTS:
        shutil.copyfile(out / f"wfc_{name}.{ext}", out / f"wfc.{ext}")
    # The pipeline's own contract: pipeline/stages/verdict.py reads its scalars.
    (a.work / "wfc.json").write_text(
        json.dumps({**found, **said, "dropped": dropped,
                    "dropped_thin": thin.get("thin", 0), "composition": name,
                    "in_sample": cols["is_label"], "out_of_sample": cols["oos_label"]},
                   indent=2), encoding="utf-8")
    look.log(a.work, a.family, {
        "step": STEP, "launched_by": "wfc", "config_hash": fingerprint(cfg),
        "n_in": len(metrics), "n_out": len(metrics), "criterion": f"wfc/{name}",
        "thresholds": {k: cfg[k] for k in ("rho_floor", "min_trades")},
        "note": f"{said['call']} rho {found['rho']:.3f} sobre {len(kept)} puntos"},
             comp[0] + comp[1])
    envelope.progress(100, f"rho {found['rho']:.2f} — {said['call']} ({len(kept)} puntos; "
                           f"{thin.get('thin', 0)} fuera por pocas operaciones en total, "
                           f"{dropped} por pocas en un lado); "
                           f"{len(comp[0] + comp[1])} filas en el ledger del paso {STEP}")
    print(f"\n{said['why']}\n-> {out / f'wfc_{name}.html'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The walk forward correlation of one strategy's parameter grid, as a result and a verdict."""

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from core.study import output, result as envelope
from engines.variants import panel
from studies.optimisation.wfc.contract import wfc
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import correlation

MODULE = "studies.optimisation.wfc"


def main() -> None:
    """Measure the grid, say what it licenses, and write it beside the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet (contract C3)")
    ap.add_argument("--split", choices=sorted(panel.MODES),
                    help="que se considera fuera de muestra. Por defecto, config.yaml: "
                         "`oos1_oos2` = IS build, OOS oos1+oos2; `oos2_only` = IS "
                         "build+oos1, OOS solo oos2, la lectura estricta")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()

    started = time.time()
    cfg = config.load(a.overrides)
    mode = a.split or cfg["split_mode"]
    cols = panel.columns(mode)
    envelope.progress(20, f"leyendo el panel: IS={cols['is_label']}, OOS={cols['oos_label']}")
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
    title = f"WFC — {a.work.name.replace('_', ' ')}"
    result = envelope.envelope(MODULE, a.work.name, None, cfg, started,
                               [wfc.tab(kept, found, cols, cfg["table_ends"], note)],
                               wfc.verdict(said, found))
    output.population(a.work / "estudios", "wfc", result, title,
                      f"{cols['is_label']} contra {cols['oos_label']}.")
    # The pipeline's own contract, unchanged: pipeline/stages/verdict.py reads its scalars.
    (a.work / "wfc.json").write_text(
        json.dumps({**found, **said, "dropped": dropped,
                    "dropped_thin": thin.get("thin", 0), "split_mode": mode,
                    "in_sample": cols["is_label"], "out_of_sample": cols["oos_label"]},
                   indent=2), encoding="utf-8")
    envelope.progress(100, f"rho {found['rho']:.2f} — {said['call']} ({len(kept)} puntos; "
                           f"{thin.get('thin', 0)} fuera por pocas operaciones en total, "
                           f"{dropped} por pocas en un lado)")
    print(f"\n{said['why']}\n-> {a.work / 'estudios' / 'wfc.html'}")


if __name__ == "__main__":
    main()

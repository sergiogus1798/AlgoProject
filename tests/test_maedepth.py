#!/usr/bin/env python3
"""The deep-MAE screen on trades whose MAE in ATR, duration and counterfactual are known by hand."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market import atr as sqx_atr
from studies.screening.maeDepth import inputs, many, measures


def main() -> None:
    """Fail loudly on any number that is not the one worked out on paper."""
    failures = []
    cfg = inputs.config([])
    # Flat bars: every true range is 2, so the ATR is 2 and one ATR is worth 2 at size 1, point 1.
    index = pd.date_range("2020-01-01", periods=1000, freq="30min")
    bars = pd.DataFrame({"High": 101.0, "Low": 99.0, "Close": 100.0}, index=index)
    atr = sqx_atr.sqx(bars)
    mae = [3.5, 3.2, 1, 0.5, 1.5, 4.5, 2, 0.2, 3.0, 5]
    pnl = [10, -20, 5, 5, -10, 30, 5, 5, -4, 20]
    held = [4] * 9 + [40]       # mean 7.6, sd 11.38, cut 36.06: only the last is anomalous
    at = [10 + 50 * i for i in range(10)]
    trades = pd.DataFrame({
        "Open time": index[at], "Close time": [index[a + h] for a, h in zip(at, held)],
        "Size": 1.0, "MAE ($)": [-2.0 * m for m in mae], "MFE ($)": 1.0, "Profit/Loss": pnl,
        "Close price": 100.0})
    t = measures.per_trade(trades, index, atr, 1.0)
    if not np.allclose(t["mae_atr"], mae) or t["bars"].tolist() != held:
        failures.append(f"per_trade: mae {t['mae_atr'].tolist()} bars {t['bars'].tolist()}")
    got = measures.one_segment(t, cfg)
    want = {"n": 10, "net": 46, "n_long": 1, "peor_mae": 5, "mae_p95_ganadoras": 4.85,
            "prof3_n": 5, "prof3_frac": 0.5, "prof3_n_rec": 3, "prof3_pnl_rec": 60,
            "prof3_cuota_rec": 60 / 46, "prof3_cortado_0": -20, "prof3_cortado_0.5": -25,
            "prof4_n": 2, "prof4_n_rec": 2, "prof4_cuota_rec": 50 / 46, "prof4_cortado_0": -20,
            "anom3_n": 1, "anom3_n_rec": 1, "anom3_cuota_rec": 20 / 46, "anom3_cortado_0": 20,
            "anom4_n": 1}
    bad = {k: (got[k], v) for k, v in want.items() if not np.isclose(got[k], v)}
    if bad:
        failures.append(f"one_segment (obtenido, esperado): {bad}")

    # A population of two copies, bar set at 0.3: the anomalous recovered give 0.43 of the net.
    both = pd.concat([t.assign(identity=i, segment="build") for i in ("a", "b")])
    names = pd.Series({"a": "A", "b": "B"})
    p = many.panel(both, names, {**cfg, "verdict": {"min_cuota_rec": 0.3, "action": "drop"}})
    if not (p["marcada"].all() and (p["verdict"] == "DESCARTAR").all()):
        failures.append("panel: con umbral 0,3 y drop las dos tenían que caer")
    free = many.panel(both, names, cfg)
    if free["marcada"].any() or (free["verdict"] != "MANTENER").any():
        failures.append("panel: sin umbral fijado nadie puede marcarse")
    print("FALLA\n" + "\n".join(failures) if failures else "ok: maedepth")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

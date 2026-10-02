#!/usr/bin/env python3
"""Known-answer test for studies.breakage.spp.model.combine (feedback §7, 2026-09-30):
the additive panel-1 metrics are rebuilt from their components, never summed as ratios, and
Sharpe/Sortino fall back to a pooled union when no per-permutation trades exist."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.spp.model import combine

DAY = pd.Timestamp("2024-01-01")


def _row(net: float, gp: float, gl: float, dd: float, sharpe: float, sortino: float) -> pd.Series:
    """One permutation -1 row, just the columns `combine` reads."""
    return pd.Series({"NetProfit": net, "GrossProfit": gp, "GrossLoss": gl, "Drawdown": dd,
                      "SharpeRatio": sharpe, "SortinoRatio": sortino})


def main() -> None:
    """Fail loudly if the combined metrics stop matching hand-worked arithmetic."""
    failures = []

    # --- real_combined: additive parts summed, ratios recomputed from the sums ---
    is_row = _row(net=1000.0, gp=3000.0, gl=2000.0, dd=500.0, sharpe=0.5, sortino=0.8)
    oos_row = _row(net=400.0, gp=1200.0, gl=800.0, dd=300.0, sharpe=0.7, sortino=1.1)
    got = combine.real_combined(is_row, oos_row)
    want = {"NetProfit": 1400.0, "ProfitFactor": 4200.0 / 2800.0, "Drawdown": 800.0,
            "ReturnDDRatio": 1400.0 / 800.0}
    for k, v in want.items():
        if abs(got[k] - v) > 1e-9:
            failures.append(f"real_combined[{k}] = {got[k]}, se esperaba {v}")
    # The trap this guards against: adding the two ProfitFactor ratios instead of recomputing.
    wrong_pf = (is_row["GrossProfit"] / is_row["GrossLoss"]) + (oos_row["GrossProfit"] /
                                                                oos_row["GrossLoss"])
    if abs(got["ProfitFactor"] - wrong_pf) < 1e-6:
        failures.append("real_combined sumó los dos Profit Factor en vez de recalcular")

    # --- population: paired sums, and Sharpe/Sortino as the plain union ---
    is_grid = pd.DataFrame({"NetProfit": [10.0, 20.0], "GrossProfit": [50.0, 60.0],
                            "GrossLoss": [40.0, 30.0], "Drawdown": [5.0, 8.0],
                            "SharpeRatio": [0.1, 0.2], "SortinoRatio": [0.3, 0.4]})
    oos_grid = pd.DataFrame({"NetProfit": [1.0, 2.0], "GrossProfit": [5.0, 6.0],
                             "GrossLoss": [4.0, 3.0], "Drawdown": [1.0, 2.0],
                             "SharpeRatio": [0.9, 1.0], "SortinoRatio": [0.8, 0.9]})
    pop = combine.population(is_grid, oos_grid)
    if not np.allclose(pop["NetProfit"], [11.0, 22.0]):
        failures.append(f"population[NetProfit] = {pop['NetProfit']}, se esperaba [11, 22]")
    if not np.allclose(pop["Drawdown"], [6.0, 10.0]):
        failures.append(f"population[Drawdown] = {pop['Drawdown']}, se esperaba [6, 10] (suma)")
    want_pf = [(50 + 5) / (40 + 4), (60 + 6) / (30 + 3)]
    if not np.allclose(pop["ProfitFactor"], want_pf):
        failures.append(f"population[ProfitFactor] = {pop['ProfitFactor']}, se esperaba {want_pf}")
    if len(pop["SharpeRatio"]) != len(is_grid) + len(oos_grid):
        failures.append("population[SharpeRatio] no es la unión simple de las dos rejillas")
    if not np.allclose(sorted(pop["SharpeRatio"]), sorted([0.1, 0.2, 0.9, 1.0])):
        failures.append("population[SharpeRatio] no agrupa los valores de ambas rejillas tal cual")

    # --- real_from_trades: hand-worked daily Sharpe on three days, one flat ---
    trades = pd.DataFrame({"Close time": [DAY, DAY, DAY + pd.Timedelta(days=2)],
                           "Profit/Loss": [100.0, -20.0, 50.0]})
    out = combine.real_from_trades(trades)
    daily = np.array([80.0, 0.0, 50.0])          # day 2 is flat, filled with zero
    want_sharpe = daily.mean() / daily.std(ddof=1) * np.sqrt(252)
    if abs(out["SharpeRatio"] - want_sharpe) > 1e-9:
        failures.append(f"real_from_trades[SharpeRatio] = {out['SharpeRatio']}, "
                        f"se esperaba {want_sharpe} (día intermedio en cero)")

    print("\n".join(failures) or "ok: métricas aditivas recompuestas, Sharpe/Sortino agrupados "
                                 "como unión y el Sharpe diario respeta los días sin operar")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

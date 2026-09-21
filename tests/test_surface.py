#!/usr/bin/env python3
"""Property test for core.surface on grids whose answer is known in advance — above all the
shuffled one, where the level statistics must read zero and the pairing must not."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.surface import dedupe, plateau, shift

N, SEED = 3000, 20260921


def grids(seed: int = SEED) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Four (in-sample, out-of-sample) pairs whose behaviour is decided by construction.

    Args:
        seed: Fixes every draw.

    Returns:
        Name to a pair of arrays over the same tuples, in the same order.
    """
    rng = np.random.default_rng(seed)
    base = rng.normal(1.0, 0.5, N)
    noise = rng.normal(0, 0.05, N)
    return {"identical": (base, base + noise),
            "block_drop": (base, base - 0.40 + noise),
            "shuffled": (base, rng.permutation(base)),
            "peak_collapse": (base, np.where(base > np.quantile(base, 0.90),
                                             base - 0.80, base) + noise)}


def main() -> None:
    """Fail loudly on the first property that does not hold."""
    failures, g = [], grids()

    # A surface that only picked up measurement noise: no shift, no reordering.
    before, after = g["identical"]
    if abs(shift.hodges_lehmann(before, after)) > 0.02:
        failures.append(f"identical: HL {shift.hodges_lehmann(before, after):+.3f}, se esperaba 0")
    if stats.spearmanr(before, after).statistic < 0.95:
        failures.append("identical: rho emparejado bajo, deberia ser casi 1")

    # The whole surface fell by a known amount: HL recovers it, the ranking survives.
    before, after = g["block_drop"]
    if abs(shift.hodges_lehmann(before, after) + 0.40) > 0.03:
        failures.append(f"block_drop: HL {shift.hodges_lehmann(before, after):+.3f}, se esperaba -0.40")
    if stats.spearmanr(before, after).statistic < 0.95:
        failures.append("block_drop: una caida en bloque no debe barajar el orden")
    if abs(shift.tail_excess(before, after)) > 0.05:
        failures.append("block_drop: exceso de cola no nulo en una caida uniforme")

    # THE ONE THAT MATTERS. Same histogram, random order: every level statistic reads
    # "nothing happened" and only the pairing sees the loss.
    before, after = g["shuffled"]
    if abs(shift.hodges_lehmann(before, after)) > 0.05:
        failures.append("shuffled: HL deberia ser 0 — el histograma no cambio")
    if abs(shift.cliff_delta(before, after)) > 0.05:
        failures.append("shuffled: delta de Cliff deberia ser 0 — el histograma no cambio")
    if abs(plateau.plateau_area(before) - plateau.plateau_area(after)) > 0.02:
        failures.append("shuffled: el area de meseta deberia ser identica")
    if abs(stats.spearmanr(before, after).statistic) > 0.10:
        failures.append("shuffled: rho emparejado deberia ser 0 — y es lo unico que lo ve")

    # The peak sinks while the plateau holds: the tail excess is what names it.
    before, after = g["peak_collapse"]
    # 0.20, not the 0.80 the points were dropped by: once the top decile sinks, the new
    # 95th percentile is drawn from the untouched 90%, which compresses the reading.
    if shift.tail_excess(before, after) < 0.20:
        failures.append(f"peak_collapse: exceso de cola {shift.tail_excess(before, after):.3f}, "
                        "deberia ser grande y positivo")
    if plateau.plateau_area(after) < plateau.plateau_area(before) - 0.05:
        failures.append("peak_collapse: la meseta aguanta, el area no deberia caer")

    # Inert parameters duplicate points; n_eff must count backtests, not rows.
    frame = pd.DataFrame({"NetProfit": np.repeat(np.arange(500.0), 4),
                          "NumberOfTrades": np.repeat(np.arange(500), 4),
                          "RExpectancy": 0.05})
    if dedupe.n_eff(frame) != 500:
        failures.append(f"n_eff dio {dedupe.n_eff(frame)} sobre 2000 filas de 500 backtests")

    # The sentinels are 0.08% of the grid and they win the argmax.
    poisoned = pd.concat([frame, pd.DataFrame({"NetProfit": [9e3], "NumberOfTrades": [1],
                                               "RExpectancy": [99999.0]})])
    if dedupe.drop_sentinels(poisoned)["RExpectancy"].max() > 1:
        failures.append("drop_sentinels dejo pasar el 99999 de RExpectancy")

    # A noise grid's best point must not clear its own noise threshold.
    pure = np.random.default_rng(SEED).normal(0, 1.0, N)
    if pure.max() > plateau.expected_max(pure.std(), N) * 1.15:
        failures.append("expected_max: una rejilla de ruido supero su propio umbral")
    if plateau.expected_max_sharpe(1.0, N) >= plateau.expected_max(1.0, N):
        failures.append("expected_max_sharpe deberia quedar por debajo de la cota sqrt(2 ln N)")

    # A bootstrap over tuples must bracket the value it resamples.
    low, high = dedupe.bootstrap_ci(g["identical"][0], np.median, n_resamples=999)
    if not low < np.median(g["identical"][0]) < high:
        failures.append("bootstrap_ci no contiene la mediana que remuestrea")

    print("\n".join(failures) or
          "ok: la rejilla barajada da HL 0, Cliff 0, misma meseta y rho 0 — solo el "
          "emparejamiento la ve; n_eff cuenta backtests y los centinelas no pasan")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

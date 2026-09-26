#!/usr/bin/env python3
"""The ATR stop study's inference on samples whose answer is known by construction."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.closing.atrCalculator import grid, inputs, noreturn, threshold, transfer

SEED = 11


def main() -> None:
    """Fail loudly on any reading that is not the one the sample was built to give."""
    failures = []
    cfg = inputs.config(["bootstrap.n=999"])
    rng = np.random.default_rng(SEED)

    # 1..100: numpy's linear percentile puts p90 at 90.1 and p80 at 80.2, and each interval
    # holds its X. Twenty winners give an interval wide enough to be marked unreliable;
    # two thousand from the same shape do not.
    xs = threshold.x_values(np.arange(1, 101, dtype=float), cfg)
    if not np.allclose(xs.set_index("percentile")["x"].loc[[80, 90]], [80.2, 90.1]):
        failures.append(f"threshold: X de 1..100 {xs['x'].tolist()}")
    if not ((xs["low"] <= xs["x"]) & (xs["x"] <= xs["high"])).all():
        failures.append("threshold: una X cae fuera de su propio intervalo")
    few = threshold.x_values(rng.lognormal(0, 1, 20), cfg)
    many = threshold.x_values(rng.lognormal(0, 1, 2000), cfg)
    if not few["unreliable"].iloc[-1] or many["unreliable"].any():
        failures.append("threshold: la marca poco fiable no separa 20 ganadoras de 2000")

    # Trades that went past 2 ATR against never came back and closed at -3: from there the
    # curve must read "sin retorno"; below it, where half of them won, "ruido".
    n = 400
    reach = np.where(np.arange(n) < n // 2, rng.uniform(0, 1.9, n), rng.uniform(2.1, 3, n))
    won = (np.arange(n) < n // 2) & (np.arange(n) % 2 == 0)
    final = np.where(won, 1.0, np.where(reach > 2, -3.2, -0.5))
    curve = noreturn.curve(pd.DataFrame({"mae_atr": reach, "winner": won,
                                         "result_atr": final}), cfg)
    if noreturn.zone_of(2.5, curve) != noreturn.NORETURN:
        failures.append(f"noreturn: a 2.5 ATR la zona es {noreturn.zone_of(2.5, curve)}")
    if noreturn.zone_of(1.0, curve) != noreturn.NOISE:
        failures.append(f"noreturn: a 1.0 ATR la zona es {noreturn.zone_of(1.0, curve)}")

    # The same distribution out of sample transfers; one needing 1.5x the air does not, and
    # its effective percentile falls below the intended one.
    base = rng.lognormal(0, 0.5, 3000)
    xs = threshold.x_values(base, cfg)
    same = transfer.effective(xs, rng.lognormal(0, 0.5, 3000), cfg)
    wider = transfer.effective(xs, 1.5 * rng.lognormal(0, 0.5, 3000), cfg)
    if not same["transfers"].all() or wider["transfers"].any() or (wider["gap"] >= 0).any():
        failures.append("transfer: el percentil efectivo no separa igual de 1,5 veces más aire")
    if transfer.shape(base, 1.5 * base)["median_ratio"] - 1.5 > 1e-9:
        failures.append("transfer: el cociente de medianas de x y 1,5x no es 1,5")

    rows = grid.rows("S", pd.DataFrame({"percentile": [90], "x": [2.0]}), cfg)
    if rows["x"].tolist() != [1.6, 1.8, 2.0, 2.2, 2.4]:
        failures.append(f"grid: ±20 % en dos pasos de 2.0 da {rows['x'].tolist()}")

    # Percentiles are the owner's input: as many as he wants, printed as he wrote them.
    if inputs.percentiles([95, 80, 85.0, 97.5, 80]) != [80, 85, 95, 97.5]:
        failures.append("percentiles: no ordena, no quita duplicados o no deja 85.0 como 85")
    for bad in ([], [0, 50], [50, 100]):
        try:
            inputs.percentiles(bad)
            failures.append(f"percentiles: acepta {bad}")
        except SystemExit:
            pass

    if failures:
        raise SystemExit("\n".join(failures))
    print("test_atrcalculator: ok")


if __name__ == "__main__":
    main()

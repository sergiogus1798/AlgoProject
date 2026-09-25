#!/usr/bin/env python3
"""Trade-level statistics on series whose answer is known by construction."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.entryQuality import eratio, excursion
from studies.readings.profitShape import breaks, concentration, dependence

SEED = 7


def main() -> None:
    """Check each statistic against a series built to have one right answer."""
    failures = []
    rng = np.random.default_rng(SEED)

    # One outlier carrying everything: the best 1% must own the whole profit, and the
    # trimmed expectancy must go negative.
    pnl = np.concatenate([rng.normal(-1, 10, 199), [2000.0]])
    if concentration.top_share(pnl, 0.01) < 1.0:
        failures.append("top_share no ve que una sola operación sostiene el total")
    if concentration.trimmed(pnl, [0, 5]).loc[5, "expectancy"] >= 0:
        failures.append("trimmed: quitando las 5 mejores la esperanza deberia caer bajo 0")

    # Independence: an i.i.d. sequence must not be called clustered, and a sequence of
    # blocks of five identical outcomes must be, on both the runs test and the streak.
    iid = rng.random(600) < 0.5
    blocks = np.repeat(rng.random(120) < 0.5, 5)
    if abs(dependence.runs(iid)["z"]) > 3:
        failures.append("runs: una secuencia i.i.d. sale agrupada")
    if dependence.runs(blocks)["z"] > -5:
        failures.append("runs: bloques de cinco no salen agrupados")
    if dependence.streak(blocks, 500, SEED)["p"] > 0.01:
        failures.append("streak: la racha de una secuencia en bloques deberia ser rara")
    if dependence.ljung_box(rng.normal(0, 1, 500), 10)["p"] < 0.01:
        failures.append("ljung_box: ruido blanco sale autocorrelado")

    # CUSUM: a constant mean must not reject; a mean that flips halfway must, and the
    # break must land near the real one.
    stable = rng.normal(5, 100, 600)
    broken = np.concatenate([rng.normal(40, 100, 300), rng.normal(-30, 100, 300)])
    if breaks.cusum(stable)["rejects"]:
        failures.append("cusum: una media constante sale rota")
    found = breaks.cusum(broken)
    if not found["rejects"] or abs(found["at"] - 300) > 40:
        failures.append(f"cusum: la rotura real esta en 300 y da {found['at']}")

    # The e-ratio: a path that only rises must read far above 1, and a symmetric random
    # walk must read near it. Built as bars, so highs and lows are used as in the study.
    steps = 200
    up = np.arange(steps, dtype=float)
    # Low is two below the open so the adverse excursion is non-zero: a strictly
    # monotone path would divide by zero and prove nothing about the ratio.
    frame = pd.DataFrame({"Open": up, "High": up + 1, "Low": up - 2, "Close": up},
                         index=pd.date_range("2020-01-01", periods=steps, freq="h"))
    walk = excursion.paths(frame, np.array([10]), np.array([1.0]),
                           np.array([up[10]]), 20)
    if eratio.curve(excursion.normalised(walk, np.array([1.0])))[-1] < 5:
        failures.append("e-ratio: una serie que solo sube no da un ratio alto")
    flat = np.zeros(steps)
    frame = pd.DataFrame({"Open": flat, "High": flat + 1, "Low": flat - 1, "Close": flat},
                         index=frame.index)
    walk = excursion.paths(frame, np.array([10]), np.array([1.0]), np.array([0.0]), 20)
    if abs(eratio.curve(excursion.normalised(walk, np.array([1.0])))[-1] - 1) > 0.01:
        failures.append("e-ratio: una serie simetrica deberia dar 1")

    print("\n".join(failures) or
          "ok: la concentración ve el outlier, las rachas ven los bloques, el CUSUM ve la "
          "rotura donde está y el e-ratio separa una tendencia de una serie simétrica")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

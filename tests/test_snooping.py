#!/usr/bin/env python3
"""SPA and StepM on panels whose answer is known: noise names nobody, one planted edge is named."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.inference.snooping import superior
from studies.screening.snoopingScreen import benchmark

DAYS, K, SEEDS, FWER, REPS = 1250, 50, 20, 0.05, 500


def noise(seed: int) -> pd.DataFrame:
    """K strategies with no edge, fat-tailed and sharing one common factor, as real ones do.

    Args:
        seed: Seed of the draw.

    Returns:
        DAYS rows by K columns of daily profit whose true mean is zero; the sample means
        are left as drawn, so some columns beat zero by luck, which is what the test is for.
    """
    rng = np.random.default_rng(seed)
    common = rng.standard_t(4, DAYS)[:, None]
    own = rng.standard_t(4, (DAYS, K))
    return pd.DataFrame(0.4 * common + own, columns=[f"s{i}" for i in range(K)])


def main() -> None:
    """Run the three controls and exit non-zero on any failure."""
    failures = []

    false = sum(bool(superior.stepm(noise(s), FWER, superior.block_length(noise(s)), REPS, s))
                for s in range(SEEDS))
    # Binomial(20, 0.05): four or more false families happens 1.6 % of the time.
    if false > 3:
        failures.append(f"ruido: el StepM nombra a alguien en {false} de {SEEDS} semillas")

    planted, hits = "s7", 0
    for s in range(SEEDS):
        panel = noise(s)
        panel[planted] += 0.15 * panel[planted].std()
        named = superior.stepm(panel, FWER, superior.block_length(panel), REPS, s)
        hits += planted in named
    if hits < SEEDS:
        failures.append(f"edge plantado: el StepM lo nombra en {hits} de {SEEDS}")

    rng = np.random.default_rng(0)
    moves = pd.Series(np.r_[np.nan, rng.normal(0.3, 10, DAYS)])
    panel = pd.DataFrame(rng.normal(0.5, 40, (DAYS + 1, K)))
    excess, _ = benchmark.equal_risk(panel, moves, 100.0)
    days, held = panel.iloc[1:], moves.iloc[1:]
    beats = days.mean() / days.std() > held.mean() / held.std()
    if not (beats == (excess.mean() > 0)).all():
        failures.append("igual riesgo: el signo del exceso no coincide con Sharpe > buy & hold")

    print("\n".join(failures) or
          f"ok: sobre ruido el StepM nombra a alguien en {false} de {SEEDS} semillas "
          f"(FWER {FWER}); el edge plantado sale nombrado en {hits} de {SEEDS}; y a igual "
          f"riesgo un exceso positivo es exactamente un Sharpe mayor que el del buy & hold")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regression test for the null models: block_shift must not overlap, and must move the same
calendar semester the same way in every market — the two properties the joint null rests on."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategies.crossmarket.mechanics import envelope
from strategies.crossmarket.model import trade_models

DRAWS, SEED = 200, 20260908


def synthetic(seed: int, start: str, years: int) -> tuple[pd.DataFrame, dict]:
    """A market of H1 bars with a few hundred trades on it.

    Args:
        seed: Which run.
        start: First bar, as a timestamp string — two markets starting on different dates is
            the case the calendar coupling exists for.
        years: How many years of bars.

    Returns:
        (held, market) in the shapes trade_models takes, market carrying the seed the way
        backtest.setting() puts it there.
    """
    rng = np.random.default_rng(seed)
    index = pd.date_range(start, periods=years * 24 * 250, freq="h")
    bars = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}, index=index)
    hold = rng.integers(1, 30, 300)
    gap = rng.integers(20, 300, 300)
    entry = np.cumsum(gap) + np.cumsum(hold) - hold
    entry = entry[entry + 30 < len(bars)]
    hold = hold[:len(entry)]
    held = pd.DataFrame({"entry": entry, "exit": entry + hold, "hold": hold})
    return held, {**envelope.describe(bars, held, 6), "seed": SEED}


def overlaps(entries: np.ndarray, holds: np.ndarray) -> int:
    """How many kept trades open before an earlier kept trade of the same run has closed."""
    e = np.where(holds > 0, entries, -1)
    order = np.argsort(e, axis=1)
    e, h = np.take_along_axis(e, order, 1), np.take_along_axis(holds, order, 1)
    reach = np.maximum.accumulate(np.where(h > 0, e + h, -1), axis=1)
    return int(((e[:, 1:] < reach[:, :-1]) & (h[:, 1:] > 0)).sum())


def main() -> None:
    """Fail loudly on the first property that does not hold."""
    failures = []
    late, early = synthetic(1, "2013-01-07", 9), synthetic(2, "2008-01-07", 14)
    for label, (held, market) in (("tardío", late), ("temprano", early)):
        ent, hold = trade_models.block_shift(held, market, DRAWS, np.random.default_rng(SEED))
        if overlaps(ent, hold):
            failures.append(f"block_shift {label}: {overlaps(ent, hold)} operaciones solapadas")
        if not (hold <= held["hold"].to_numpy()).all():
            failures.append(f"block_shift {label}: un hold creció al recortarlo")
        if (hold.sum(axis=1) == 0).any():
            failures.append(f"block_shift {label}: una tirada se quedó sin operaciones")

    # The same semester, drawn for two markets that start five years apart, must move the
    # same way: that is what makes joint.run()'s pooling correctly sized.
    shared = [trade_models.semester_shift(SEED, 4030, DRAWS, 0),
              trade_models.semester_shift(SEED, 4030, DRAWS, 0)]
    if not np.array_equal(*shared):
        failures.append("semester_shift: el mismo semestre dio dos desplazamientos")
    if np.array_equal(shared[0], trade_models.semester_shift(SEED, 4031, DRAWS, 0)):
        failures.append("semester_shift: dos semestres distintos dieron el mismo")
    whole = trade_models.semester_shift(SEED, 4030, DRAWS, 0)
    halves = np.concatenate([trade_models.semester_shift(SEED, 4030, DRAWS // 2, 0),
                             trade_models.semester_shift(SEED, 4030, DRAWS // 2, DRAWS // 2)])
    if not np.array_equal(whole, halves):
        failures.append("semester_shift: por lotes no reproduce la tirada entera")
    print("\n".join(failures)
          or "ok: block_shift no solapa, y un semestre se mueve igual en cualquier mercado")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

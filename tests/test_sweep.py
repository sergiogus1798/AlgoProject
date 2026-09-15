#!/usr/bin/env python3
"""Regression test for the window sweep: one block is the model itself, and blocks confine."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategies.crossmarket import envelope, sweep, trade_models

FREE = ("segment_permute", "resampled_holds", "fitted_holds")
DRAWS = 300


def synthetic(seed: int) -> tuple[pd.DataFrame, dict]:
    """A real-looking run: a few hundred trades with uneven holds and gaps.

    Args:
        seed: Which run.

    Returns:
        (held, market) in the shapes envelope.occupancy() and envelope.describe() give, the
        window ending on the last exit as envelope.window() leaves it.
    """
    rng = np.random.default_rng(seed)
    hold = rng.integers(1, 40, 400)
    gap = rng.integers(0, 300, 400)
    entry = np.cumsum(gap) + np.cumsum(hold) - hold
    held = pd.DataFrame({"entry": entry, "exit": entry + hold, "hold": hold})
    return held, {"gaps": envelope.gaps(held), "n_bars": int(held["exit"].iloc[-1]) + 1}


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
    for seed in range(3):
        held, market = synthetic(seed)
        n = market["n_bars"]
        for model in FREE:
            alone = trade_models.MODELS[model](held, market, DRAWS, np.random.default_rng(seed))
            one = sweep.confine(model, held, np.zeros(n, dtype=np.int64), DRAWS,
                                np.random.default_rng(seed))
            if not (np.array_equal(alone[0], one[0]) and np.array_equal(alone[1], one[1])):
                failures.append(f"{model} seed {seed}: one block is not the model itself")
            if overlaps(*alone):
                failures.append(f"{model} seed {seed}: {overlaps(*alone)} overlapping trades")
            block = np.arange(n) // 5000
            entries, holds = sweep.confine(model, held, block, DRAWS,
                                           np.random.default_rng(seed))
            home = block[held["entry"].to_numpy()]
            first = np.searchsorted(block, home)
            last = np.searchsorted(block, home, side="right")
            kept = holds > 0
            outside = kept & ((entries < first) | (entries + holds > last))
            if outside.any():
                failures.append(f"{model} seed {seed}: {outside.sum()} trades left their block")
            if overlaps(entries, holds):
                failures.append(f"{model} seed {seed}: overlap inside blocks")
            if kept.mean() < 0.9:
                failures.append(f"{model} seed {seed}: only {kept.mean():.0%} of trades kept")
    print("\n".join(failures) or "ok: one block is the model, blocks confine, nothing overlaps")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

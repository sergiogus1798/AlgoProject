"""Which strategies beat their benchmark once every strategy tried is paid for: SPA and StepM."""

import numpy as np
import pandas as pd
from arch.bootstrap import SPA, optimal_block_length


def block_length(excess: pd.DataFrame) -> int:
    """Mean block length of the stationary bootstrap, by Politis and White.

    Args:
        excess: One column per strategy, one row per day, each the strategy's daily
            profit minus its benchmark's.

    Returns:
        The median over columns of each column's optimal length, rounded, at least 1. One
        length for the whole panel, because the bootstrap resamples whole days across
        every column at once — that joint draw is what carries the correlation between
        strategies into the null.
    """
    lengths = optimal_block_length(excess)["stationary"]
    return max(1, int(round(float(lengths.median()))))


def spa(excess: pd.DataFrame, block: int, reps: int, seed: int) -> dict:
    """Hansen's test of superior predictive ability over the whole panel.

    Args:
        excess: As block_length() takes it.
        block: Mean block length.
        reps: Bootstrap replications.
        seed: Seed of the bootstrap.

    Returns:
        {"lower", "consistent", "upper"}: the p of "no strategy beats its benchmark". The
        three differ only in how they treat the strategies that are clearly worse than the
        benchmark — `upper` counts all of them against the test, `lower` none — so the gap
        between the two says how much the bad candidates are dragging the answer.
    """
    test = SPA(np.zeros(len(excess)), -excess, block_size=block, reps=reps,
               bootstrap="stationary", seed=seed)
    test.compute()
    return {k: float(v) for k, v in test.pvalues.items()}


def stepm(excess: pd.DataFrame, fwer: float, block: int, reps: int, seed: int) -> list:
    """Romano and Wolf's stepwise set of the strategies that beat their benchmark.

    Args:
        excess: As block_length() takes it.
        fwer: Family-wise error rate: the chance of naming at least one strategy that does
            not beat its benchmark.
        block: Mean block length.
        reps: Bootstrap replications.
        seed: Seed of the bootstrap.

    Returns:
        The column names it can name at that error rate, possibly none, sorted.

        The step-down is written here on `arch`'s own SPA instead of calling its `StepM`:
        🔬 `arch` 7.2.0 loops while the *last* round named fewer than K, not the rounds
        together, so a panel whose rounds name every column between them re-runs the SPA
        on zero columns and raises. At K = 200 it never happens; at the handful of mothers
        step 20 tests it does. Same seed, same draws: on 80 panels where `StepM` does not
        raise, this names exactly what it names.
    """
    named, left = [], list(excess.columns)
    while left:
        test = SPA(np.zeros(len(excess)), -excess[left], block_size=block, reps=reps,
                   bootstrap="stationary", seed=seed)
        test.compute()
        found = list(test.better_models(fwer))
        if not found:
            break
        named += found
        left = [c for c in left if c not in found]
    return sorted(named)

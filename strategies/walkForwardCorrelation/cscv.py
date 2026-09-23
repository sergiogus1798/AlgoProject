"""Combinatorially symmetric cross-validation: every half of history trains, the rest judges."""

import itertools
from collections.abc import Callable

import numpy as np
import pandas as pd


def partitions(blocks: int) -> list[tuple[int, ...]]:
    """Every way to use half the blocks as in-sample and the other half as out-of-sample.

    Args:
        blocks: How many contiguous pieces the history is cut into. Ten gives 252.

    Returns:
        One tuple of in-sample block numbers per partition; the rest is out of sample.

        Taking combinations rather than a moving boundary is what makes this symmetric:
        every block spends the same number of partitions on each side, so nothing about
        the answer depends on which end of the history a period happened to fall.
    """
    return list(itertools.combinations(range(blocks), blocks // 2))


def sharpe(values: np.ndarray) -> np.ndarray:
    """Per-period Sharpe of every column of a block of returns.

    Args:
        values: Periods down, variants across.

    Returns:
        One Sharpe per variant, unannualised. A variant that never moved in the window
        scores zero rather than dividing by zero -- it made nothing, which is the honest
        reading and keeps it rankable against the rest.
    """
    spread = values.std(axis=0, ddof=1)
    return np.divide(values.mean(axis=0), spread, out=np.zeros_like(spread),
                     where=spread > 0)


def carry(train: np.ndarray, test: np.ndarray) -> tuple[float, float]:
    """How much of the in-sample ordering survives into the held-out half.

    Args:
        train: One in-sample Sharpe per variant.
        test: The same variants' out-of-sample Sharpe.

    Returns:
        (slope, R-squared) of a straight line through all the variants.

        ⚠️ **Across every variant, not just the chosen one.** For a fixed variant the two
        halves are disjoint rows, so under a null they are independent and this slope is
        zero. Regress only the *chosen* variant's two Sharpes and you measure something
        else entirely: the halves are complementary, so a partition where the winner
        looked unusually good inside has less left over outside. Measured on pure noise
        2026-09-22, that version reads -0.57, and on a panel with one genuinely good
        column it reads -0.99 -- more negative where the edge is real. It is a seesaw,
        not a diagnosis.
    """
    slope, intercept = np.polyfit(train, test, 1)
    fitted = slope * train + intercept
    spread = ((test - test.mean()) ** 2).sum()
    return float(slope), float(1 - ((test - fitted) ** 2).sum() / spread)


def run(wide: pd.DataFrame, blocks: int, rule: Callable, grid: pd.DataFrame,
        rng: np.random.Generator) -> pd.DataFrame:
    """Choose in sample and score out of sample, once per partition.

    Args:
        wide: The panel, periods down and variants across.
        blocks: How many pieces to cut the history into.
        rule: One of `rules.RULES` -- what "choose the best" is taken to mean.
        grid: The `param_` columns in the panel's column order, for the rules that need
            to know which variants are neighbours.
        rng: The draw, for the rule that is random.

    Returns:
        One row per partition: which variant the rule picked, its relative rank out of
        sample (`omega`), the logit of that rank (`lam`), the two Sharpes, the median
        variant's out-of-sample Sharpe, and the picked variant's out-of-sample profit.

        `omega` is the rank among n variants scaled into (0, 1), so 0.5 is the median
        and `lam <= 0` is the event the whole method is built to count: the parameter set
        that won in sample came back below average out of it.
    """
    pieces = np.array_split(np.arange(len(wide)), blocks)
    values, n = wide.to_numpy(), wide.shape[1]
    rows = []
    for inside in partitions(blocks):
        outside = [b for b in range(blocks) if b not in inside]
        train = sharpe(values[np.concatenate([pieces[b] for b in inside])])
        held = values[np.concatenate([pieces[b] for b in outside])]
        test = sharpe(held)
        pick = rule(train, grid, rng)
        omega = (int((test < test[pick]).sum()) + 1) / (n + 1)
        slope, r2 = carry(train, test)
        rows.append({"pick": pick, "omega": omega,
                     "lam": float(np.log(omega / (1 - omega))),
                     "is_sharpe": float(train[pick]), "oos_sharpe": float(test[pick]),
                     "oos_median": float(np.median(test)), "slope": slope, "r2": r2,
                     "oos_pnl": float(held[:, pick].sum())})
    return pd.DataFrame(rows)

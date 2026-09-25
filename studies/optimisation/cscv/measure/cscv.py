"""Combinatorially symmetric cross-validation: every half of history trains, the rest judges."""

import itertools
from collections.abc import Callable

import numpy as np
import pandas as pd


def partitions(blocks: int) -> list[tuple[int, ...]]:
    """Every way to use half the blocks as in-sample and the other half as out-of-sample.

    Args:
        blocks: How many contiguous pieces the history is cut into. Twelve gives 924,
            ten gives 252.

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


def sortino(values: np.ndarray) -> np.ndarray:
    """Per-period Sortino of every column of a block of returns.

    Args:
        values: Periods down, variants across.

    Returns:
        One Sortino per variant, unannualised: the mean over the downside deviation
        around zero, which counts only the periods that lost. Same shape and same
        direction as `sharpe`, and time-comparable for the same reason -- both are a
        rate per period rather than a total, so a window twice as long does not score
        twice as high.

        ⚠️ **A variant that never lost in the window has no downside deviation and so no
        finite Sortino.** It is placed one step above every variant that did lose, which
        is the right ranking and an uninterpretable number: read `lam` and `omega`, never
        the level itself, on a panel where that happens.
    """
    mean = values.mean(axis=0)
    downside = np.sqrt(np.square(np.minimum(values, 0.0)).mean(axis=0))
    out = np.divide(mean, downside, out=np.zeros_like(downside), where=downside > 0)
    flawless = (downside <= 0) & (mean > 0)
    if flawless.any():
        out[flawless] = out.max(initial=0.0) + 1.0
    return out


# Every score here must be comparable across windows of different lengths: a rate per
# period, never a total. That is what rules out Ret/DD, whose numerator grows with T and
# whose denominator grows with sqrt(T) -- see POSSIBLE_IMPROVEMENTS.md section 2.
SCORES = {"sharpe": sharpe, "sortino": sortino}


def carry(train: np.ndarray, test: np.ndarray) -> tuple[float, float]:
    """How much of the in-sample ordering survives into the held-out half.

    Args:
        train: One in-sample score per variant.
        test: The same variants' out-of-sample score.

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
        rng: np.random.Generator, score: Callable = sharpe) -> pd.DataFrame:
    """Choose in sample and score out of sample, once per partition.

    Args:
        wide: The panel, periods down and variants across.
        blocks: How many pieces to cut the history into.
        rule: One of `rules.RULES` -- what "choose the best" is taken to mean.
        grid: The `param_` columns in the panel's column order, for the rules that need
            to know which variants are neighbours.
        rng: The draw, for the rule that is random.
        score: What "best" is measured in, one of `SCORES`. Whatever it is, it is used
            on both halves of every partition, so the comparison stays like for like.

    Returns:
        One row per partition: which variant the rule picked, its relative rank out of
        sample (`omega`), the logit of that rank (`lam`), the two scores, the median
        variant's out-of-sample score, and the picked variant's out-of-sample profit.

        `omega` is the rank among n variants scaled into (0, 1), so 0.5 is the median
        and `lam <= 0` is the event the whole method is built to count: the parameter set
        that won in sample came back below average out of it.
    """
    pieces = np.array_split(np.arange(len(wide)), blocks)
    values, n = wide.to_numpy(), wide.shape[1]
    rows = []
    for inside in partitions(blocks):
        outside = [b for b in range(blocks) if b not in inside]
        train = score(values[np.concatenate([pieces[b] for b in inside])])
        held = values[np.concatenate([pieces[b] for b in outside])]
        test = score(held)
        pick = rule(train, grid, rng)
        omega = (int((test < test[pick]).sum()) + 1) / (n + 1)
        slope, r2 = carry(train, test)
        rows.append({"pick": pick, "omega": omega,
                     "lam": float(np.log(omega / (1 - omega))),
                     "is_score": float(train[pick]), "oos_score": float(test[pick]),
                     "oos_median": float(np.median(test)), "slope": slope, "r2": r2,
                     "oos_pnl": float(held[:, pick].sum())})
    return pd.DataFrame(rows)

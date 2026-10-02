"""Combinatorially symmetric cross-validation: every half of history trains, the rest judges."""

import itertools
from collections.abc import Callable

import numpy as np
import pandas as pd


def partitions(blocks: int) -> list[tuple[int, ...]]:
    """Every way to use half the blocks as in-sample and the other half as out-of-sample.

    Args:
        blocks: How many contiguous pieces the history is cut into. Sixteen (the ledger's
            `cscv.blocks`) gives C(16,8) = 12,870; twelve gives 924.

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


def moments(values: np.ndarray, blocks: int) -> dict:
    """Each block's sufficient statistics, so a partition's score never re-reads its rows.

    Args:
        values: The panel as an array, periods down and variants across.
        blocks: How many contiguous pieces the history is cut into.

    Returns:
        `n` (rows per block) and, per block and variant, `s1` (sum), `s2` (sum of squares)
        and `neg2` (sum of squared losses) -- shapes (blocks,) and (blocks, variants).
        Every half of every partition is a sum of eight of these rows, which is what makes
        12,870 partitions over a daily panel cost the same as over a weekly one.
    """
    pieces = np.array_split(values, blocks)
    return {"n": np.array([len(p) for p in pieces], dtype=np.float64),
            "s1": np.stack([p.sum(axis=0) for p in pieces]),
            "s2": np.stack([np.square(p).sum(axis=0) for p in pieces]),
            "neg2": np.stack([np.square(np.minimum(p, 0.0)).sum(axis=0) for p in pieces])}


def _sharpe_of(n: np.ndarray, s1: np.ndarray, s2: np.ndarray, neg2: np.ndarray) -> np.ndarray:
    """`sharpe` off summed moments, one row per partition: mean over the ddof=1 deviation."""
    mean = s1 / n
    var = np.maximum(s2 - s1 * mean, 0.0) / (n - 1)
    spread = np.sqrt(var)
    return np.divide(mean, spread, out=np.zeros_like(spread), where=spread > 0)


def _sortino_of(n: np.ndarray, s1: np.ndarray, s2: np.ndarray, neg2: np.ndarray) -> np.ndarray:
    """`sortino` off summed moments, one row per partition, flawless variants placed on top."""
    mean = s1 / n
    downside = np.sqrt(neg2 / n)
    out = np.divide(mean, downside, out=np.zeros_like(downside), where=downside > 0)
    flawless = (downside <= 0) & (mean > 0)
    top = np.maximum(out.max(axis=1, keepdims=True), 0.0) + 1.0
    return np.where(flawless, top, out)


# The same two scores as SCORES, computed from block sums instead of rows.
FROM_MOMENTS = {"sharpe": _sharpe_of, "sortino": _sortino_of}
# Partitions scored at once: bounds the working set to a dozen CHUNK x variants arrays
# (about 40 MB at 500 variants) whatever the number of blocks.
CHUNK = 1024


def carry(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """How much of the in-sample ordering survives into the held-out half, per partition.

    Args:
        train: One in-sample score per variant, one row per partition.
        test: The same variants' out-of-sample score.

    Returns:
        (slope, R-squared) of each row's least-squares line through all the variants.

        ⚠️ **Across every variant, not just the chosen one** -- an extension of this
        project. For a fixed variant the two halves are disjoint rows, so under a null they
        are independent and this slope is zero. Regress only the *chosen* variant's two
        scores and you get the paper's performance-degradation line, which reads -0.57 on
        pure noise and -0.99 on a panel with one genuinely good column: the halves are
        complementary, so it is a seesaw, not a diagnosis
        (`knowhow/research/cscv-chosen-point-slope-seesaw.md`).
    """
    dx = train - train.mean(axis=1, keepdims=True)
    dy = test - test.mean(axis=1, keepdims=True)
    sxx, syy, sxy = (dx * dx).sum(axis=1), (dy * dy).sum(axis=1), (dx * dy).sum(axis=1)
    slope = sxy / sxx
    return slope, 1 - (syy - slope * sxy) / syy


def run(wide: pd.DataFrame, blocks: int, rule: Callable, grid: pd.DataFrame,
        rng: np.random.Generator, score: str = "sharpe") -> pd.DataFrame:
    """Choose in sample and score out of sample, once per partition.

    Args:
        wide: The panel, periods down and variants across -- daily P&L since 2026-10-01.
        blocks: How many pieces to cut the history into.
        rule: One of `rules.RULES` -- what "choose the best" is taken to mean.
        grid: The `param_` columns in the panel's column order, for the rules that need
            to know which variants are neighbours.
        rng: The draw, for the rule that is random.
        score: What "best" is measured in, a key of `SCORES`. Whatever it is, it is used
            on both halves of every partition, so the comparison stays like for like.

    Returns:
        One row per partition: which variant the rule picked, its relative rank out of
        sample (`omega`), the logit of that rank (`lam`), the two scores, the median
        variant's out-of-sample score, and the picked variant's out-of-sample profit.

        `omega` is the rank among n variants scaled into (0, 1), so 0.5 is the median
        and `lam <= 0` is the event the whole method is built to count: the parameter set
        that won in sample came back below average out of it. Each half is scored off the
        block sums of `moments`, never by concatenating rows; the result is the per-row
        computation's to floating point (`tests/test_cscv.py` holds them equal).
    """
    got, n = moments(wide.to_numpy(np.float64), blocks), wide.shape[1]
    measure = FROM_MOMENTS[score]
    total = {k: v.sum(axis=0) for k, v in got.items()}
    member = np.zeros((len(partitions(blocks)), blocks))
    for i, inside in enumerate(partitions(blocks)):
        member[i, list(inside)] = 1.0
    frames = []
    for at in range(0, len(member), CHUNK):
        take = member[at:at + CHUNK]
        inside = {k: take @ v for k, v in got.items() if k != "n"}
        size = (take @ got["n"])[:, None]
        outside = {k: total[k] - v for k, v in inside.items()}
        train = measure(size, inside["s1"], inside["s2"], inside["neg2"])
        test = measure(total["n"] - size, outside["s1"], outside["s2"], outside["neg2"])
        pick = np.array([rule(row, grid, rng) for row in train])
        rows = np.arange(len(pick))
        chosen = test[rows, pick]
        omega = ((test < chosen[:, None]).sum(axis=1) + 1) / (n + 1)
        slope, r2 = carry(train, test)
        frames.append(pd.DataFrame({
            "pick": pick, "omega": omega, "lam": np.log(omega / (1 - omega)),
            "is_score": train[rows, pick], "oos_score": chosen,
            "oos_median": np.median(test, axis=1), "slope": slope, "r2": r2,
            "oos_pnl": outside["s1"][rows, pick]}))
    return pd.concat(frames, ignore_index=True)

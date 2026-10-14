"""The gate's two resampling tests on a strategy's own trades: homogeneity across periods, and the drawdown its build makes expectable."""

import hashlib

import numpy as np
from numba import njit

from studies.screening.analysis import permuted

ROWS = (
    4096  # sequences whose block starts are drawn at a time: memory only, same stream
)


def warm() -> None:
    """Compile the drawdown and homogeneity kernels in the calling process, before a study forks: a fork child that compiles its own took the pool down."""
    drawdowns(np.ones(2), 0.0, 2, 1, 1, stream(0, ""))
    q_null(np.zeros(4), np.array([2, 2]), 1, stream(0, ""))


def root(seed: int | None) -> int:
    """The root seed of one resampling: the configured one, or a fresh one to write down.

    Args:
        seed: The config's `seed`; None draws a new root.

    Returns:
        32 bits when drawn, so it survives a float column of the scorecard exactly.
    """
    return (
        int(np.random.SeedSequence().generate_state(1)[0])
        if seed is None
        else int(seed)
    )


def stream(seed: int, key: str) -> np.random.Generator:
    """One strategy's own random stream under a root.

    Args:
        seed: What root() returned.
        key: The strategy's identity.

    Returns:
        A generator that depends on the root and the key only — not on which other strategies
        are alive, nor on their order. BLAKE2b because `hash()` is salted per process.
    """
    digest = hashlib.blake2b(key.encode(), digest_size=8).digest()
    return np.random.default_rng([seed, int.from_bytes(digest, "big")])


def periods(labels: np.ndarray, least: int) -> np.ndarray:
    """How many trades each period holds, the thin periods joined to the one after.

    Args:
        labels: One calendar label per trade, labels sorting in time order ("2020Q3").
        least: A period with fewer trades than this is joined to the next; a thin tail is
            joined to the period before it.

    Returns:
        Sizes of the consecutive groups of the trades once sorted by label; they add up to
        len(labels).
    """
    sizes, carry = [], 0
    for count in np.unique(labels, return_counts=True)[1]:
        carry += count
        if carry >= least:
            sizes.append(carry)
            carry = 0
    if carry and sizes:
        sizes[-1] += carry
    return np.array(sizes if sizes else [carry])


def p_upper(null: np.ndarray, observed: float, slack: float = 0.0) -> float:
    """The share of a null at or above what was observed, the observation counted in.

    Args:
        null: The statistic under each repetition.
        observed: The statistic of the real data.
        slack: Rounding tolerance of the statistic: a repetition this close below counts as a tie.

    Returns:
        (count + 1) / (repetitions + 1): never 0.
    """
    return float(((null >= observed - slack).sum() + 1) / (len(null) + 1))


def q_null(
    values: np.ndarray, sizes: np.ndarray, permutations: int, rng: np.random.Generator
) -> tuple[np.ndarray, float, float]:
    """The Q of homogeneity under shuffles of the trades across periods, and the observed one.

    Args:
        values: One figure per trade, sorted so that each period's trades are together.
        sizes: What periods() returned for them; at least two.
        permutations: Shuffles of the trades across periods, every period keeping its size.
        rng: The strategy's stream.

    Returns:
        (the statistic per shuffle, the observed one, its rounding slack). Q is ranked through
        the between-period sum of squares alone: the total is the same in every shuffle, so
        the within-period variance Q divides by moves with it.
    """
    assert sizes.sum() == len(values), "the periods' sizes do not add up to the trades"
    assert sizes[-1] >= 1, "the last period is empty"
    centred = values - values.mean()
    starts = np.cumsum(sizes) - sizes
    observed = (np.add.reduceat(centred, starts) ** 2 / sizes).sum()
    between = permuted.between(centred, starts, sizes, permutations, rng)
    return (
        between,
        float(observed),
        len(centred) * np.finfo(float).eps * (centred @ centred),
    )


def homogeneity(
    values: np.ndarray, sizes: np.ndarray, permutations: int, rng: np.random.Generator
) -> float:
    """Permutation p of the Q of homogeneity: are the periods' means further apart than chance?

    Args:
        values: One figure per trade, sorted so that each period's trades are together.
        sizes: What periods() returned for them.
        permutations: Shuffles of the trades across periods, every period keeping its size.
        rng: The strategy's stream.

    Returns:
        The share of shuffles whose Q (`q_null`) reaches the observed one; NaN with fewer than
        two periods.
    """
    if len(sizes) < 2:
        return np.nan
    return p_upper(*q_null(values, sizes, permutations, rng))


def max_drawdown(pnl: np.ndarray) -> np.ndarray:
    """The deepest fall of a closed-trade curve from its running high.

    Args:
        pnl: Per-trade P/L in time order along the last axis.

    Returns:
        Positive, one per sequence; the curve starts at 0, which counts as a high.
    """
    curve = np.cumsum(pnl, axis=-1)
    return (np.maximum(np.maximum.accumulate(curve, axis=-1), 0.0) - curve).max(axis=-1)


def drawdowns(
    build: np.ndarray,
    mean: float,
    length: int,
    block: int,
    sequences: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Maximum drawdowns of block-bootstrapped sequences of the build's trades at another mean.

    Args:
        build: The build's per-trade P/L, in time order.
        mean: The mean every trade is shifted to — oos1's: spread, tails and order stay.
        length: Trades per sequence — oos1's count.
        block: Consecutive trades per block; a build shorter than a block is one block.
        sequences: How many sequences.
        rng: The strategy's stream.

    Returns:
        One maximum drawdown per sequence, in the units of `build`. Blocks start anywhere a
        whole block fits and never wrap from the last trade to the first.
    """
    if length < 1:
        raise ValueError("a drawdown needs at least one trade per sequence")
    shifted = build - build.mean() + mean
    block = min(block, len(shifted))
    out = np.empty(sequences)
    for done in range(0, sequences, ROWS):
        part = out[done : done + ROWS]
        _dd_stream(
            shifted,
            rng.integers(0, len(shifted) - block + 1, (len(part), -(-length // block))),
            block,
            length,
            part,
        )
    return out


@njit(cache=True, nogil=True)
def _dd_stream(
    shifted: np.ndarray, starts: np.ndarray, block: int, length: int, out: np.ndarray
) -> None:
    """max_drawdown() of each row of block starts, walked trade by trade and cut at `length`.

    numba's max() drops a NaN that numpy's maximum carries, so a curve that stops being a
    number is flagged and answered NaN, never a drawdown of 0 that looks measured.
    """
    for s in range(starts.shape[0]):
        curve = peak = deepest = 0.0
        left, bad = length, False
        for first in starts[s]:
            for i in range(first, first + min(block, left)):
                curve += shifted[i]
                peak = max(peak, curve)
                fall = peak - curve
                bad |= fall != fall
                deepest = max(deepest, fall)
            left -= block
        out[s] = np.nan if bad else deepest

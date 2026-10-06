"""The gate's two resampling tests on a strategy's own trades: homogeneity across periods, and the drawdown its build makes expectable."""

import hashlib

import numpy as np


def root(seed: int | None) -> int:
    """The root seed of one resampling: the configured one, or a fresh one to write down.

    Args:
        seed: The config's `seed`; None draws a new root.

    Returns:
        32 bits when drawn, so it survives a float column of the scorecard exactly.
    """
    return int(np.random.SeedSequence().generate_state(1)[0]) if seed is None else int(seed)


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


def homogeneity(values: np.ndarray, sizes: np.ndarray, permutations: int,
                rng: np.random.Generator) -> float:
    """Permutation p of the Q of homogeneity: are the periods' means further apart than chance?

    Args:
        values: One figure per trade, sorted so that each period's trades are together.
        sizes: What periods() returned for them.
        permutations: Shuffles of the trades across periods, every period keeping its size.
        rng: The strategy's stream.

    Returns:
        The share of shuffles whose Q reaches the observed one; NaN with fewer than two
        periods. Q is ranked through the between-period sum of squares alone: the total is
        the same in every shuffle, so the within-period variance Q divides by moves with it.
    """
    if len(sizes) < 2:
        return np.nan
    centred = values - values.mean()
    starts = np.cumsum(sizes) - sizes
    # ponytail: one permutations x trades matrix (8 bytes each); chunk the shuffles if a
    # strategy ever brings enough trades for that to matter
    between = (np.add.reduceat(rng.permuted(np.tile(centred, (permutations, 1)), axis=1),
                               starts, axis=1) ** 2 / sizes).sum(axis=1)
    observed = (np.add.reduceat(centred, starts) ** 2 / sizes).sum()
    return p_upper(between, observed, len(centred) * np.finfo(float).eps * (centred @ centred))


def max_drawdown(pnl: np.ndarray) -> np.ndarray:
    """The deepest fall of a closed-trade curve from its running high.

    Args:
        pnl: Per-trade P/L in time order along the last axis.

    Returns:
        Positive, one per sequence; the curve starts at 0, which counts as a high.
    """
    curve = np.cumsum(pnl, axis=-1)
    return (np.maximum(np.maximum.accumulate(curve, axis=-1), 0.0) - curve).max(axis=-1)


def drawdowns(build: np.ndarray, mean: float, length: int, block: int, sequences: int,
              rng: np.random.Generator) -> np.ndarray:
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
    shifted = build - build.mean() + mean
    block = min(block, len(shifted))
    starts = rng.integers(0, len(shifted) - block + 1, (sequences, -(-length // block)))
    index = (starts[:, :, None] + np.arange(block)).reshape(sequences, -1)[:, :length]
    return max_drawdown(shifted[index])

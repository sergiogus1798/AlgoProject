"""How a trade stream is reordered or resampled. Every model behind one signature."""

import numpy as np


def iid_shuffle(n: int, size: int, rng: np.random.Generator, block: int) -> np.ndarray:
    """Uniform permutation of the trades.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Fresh generator.
        block: Unused; the signature is shared by every model in DRAWS.

    Returns:
        One row of positions per simulation. Assumes trades are independent, so it
        understates drawdown when they are not: it is the baseline whose gap against the
        block models measures the autocorrelation.
    """
    return rng.permuted(np.tile(np.arange(size), (n, 1)), axis=1)


def block_shuffle(n: int, size: int, rng: np.random.Generator, block: int) -> np.ndarray:
    """Permute contiguous blocks of trades, keeping each block's inside order.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Fresh generator.
        block: Trades per block.

    Returns:
        One row of positions per simulation, every trade exactly once. The last block is
        short when size is not a multiple of block; it is padded and the padding removed
        afterwards, so the multiset is preserved whatever the block length.
    """
    count = -(-size // block)
    pad = np.full(count * block, -1)
    pad[:size] = np.arange(size)
    order = rng.permuted(np.tile(np.arange(count), (n, 1)), axis=1)
    laid = pad.reshape(count, block)[order].reshape(n, count * block)
    keep = np.argsort(laid < 0, axis=1, kind="stable")
    return np.take_along_axis(laid, keep, axis=1)[:, :size]


def stationary(n: int, size: int, rng: np.random.Generator, block: int) -> np.ndarray:
    """Politis-Romano stationary bootstrap: geometric block lengths, wrapping around.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Fresh generator.
        block: Mean block length; the per-block draw is Geometric(1 / block).

    Returns:
        One row of positions per simulation, drawn with replacement. No single dependence
        length is imposed, which is why its drawdown distribution is the headline one — at
        the price of perturbing composition mildly, so its net profit is not invariant.
    """
    out = np.empty((n, size), dtype=int)
    fresh = rng.random((n, size)) < 1.0 / block
    starts = rng.integers(0, size, (n, size))
    out[:, 0] = starts[:, 0]
    for j in range(1, size):
        out[:, j] = np.where(fresh[:, j], starts[:, j], (out[:, j - 1] + 1) % size)
    return out


def iid_bootstrap(n: int, size: int, rng: np.random.Generator, block: int) -> np.ndarray:
    """Draw the same number of trades with replacement, independently.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Fresh generator.
        block: Unused; the signature is shared.

    Returns:
        One row of positions per simulation. The independence baseline for composition luck.
    """
    return rng.integers(0, size, (n, size))


def block_bootstrap(n: int, size: int, rng: np.random.Generator, block: int) -> np.ndarray:
    """Draw contiguous blocks with replacement, wrapping around the end.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Fresh generator.
        block: Trades per block.

    Returns:
        One row of positions per simulation. Composition varies while runs of consecutive
        trades survive, which is the realistic composition test when trades are correlated.
    """
    count = -(-size // block)
    starts = rng.integers(0, size, (n, count))
    laid = (starts[:, :, None] + np.arange(block)) % size
    return laid.reshape(n, count * block)[:, :size]


DRAWS = {"iid_shuffle": iid_shuffle, "block_shuffle": block_shuffle,
         "stationary": stationary, "iid_bootstrap": iid_bootstrap,
         "block_bootstrap": block_bootstrap}

# What each model holds fixed and what it randomises. A model that changes more than one
# thing cannot attribute a result to any single cause, so this table is printed next to the
# numbers it produced rather than kept as documentation.
FAMILY = {"iid_shuffle": "A", "block_shuffle": "A", "stationary": "A",
          "iid_bootstrap": "B", "block_bootstrap": "B"}
PRESERVES = {
    "iid_shuffle": "every trade exactly once; only the order changes",
    "block_shuffle": "every trade exactly once, and the runs inside each block",
    "stationary": "the trade count and, on average, runs of length block; composition drifts",
    "iid_bootstrap": "only the trade count; which trades occur changes",
    "block_bootstrap": "the trade count and runs of consecutive trades; composition changes"}
KEEPS_MULTISET = ("iid_shuffle", "block_shuffle")

# What a run is called on screen and in the report. The keys above are code; nobody should
# have to know them to read a progress bar.
TITLES = {"iid_shuffle": "Barajado i.i.d.", "block_shuffle": "Bloques barajados",
          "stationary": "Bootstrap estacionario", "iid_bootstrap": "Remuestreo i.i.d.",
          "block_bootstrap": "Bloques remuestreados"}


def title(model: str, block: int) -> str:
    """The name of one sub-run, as a human reads it.

    Args:
        model: Key of DRAWS.
        block: Block length, 0 for the models that have none.

    Returns:
        A sentence, e.g. "Bloques barajados — bloques de 17 operaciones". The stationary
        bootstrap says "media" because its block length is the mean of a geometric draw and
        not a fixed size.
    """
    if model == "stationary":
        return f"{TITLES[model]} — bloques de {block} operaciones de media"
    if block <= 1:
        return TITLES[model]
    return f"{TITLES[model]} — bloques de {block} operaciones"

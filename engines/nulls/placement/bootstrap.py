"""Block-bootstrap resampling of trade sequences, and confidence intervals from the draws."""

from collections.abc import Iterator

import numpy as np

CELLS = 1_000_000   # positions laid out at once: 8 MB of int64


def block_rows(n: int, size: int, rng: np.random.Generator, block: int,
               cells: int = CELLS) -> Iterator[np.ndarray]:
    """Draw contiguous blocks with replacement, wrapping around the end, a few rows at a time.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Seeded generator.
        block: Trades per block.
        cells: Most positions laid out at once.

    Yields:
        Consecutive slices of the (n, size) matrix of positions into the original sequence,
        one row per simulation. Every block start is drawn in one call before any row is
        laid out, so the draws are the same whatever `cells` is; only the memory changes.
        🔬 2026-09-26: the whole matrix of 2,000 x 20,414 trades was ~650 MB in one
        crossmarket worker, 48 of them at once. A copy of engines.resample.draws'
        block_bootstrap in spirit: crossmarket keeps its own under CODESTYLE.md rule 5.
    """
    count = -(-size // block)
    starts = rng.integers(0, size, (n, count))
    step = max(1, cells // size)
    for first in range(0, n, step):
        laid = (starts[first:first + step, :, None] + np.arange(block)) % size
        yield laid.reshape(len(laid), count * block)[:, :size]


def percentile_ci(values: np.ndarray, lo: float, hi: float) -> dict:
    """A percentile confidence interval from a set of bootstrap draws.

    Args:
        values: One statistic per draw.
        lo, hi: Percentiles to report.

    Returns:
        Keys lo, hi and median.
    """
    return {"lo": float(np.percentile(values, lo)), "hi": float(np.percentile(values, hi)),
            "median": float(np.median(values))}

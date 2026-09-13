"""Block-bootstrap resampling of trade sequences, and confidence intervals from the draws."""

import numpy as np


def block_bootstrap(n: int, size: int, rng: np.random.Generator, block: int) -> np.ndarray:
    """Draw contiguous blocks with replacement, wrapping around the end.

    Args:
        n: Simulations to draw.
        size: Trades in the stream.
        rng: Seeded generator.
        block: Trades per block.

    Returns:
        One row of positions per simulation, into the original sequence. A copy of
        strategies.monteCarlo.draws.block_bootstrap: exposure.py and significance.py both
        need it, which under CODESTYLE.md rule 5 is not yet "shared" — crossmarket keeps
        its own rather than importing from monteCarlo.
    """
    count = -(-size // block)
    starts = rng.integers(0, size, (n, count))
    laid = (starts[:, :, None] + np.arange(block)) % size
    return laid.reshape(n, count * block)[:, :size]


def percentile_ci(values: np.ndarray, lo: float = 5.0, hi: float = 95.0) -> dict:
    """A percentile confidence interval from a set of bootstrap draws.

    Args:
        values: One statistic per draw.
        lo, hi: Percentiles to report.

    Returns:
        Keys lo, hi and median.
    """
    return {"lo": float(np.percentile(values, lo)), "hi": float(np.percentile(values, hi)),
            "median": float(np.median(values))}

"""One worker's batch, computed in strips of rows small enough to stay in cache."""

import numpy as np

from engines.resample import draws
from portfolio.common.monteCarlo.model import stress
from portfolio.common.monteCarlo.simulate import kernel, metrics

# Bytes one trade of one simulated path costs while its strip is alive: the (rows, trades)
# int64 positions a draw model returns, or the float64 P&L a stress model prices. The
# statistics themselves run in `kernel`, which keeps no matrix of its own.
ROW_ITEM = 8


def rows(n_trades: int, tile_bytes: int) -> int:
    """How many simulations one strip carries.

    Args:
        n_trades: Trades in the stream.
        tile_bytes: cfg["global"]["tile_bytes"], the working-set budget of one strip.

    Returns:
        At least one row. Sizing the strip in bytes rather than in simulations is what
        makes a worker's memory independent of how long the strategy is.
    """
    return max(1, tile_bytes // (n_trades * ROW_ITEM))


def batch(job: tuple) -> dict[str, np.ndarray]:
    """One worker's share of the simulations, one strip at a time.

    Args:
        job: (kind, model, block, simulations, payload, starting equity, family_c config,
            tile bytes, seed).

    Returns:
        One array per statistic of metrics.NAMES, of length `simulations`. The generator is
        built from the job's `seed` (a SeedSequence the engine derives per sub-test and chunk),
        so a run is reproducible and no two chunks share a stream.

    Every strip asks its model for its own draw. A hand-rolled strip sampler that reused
    one uniform buffer for "does this block restart" and "where does it restart" would
    correlate the restart positions with the 1/block threshold and pile them at the head of
    the stream; calling the model per strip keeps the two draws independent by construction.
    """
    kind, model, block, n, data, equity0, cfg_c, tile_bytes, seed = job
    rng = np.random.default_rng(seed)
    # float32 for the gathered P&L: metrics.paths accumulates in float64 whatever it is
    # given, and 24 bits of mantissa summed in 53 make the reordering invariant exact
    # rather than approximate. The Family C models build their P&L from fresh uniforms
    # instead of gathering it, so they arrive in float64 and stay there.
    source = data["pnl"].astype(np.float32)
    height = rows(source.size, tile_bytes)
    out = np.empty((n, len(metrics.NAMES)))
    for lo in range(0, n, height):
        high = min(lo + height, n)
        if kind == "draw":
            kernel.gathered(source, draws.DRAWS[model](high - lo, source.size, rng, block),
                            equity0, out[lo:high])
        else:
            kernel.priced(stress.STRESS[model](data, high - lo, rng, cfg_c), equity0,
                          out[lo:high])
    return {name: out[:, i].copy() for i, name in enumerate(metrics.NAMES)}

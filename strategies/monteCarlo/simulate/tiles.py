"""One worker's batch, computed in strips of rows small enough to stay in cache."""

import numpy as np

from strategies.monteCarlo.model import draws, stress
from strategies.monteCarlo.simulate import metrics

# Bytes one trade of one simulated path costs while its strip is alive. The kernel holds
# several (rows, trades) intermediates at once — the equity path, its running peak, the
# drop and the drop ratio — and the widest of them is float64, so the strip is measured in
# whole float64 matrices and tile_bytes carries the rest of the factor.
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
            tile bytes).

    Returns:
        One array per statistic of metrics.NAMES, of length `simulations`. The generator is
        seeded from the operating system inside the worker, so every batch draws
        independent fresh entropy and no two workers can share a stream. Runs are
        deliberately not reproducible — stability.py measures the run-to-run spread instead
        of hiding it behind a seed.

    Every strip asks its model for its own draw. A hand-rolled strip sampler that reused
    one uniform buffer for "does this block restart" and "where does it restart" would
    correlate the restart positions with the 1/block threshold and pile them at the head of
    the stream; calling the model per strip keeps the two draws independent by construction.
    """
    kind, model, block, n, data, equity0, cfg_c, tile_bytes = job
    rng = np.random.default_rng()
    # float32 for the gathered P&L: metrics.paths accumulates in float64 whatever it is
    # given, and 24 bits of mantissa summed in 53 make the reordering invariant exact
    # rather than approximate. The Family C models build their P&L from fresh uniforms
    # instead of gathering it, so they arrive in float64 and stay there.
    source = data["pnl"].astype(np.float32)
    height = rows(source.size, tile_bytes)
    out = {k: np.empty(n) for k in metrics.NAMES}
    for lo in range(0, n, height):
        high = min(lo + height, n)
        if kind == "draw":
            pnl = source[draws.DRAWS[model](high - lo, source.size, rng, block)]
        else:
            pnl = stress.STRESS[model](data, high - lo, rng, cfg_c)
        for name, value in metrics.paths(pnl, equity0).items():
            out[name][lo:high] = value
    return out

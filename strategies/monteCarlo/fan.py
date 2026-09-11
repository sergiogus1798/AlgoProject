"""The equity envelope: where the reordered paths ran, trade by trade, around the real one."""

import numpy as np

from strategies.monteCarlo import draws

STEPS = 200   # points kept per curve; an SVG cannot show more and the file stays small


def envelope(pnl: np.ndarray, model: str, block: int, sims: int, equity0: float,
             qs: list[int]) -> dict:
    """Percentile bands of the simulated equity paths, against the path that happened.

    Args:
        pnl: Net USD per trade, in the order they happened.
        model: Key of draws.DRAWS.
        block: Block length, ignored by the models that have none.
        sims: Paths to draw. Far fewer than a gate needs: this is a picture of the spread,
            and its bands are stable long before its tails are.
        equity0: Starting account in USD.
        qs: Percentiles to band.

    Returns:
        The step positions, one band per percentile and the observed path, all sampled down
        to STEPS points. Read it for the width of the cone, not for any single curve: the
        cone is what order luck alone can do to the same trades.
    """
    rng = np.random.default_rng()
    idx = draws.DRAWS[model](sims, pnl.size, rng, block)
    equity = equity0 + np.cumsum(pnl[idx], axis=1)
    at = np.unique(np.linspace(0, pnl.size - 1, min(STEPS, pnl.size)).astype(int))
    bands = np.percentile(equity[:, at], qs, axis=0)
    return {"at": at.tolist(),
            "bands": {q: row.tolist() for q, row in zip(qs, bands)},
            "observed": (equity0 + np.cumsum(pnl))[at].tolist()}

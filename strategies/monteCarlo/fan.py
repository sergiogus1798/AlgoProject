"""The equity envelope: where the simulated paths ran, trade by trade, around the real one."""

import numpy as np

from strategies.monteCarlo import draws, stress

STEPS = 200   # points kept per curve; an SVG cannot show more and the file stays small


def _bands(equity: np.ndarray, pnl: np.ndarray, equity0: float, qs: list[int]) -> dict:
    """Percentile bands of a batch of simulated equity paths, sampled down for an SVG.

    Args:
        equity: One simulated equity path per row.
        pnl: The real, unperturbed net USD per trade, for the observed curve.
        equity0: Starting account in USD.
        qs: Percentiles to band.

    Returns:
        The step positions, one band per percentile and the observed path, all sampled down
        to STEPS points.
    """
    at = np.unique(np.linspace(0, pnl.size - 1, min(STEPS, pnl.size)).astype(int))
    bands = np.percentile(equity[:, at], qs, axis=0)
    return {"at": at.tolist(),
            "bands": {q: row.tolist() for q, row in zip(qs, bands)},
            "observed": (equity0 + np.cumsum(pnl))[at].tolist()}


def envelope(pnl: np.ndarray, model: str, block: int, sims: int, equity0: float,
             qs: list[int]) -> dict:
    """Percentile bands under a reordering or resampling model (Families A and B).

    Args:
        pnl: Net USD per trade, in the order they happened.
        model: Key of draws.DRAWS.
        block: Block length, ignored by the models that have none.
        sims: Paths to draw. Far fewer than a gate needs: this is a picture of the spread,
            and its bands are stable long before its tails are.
        equity0: Starting account in USD.
        qs: Percentiles to band.

    Returns:
        What _bands() returns. Read it for the width of the cone, not for any single curve:
        the cone is what order or composition luck alone can do to the same trades.
    """
    rng = np.random.default_rng()
    idx = draws.DRAWS[model](sims, pnl.size, rng, block)
    return _bands(equity0 + np.cumsum(pnl[idx], axis=1), pnl, equity0, qs)


def stress_envelope(source: dict, model: str, sims: int, cfg: dict, qs: list[int]) -> dict:
    """Percentile bands under one Family C execution stress.

    Args:
        source: What engine.payload() returned — pnl, cost, spread and mae aligned.
        model: Key of stress.STRESS.
        sims: Paths to draw.
        cfg: What config.load() returned.
        qs: Percentiles to band.

    Returns:
        What _bands() returns. The cone here is what the same execution stress can do to
        the curve, not what order alone can — a different question from envelope()'s.
    """
    rng = np.random.default_rng()
    pnl = stress.STRESS[model](source, sims, rng, cfg["family_c"])
    equity0 = cfg["global"]["starting_equity"]
    return _bands(equity0 + np.cumsum(pnl, axis=1), source["pnl"], equity0, qs)

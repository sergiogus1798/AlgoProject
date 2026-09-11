"""The adversarial path: a bad draw from every period of the history, one after another."""

import numpy as np

from strategies.monteCarlo import metrics


def _bad_draw(pnl: np.ndarray, sims: int, quantile: float,
              rng: np.random.Generator) -> np.ndarray:
    """One low-percentile bootstrap realisation of a single period.

    Args:
        pnl: Net USD per trade inside that period.
        sims: Bootstrap draws to choose from.
        quantile: Which draw to keep, 0-1 on net profit.
        rng: Fresh generator.

    Returns:
        The per-trade P&L of the chosen draw, not a summary of it: the point of the stress
        path is that the pieces are concatenated, so the trades themselves have to survive.
    """
    idx = rng.integers(0, pnl.size, (sims, pnl.size))
    drawn = pnl[idx]
    return drawn[int(np.argsort(drawn.sum(axis=1))[int(quantile * (sims - 1))])]


def worst_path(pnl: np.ndarray, segments: list[dict], sims: int, quantile: float,
               equity0: float) -> dict:
    """Stitch a bad period from each segment into one continuous path.

    Args:
        pnl: Net USD per trade, whole stream.
        segments: What windows.rolling() returned for the non-overlapping blocks.
        sims: Bootstrap draws per segment.
        quantile: How bad the draw from each segment is, 0-1 on net profit.
        equity0: Starting account in USD.

    Returns:
        The core statistics of the stitched path. Global Monte Carlo never produces this
        path: it asks what a bad decade looks like, while this asks what it looks like when
        every single period comes in near its own bad end. It is a stress reference and
        feeds the narrative, never a gate on its own.
    """
    rng = np.random.default_rng()
    pieces = [_bad_draw(pnl[s["positions"]], sims, quantile, rng) for s in segments
              if s["positions"].size > 1]
    path = np.concatenate(pieces)
    return {**metrics.observed(path, equity0), "segments": len(pieces),
            "quantile": quantile}

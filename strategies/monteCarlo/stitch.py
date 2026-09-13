"""The adversarial path: a bad draw from every period of the history, one after another."""

import numpy as np

from strategies.monteCarlo import metrics


def _bad_draws(pnl: np.ndarray, sims: int, quantiles: list[float],
               rng: np.random.Generator) -> dict[float, np.ndarray]:
    """One bootstrap realisation of a single period, per requested severity.

    Args:
        pnl: Net USD per trade inside that period.
        sims: Bootstrap draws to choose from.
        quantiles: Which draws to keep, 0-1 on net profit, e.g. 0.05 for the 5th percentile
            draw. Sharing one batch of draws across every quantile — sorting it once and
            reading off several positions — means the quantiles are directly comparable:
            the only thing that differs between them is which row of the same resample gets
            picked, not a fresh draw of randomness.
        rng: Fresh generator.

    Returns:
        {quantile: per-trade P&L of the chosen draw}, not a summary of it: the point of the
        stress path is that the pieces are concatenated, so the trades themselves have to
        survive.
    """
    idx = rng.integers(0, pnl.size, (sims, pnl.size))
    drawn = pnl[idx]
    order = np.argsort(drawn.sum(axis=1))
    return {q: drawn[order[int(q * (sims - 1))]] for q in quantiles}


def worst_path(pnl: np.ndarray, segments: list[dict], sims: int, quantiles: list[float],
               equity0: float) -> dict[float, dict]:
    """Stitch a bad period from each segment into one continuous path, at each severity.

    Args:
        pnl: Net USD per trade, whole stream.
        segments: What windows.rolling() returned for the non-overlapping blocks.
        sims: Bootstrap draws per segment.
        quantiles: How bad the draw from each segment is, 0-1 on net profit. How adversarial
            "bad" should be has no principled answer, so this reports the whole curve
            (`family_d.stitch_quantiles`, e.g. [0.01, 0.05, 0.10, 0.25]) instead of
            committing to one number: if the drawdown barely moves across it, the stress
            reference is stable; if it swings wildly, that instability is itself a finding.
        equity0: Starting account in USD.

    Returns:
        {quantile: core statistics of that quantile's stitched path}. Global Monte Carlo
        never produces this path: it asks what a bad decade looks like, while this asks what
        it looks like when every single period comes in near its own bad end. It is a stress
        reference and feeds the narrative, never a gate on its own.
    """
    rng = np.random.default_rng()
    per_segment = [_bad_draws(pnl[s["positions"]], sims, quantiles, rng) for s in segments
                   if s["positions"].size > 1]
    return {q: {**metrics.observed(np.concatenate([seg[q] for seg in per_segment]), equity0),
               "segments": len(per_segment), "quantile": q}
           for q in quantiles}

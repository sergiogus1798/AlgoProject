"""Streaks of wins and losses, and the runs test SQX scores their randomness with."""

import numpy as np


def _streaks(signs: np.ndarray, want: int) -> tuple[int, float]:
    """Longest and mean run of one sign in a sequence.

    Args:
        signs: The sign of every trade of one simulation.
        want: 1 for wins, -1 for losses.

    Returns:
        (longest, mean). Both zero when the sign never occurs.
    """
    hit = signs == want
    if not hit.any():
        return 0, 0.0
    edges = np.flatnonzero(np.diff(np.concatenate([[0], hit.view(np.int8), [0]])))
    lengths = edges[1::2] - edges[::2]
    return int(lengths.max()), float(lengths.mean())


def prepare(p: dict) -> dict:
    """Add the per-simulation streak and runs statistics to the shared parts, once.

    Args:
        p: What recon.parts() returned.

    Returns:
        The same dict with "max_win_run", "max_loss_run", "avg_win_run", "avg_loss_run" and
        "zscore" added. All five are sequence-dependent, so they share one pass.
    """
    signs = np.sign(p["pnl"]).astype(np.int8)
    sims = p["n"].size
    out = {k: np.zeros(sims) for k in
           ("max_win_run", "max_loss_run", "avg_win_run", "avg_loss_run", "zscore")}
    for k, (start, stop) in enumerate(zip(p["offsets"][:-1], p["offsets"][1:])):
        run = signs[start:stop]
        out["max_win_run"][k], out["avg_win_run"][k] = _streaks(run, 1)
        out["max_loss_run"][k], out["avg_loss_run"][k] = _streaks(run, -1)
        out["zscore"][k] = _zscore(run)
    return {**p, **out}


def _zscore(signs: np.ndarray) -> float:
    """Wald-Wolfowitz runs statistic of one win/loss sequence.

    Args:
        signs: The sign of every trade of one simulation.

    Returns:
        How far the number of runs sits from what independence predicts, in standard
        deviations. Carries a +0.5 continuity correction, which is what SQX uses: without
        it the reconstruction misses its stored value by exactly 0.5 / sigma every time.
        Zero when there are too few trades, or when every trade went the same way.
    """
    wins, losses = int((signs > 0).sum()), int((signs < 0).sum())
    n = wins + losses
    if n < 3 or not wins or not losses:
        return 0.0
    runs = 1 + int((signs[1:] != signs[:-1]).sum())
    mean = 2 * wins * losses / n + 1
    var = 2 * wins * losses * (2 * wins * losses - n) / (n ** 2 * (n - 1))
    return float((runs - mean + 0.5) / np.sqrt(var)) if var > 0 else 0.0


def max_consec_wins(p: dict) -> np.ndarray:
    """Longest run of winning trades.

    Args:
        p: What recon.parts() returned.

    Returns:
        Trades per simulation.
    """
    return p["max_win_run"]


def max_consec_losses(p: dict) -> np.ndarray:
    """Longest run of losing trades.

    Args:
        p: What recon.parts() returned.

    Returns:
        Trades per simulation.
    """
    return p["max_loss_run"]


def avg_consec_wins(p: dict) -> np.ndarray:
    """Mean length of a winning run.

    Args:
        p: What recon.parts() returned.

    Returns:
        Trades per simulation.
    """
    return p["avg_win_run"]


def avg_consec_losses(p: dict) -> np.ndarray:
    """Mean length of a losing run.

    Args:
        p: What recon.parts() returned.

    Returns:
        Trades per simulation.
    """
    return p["avg_loss_run"]


def zscore(p: dict) -> np.ndarray:
    """How non-random the order of wins and losses was.

    Args:
        p: What recon.parts() returned.

    Returns:
        Standard deviations per simulation. A large magnitude means wins clustered, or
        alternated, more than chance explains at the same win rate.
    """
    return p["zscore"]

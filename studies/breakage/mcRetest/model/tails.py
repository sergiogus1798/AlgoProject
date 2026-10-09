"""Where a re-run and the original are the same trades: the tail they share, and what it dates."""

import numpy as np


def common_suffix(run: np.ndarray, original: np.ndarray) -> int:
    """How many trades, counted from the last one back, a re-run shares with the original.

    Args:
        run: P/L per trade of one re-run, chronological, as SQX stored it (cents, or cents
            over 100: the comparison is exact either way).
        original: The same for the unperturbed backtest.

    Returns:
        The length of the longest common suffix. A simulation carries no dates, so an equal
        tail is the only way to give its trades the original's.
    """
    n = min(run.size, original.size)
    differs = (run[run.size - n:] != original[original.size - n:])[::-1]
    return int(np.argmax(differs)) if differs.any() else n


def window_excess(run: np.ndarray, shared: int, excess: np.ndarray, drift: np.ndarray,
                  inside: np.ndarray) -> float:
    """One re-run's excess inside the common window, exact wherever its tail is the original's.

    Args:
        run: P/L per trade of the re-run, USD, chronological.
        shared: What common_suffix() returned for it; the caller has already refused a tail
            too short to be believed.
        excess: The original's P/L minus its drift, per trade, USD.
        drift: The original's drift per trade, USD.
        inside: Per trade of the original, whether it opened inside the common window.

    Returns:
        The original's excess over the window's trades the tail covers, plus, when the tail
        stops short of the window's first trade, the run's unshared head: its P/L minus the
        drift the original collected over the uncovered part of the window, pro rata to how
        many trades the head has against how many the original had before the tail (no
        trades, no exposure, no drift). The head's trades from before the window cannot be
        told apart and are counted in.
    """
    before = excess.size - shared
    covered = inside & (np.arange(excess.size) >= before)
    out = float(excess[covered].sum())
    uncovered = inside & ~covered
    if uncovered.any():
        head = run[:run.size - shared]
        out += float(head.sum() - drift[uncovered].sum() * head.size / before)
    return out

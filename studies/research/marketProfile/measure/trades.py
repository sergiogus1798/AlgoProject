"""What a signal becomes: its entry and exit bars, and the statistic its returns are judged by."""

import numpy as np


def prev(mask: np.ndarray) -> np.ndarray:
    """A condition as it stood one bar earlier."""
    return np.concatenate([[False], mask[:-1]])


def after(mask: np.ndarray, hold: int) -> tuple[np.ndarray, np.ndarray]:
    """Entry and exit bars of a signal read on a closed bar.

    Args:
        mask: True on the bars whose close gives the signal.
        hold: Bars the trade is held.

    Returns:
        (entry, exit): the open of the next bar, and the open `hold` bars later — the
        open-to-open fill SQX was measured to use.
    """
    idx = np.flatnonzero(mask[: mask.size - hold - 1])
    return idx + 1, idx + 1 + hold


def tstat(x: dict, entry: np.ndarray, leave: np.ndarray, least: int) -> float:
    """The t statistic of the trades' log returns; 0 when there are fewer than `least`.

    Studentised on purpose: the null moves returns across hours and regimes of different
    volatility, and a plain mean would be judged against the wrong spread.
    """
    if entry.size < least:
        return 0.0
    v = x["o"][leave] - x["o"][entry]
    spread = v.std(ddof=1)
    return float(v.mean() / spread * np.sqrt(v.size)) if spread > 0 else 0.0


def hit(x: dict, entry: np.ndarray, leave: np.ndarray, least: int) -> float:
    """Share of the trades that close up, less the share of all bars that do."""
    if entry.size < least:
        return 0.0
    o = x["o"]
    return float(np.mean(o[leave] > o[entry]) - np.mean(np.diff(o) > 0))

"""The reading of M9: a fresh stretch against the band of equal-length windows of the portfolio's own history."""

from typing import TypedDict

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from core.metrics import sharpe


def _sharpe(windows: np.ndarray) -> np.ndarray:
    """`core.metrics.sharpe` per day along the last axis; 0 where a window does not vary."""
    return np.nan_to_num(sharpe(windows, 1), nan=0.0)


FIGURES = {"pnl": lambda windows: windows.sum(axis=-1), "sharpe": _sharpe}


class _BandBase(TypedDict):
    """The keys every reading has."""

    state: str
    flagged: bool
    days: int
    windows: int
    independent: int


class Band(_BandBase, total=False):
    """A reading; `value`..`percentile` are absent when there is no band."""

    value: float
    low: float
    high: float
    percentile: float


def read(
    history: np.ndarray, fresh: np.ndarray, figure: str, band: list[float]
) -> Band:
    """Where the fresh stretch's figure falls among every window of its length in the history.

    Args:
        history: [H] the portfolio's daily P&L per unit of risk on the registered segments.
        fresh: [n] the same on the days after them, every day since the first.
        figure: A key of `FIGURES`.
        band: [low, high] percentiles of the windows' figures, 0..100.

    Returns:
        `state` -- "inside", "below" or "above" the band, or "no_band" when the stretch is
        longer than the history (no window of its length exists) or under 2 days; `flagged`
        (below or above); `value`, `low`, `high`, `percentile` (share of windows at or under
        the value), `days`, `windows` (overlapping ones) and `independent` (H // n: how many
        of them do not share a day -- the band's real sample size).
    """
    n = len(fresh)
    if n < 2 or n > len(history):
        return {
            "state": "no_band",
            "flagged": False,
            "days": n,
            "windows": 0,
            "independent": 0,
        }
    values = FIGURES[figure](sliding_window_view(np.asarray(history, dtype=float), n))
    value = float(FIGURES[figure](np.asarray(fresh, dtype=float)))
    low, high = (float(v) for v in np.percentile(values, band))
    state = "below" if value < low else "above" if value > high else "inside"
    return {
        "state": state,
        "flagged": state != "inside",
        "value": value,
        "low": low,
        "high": high,
        "percentile": float((values <= value).mean() * 100),
        "days": n,
        "windows": len(values),
        "independent": len(history) // n,
    }

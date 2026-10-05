"""The reading of M9: a fresh stretch against the band of equal-length windows of the portfolio's own history."""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _sharpe(windows: np.ndarray) -> np.ndarray:
    """Daily Sharpe along the last axis; 0 where a window does not vary."""
    sd = windows.std(axis=-1, ddof=1)
    return np.divide(windows.mean(axis=-1), sd, out=np.zeros_like(sd), where=sd > 0)


FIGURES = {"pnl": lambda windows: windows.sum(axis=-1), "sharpe": _sharpe}


def read(history: np.ndarray, fresh: np.ndarray, figure: str, band: list[float]) -> dict:
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
        return {"state": "no_band", "flagged": False, "days": n, "windows": 0, "independent": 0}
    values = FIGURES[figure](sliding_window_view(np.asarray(history, dtype=float), n))
    value = float(FIGURES[figure](np.asarray(fresh, dtype=float)))
    low, high = (float(v) for v in np.percentile(values, band))
    state = "below" if value < low else "above" if value > high else "inside"
    return {"state": state, "flagged": state != "inside", "value": value, "low": low, "high": high,
            "percentile": float((values <= value).mean() * 100), "days": n, "windows": len(values),
            "independent": len(history) // n}

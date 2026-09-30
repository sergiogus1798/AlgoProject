"""Rolling-window correlation extremes over a pair's aligned series."""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import rankdata


def _window_pearson(aw: np.ndarray, bw: np.ndarray) -> np.ndarray:
    """Pearson correlation per row of two (n_windows, window) matrices."""
    am = aw - aw.mean(axis=1, keepdims=True)
    bm = bw - bw.mean(axis=1, keepdims=True)
    num = (am * bm).sum(axis=1)
    den = np.sqrt((am**2).sum(axis=1) * (bm**2).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / den


def _corr_per_window(aw: np.ndarray, bw: np.ndarray, method: str) -> np.ndarray:
    """Signed correlation per window, one full pass, no python loop over pairs."""
    if method == "spearman":
        aw = np.apply_along_axis(rankdata, 1, aw)
        bw = np.apply_along_axis(rankdata, 1, bw)
    return _window_pearson(aw, bw)


def rolling_max(a: np.ndarray, b: np.ndarray, window: int, recent: int, method: str) -> dict:
    """Maximum signed correlation over every one-step rolling window.

    Args:
        a, b: Aligned P&L series, same length, NaN where outside history.
        window: Window length in rows (60 months).
        recent: A window counts as recent when its last row is among the series' final
            `recent` rows.
        method: "pearson" or "spearman".

    Returns:
        `whole`, `recent`: max of the signed coefficient (NaN if no valid window).
        `whole_abs`, `recent_abs`: max of its absolute value.
        `n_windows`: count of windows with no non-finite row, used in `whole`.
    """
    n = a.size
    if n < window:
        return {"whole": float("nan"), "recent": float("nan"),
                "whole_abs": float("nan"), "recent_abs": float("nan"), "n_windows": 0}

    aw = sliding_window_view(a, window)
    bw = sliding_window_view(b, window)
    valid = np.all(np.isfinite(aw), axis=1) & np.all(np.isfinite(bw), axis=1)
    corr = _corr_per_window(aw, bw, method)
    corr = np.where(valid, corr, np.nan)

    last_row = np.arange(window - 1, n)
    is_recent = last_row >= (n - recent)

    def _max(mask: np.ndarray, abs_: bool) -> float:
        """Max (or max-abs) of the valid windows `mask` selects; NaN if none."""
        vals = corr[mask & valid]
        if vals.size == 0:
            return float("nan")
        return float(np.nanmax(np.abs(vals) if abs_ else vals))

    return {
        "whole": _max(np.ones(corr.size, dtype=bool), False),
        "recent": _max(is_recent, False),
        "whole_abs": _max(np.ones(corr.size, dtype=bool), True),
        "recent_abs": _max(is_recent, True),
        "n_windows": int(valid.sum()),
    }

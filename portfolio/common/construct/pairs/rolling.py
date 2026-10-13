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


def ranked_windows(x: np.ndarray, window: int) -> np.ndarray | None:
    """Ranks inside every one-step window of one series (None if shorter than `window`).

    A series' ranks do not depend on its partner, so the table computes them once per series
    and passes them to `rolling_max` instead of re-ranking in every pair.
    """
    if x.size < window:
        return None
    return rankdata(sliding_window_view(x, window), axis=1)


def _corr_per_window(aw: np.ndarray, bw: np.ndarray, method: str, ranks: tuple[np.ndarray, np.ndarray] | None = None) -> np.ndarray:
    """Signed correlation per window, one full pass, no python loop over pairs."""
    if method == "spearman":
        aw, bw = ranks if ranks is not None else (rankdata(aw, axis=1), rankdata(bw, axis=1))
    return _window_pearson(aw, bw)


def rolling_max(a: np.ndarray, b: np.ndarray, window: int, recent: int, method: str,
                ranks: tuple[np.ndarray, np.ndarray] | None = None) -> dict:
    """Maximum signed correlation over every one-step rolling window.

    Args:
        a, b: Aligned P&L series, same length, NaN where outside history.
        window: Window length in rows (60 months).
        recent: A window counts as recent when its last row is among the series' final
            `recent` rows.
        method: "pearson" or "spearman".
        ranks: Optional `ranked_windows` of `a` and of `b`, for "spearman" (computed if omitted).

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
    corr = _corr_per_window(aw, bw, method, ranks)
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

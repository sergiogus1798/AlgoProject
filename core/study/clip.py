"""The one rule every histogram of the window follows: the axis spans percentiles 0.5-99.5, outliers are not drawn."""

import numpy as np

SPAN = (0.5, 99.5)


def clip(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    """The finite values inside the percentile span of the data, and the span's ends.

    Args:
        values: Raw draws of one statistic.

    Returns:
        (values inside [lo, hi], lo, hi). `len(values) - len(inside)` is how many were left out.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    lo, hi = np.percentile(v, SPAN)
    return v[(v >= lo) & (v <= hi)], float(lo), float(hi)


def caption(left_out: int) -> str:
    """The sentence saying how many values the clipped axis does not draw."""
    return (f" Eje recortado a los percentiles {SPAN[0]:g}-{SPAN[1]:g}: {left_out} valores "
            "fuera, no dibujados." if left_out else "")

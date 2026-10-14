"""N curves drawn as percentile bands (5-95, 25-75), the median and the original — a `cone` block."""

from typing import Any

import numpy as np

from core.study import blocks


def bands(
    title: str,
    unit: str,
    x: list,
    curves: np.ndarray,
    original: list,
    split: str | None = None,
    original_label: str = "original",
) -> dict[str, Any]:
    """Many curves drawn as percentile bands: 5-95 light, 25-75 darker, the median, the original.

    Args:
        title: What the reader is looking at.
        unit: Unit of the curves.
        x: One label per point.
        curves: Shape (n_curves, len(x)) — the permuted, simulated or variant curves.
        original: The observed curve, len(x).
        split: Where the out-of-sample starts, if it does.
        original_label: Key text of the `original` line.

    Returns:
        A "cone" block with `BANDS_5_95` levels; the curves never leave.
    """
    return blocks.cone(
        title, unit, x, curves, original, split, blocks.BANDS_5_95, original_label
    )

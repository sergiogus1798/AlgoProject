"""The shared histogram clip: the axis spans percentiles 0.5-99.5 and says how many values it left out."""

import numpy as np

from core.study import blocks


def test_outliers_leave_the_axis_and_the_caption_counts_them() -> None:
    """Five huge values leave the axis, and the note says so."""
    v = np.concatenate([np.linspace(1, 2, 1000), [120.0] * 5])
    b = blocks.distribution("t", "pb", v, 1.5, "nota")
    assert b["bins"][-1] < 3 and sum(b["counts"]) < len(v)
    assert "5 valores fuera" in b["note"] or "valores fuera" in b["note"]
    assert max(b["counts"]) < 0.5 * sum(b["counts"])      # not one pile in a single bar

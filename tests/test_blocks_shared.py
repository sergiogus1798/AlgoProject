"""Known answers for the shared drawing blocks: sign caption, band helper, scatter cap, red-green ramp."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np  # noqa: E402

from core.study import bands, blocks  # noqa: E402


def test_share_positive_and_shade_flag() -> None:
    """3 of 4 draws above zero is 75 %; a one-sided sample carries no share."""
    b = blocks.distribution("t", "USD", np.array([-1.0, 1, 2, 3]), 1.0, "n")
    assert b["share_positive"] == 0.75 and b["sign_shade"]
    assert "share_positive" not in blocks.distribution(
        "t", "", np.array([1.0, 2, 3]), 1.0, "n"
    )
    assert "share_positive" not in blocks.distribution(
        "t", "", np.array([-1.0, 1]), 0, "n", sign_shade=False
    )


def test_pivot_counts_above_it() -> None:
    """With pivot 1, 2 of 4 ratios are above it; the caption names the pivot."""
    from ui.desktop.blocks.shade import caption

    b = blocks.distribution(
        "t", "", np.array([0.5, 0.9, 1.5, 2.0]), 1.0, "n", pivot=1.0
    )
    assert b["share_positive"] == 0.5 and b["pivot"] == 1.0
    assert caption(0.5, 1.0).endswith("% por encima de 1") and caption(0.75).endswith(
        "rentables"
    )


def test_beside_and_text_score() -> None:
    """A beside block shares the row of the one before; a text score reaches the verdict card."""
    from PySide6.QtWidgets import QApplication
    from ui.desktop.blocks import verdict
    from ui.desktop.blocks.tabpage import TabPage

    app = QApplication.instance() or QApplication([])
    a, b = (blocks.table(t, __import__("pandas").DataFrame({"x": [1]})) for t in "ab")
    page = TabPage([{"name": "t", "note": "", "blocks": [a, b | {"beside": True}]}], {})
    grid = page.body.layout()
    assert grid.rowCount() == 1 and grid.columnCount() == 2
    v = verdict.widget(blocks.verdict("Fiable", "pass", "m", "Spearman 44,53 %"))
    assert (
        "44,53 %"
        in v.findChild(__import__("PySide6.QtWidgets").QtWidgets.QLabel).text()
        and app
    )


def test_bands_percentiles_of_a_tiny_array() -> None:
    """Five curves of 0..4 plus the original: the bands are the percentiles per point."""
    curves = np.array([[i, 10.0 + i] for i in range(5)])  # n_curves x n_points
    b = bands.bands("t", "USD", [0, 1], curves, [2.0, 12.0])
    assert list(b["bands"]) == ["5", "25", "50", "75", "95"]
    assert b["bands"]["50"] == [2.0, 12.0] and b["bands"]["25"] == [1.0, 11.0]
    assert b["bands"]["5"] == [0.2, 10.2] and b["real_label"] == "original"


def test_scatter_cap_and_ramp() -> None:
    """1000 points draw 400, the same ones each time, the range of all; the ramp has no blue."""
    from ui.desktop.blocks import scatter
    from ui.desktop.blocks.states import DIVERGING, SEQUENTIAL

    pts = [
        {"x": float(i), "y": float(i), "label": str(i), "group": "g"}
        for i in range(1000)
    ]
    b = {"points": pts, "fit": {"slope": 1, "intercept": 0, "r": 1.0}}
    s = scatter._sample(b)
    assert len(s["points"]) == 400 and s["points"] == scatter._sample(b)["points"]
    assert s["span"] == ((0.0, 999.0), (0.0, 999.0)) and s["n_all"] == 1000
    blue = lambda c: int(c[5:7], 16) > max(int(c[1:3], 16), int(c[3:5], 16))
    assert not any(blue(c) for c in SEQUENTIAL + DIVERGING)  # no blue anywhere


if __name__ == "__main__":
    test_share_positive_and_shade_flag()
    test_pivot_counts_above_it()
    test_beside_and_text_score()
    test_bands_percentiles_of_a_tiny_array()
    test_scatter_cap_and_ramp()
    print("ok")


def test_a_series_with_nothing_inside_the_shared_bins_is_a_flat_zero() -> None:
    """A series the union's clip leaves outside the bins was 0/0, None after JSON, and a
    TypeError in the block check that failed step 16 (2026-10-10)."""
    import numpy as np
    from core.study import blockcheck, blocks

    a, b = np.linspace(0, 1, 2000), np.array([1e9])
    block = blocks.distribution(
        "t", "", np.concatenate([a, b]), None, "n", series={"a": a, "b": b}
    )
    assert block["series"][1]["counts"] == [0.0] * (len(block["bins"]) - 1)
    blockcheck.extensions(block, "x")

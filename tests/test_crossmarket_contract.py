#!/usr/bin/env python3
"""The equity lines of the window take their style from their sign alone, the reference included."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt  # noqa: E402

from ui.desktop.blocks import lines  # noqa: E402


def test_line_style_follows_the_sign_only() -> None:
    """Nine series and a reference: past six the colours repeat but the style does not cycle —
    each ending below zero is dashed, each ending above solid, the reference too."""
    ends = [1, -1, 2, 3, -2, 4, 5, 6, -3]
    series = [
        {"label": str(i), "values": [0.0, float(e)], "role": "real"}
        for i, e in enumerate(ends)
    ]
    series += [
        {"label": "base", "values": [0.0, 7.0], "role": "reference"},
        {"label": "base-", "values": [0.0, -7.0], "role": "reference"},
    ]
    pens = lines._pens({"series": series, "auto_dash_negative": True})
    want = [Qt.DashLine if e < 0 else Qt.SolidLine for e in ends] + [
        Qt.SolidLine,
        Qt.DashLine,
    ]
    assert [style for _, style, _ in pens] == want


if __name__ == "__main__":
    test_line_style_follows_the_sign_only()
    print("ok")

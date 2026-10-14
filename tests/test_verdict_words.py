"""A study column's English verdict words read in Spanish in the table; the raw word still sorts."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.desktop.workspace.tablemodel import Rows  # noqa: E402
from ui.text.verdictwords import verdict_word  # noqa: E402


def test_words_and_sort() -> None:
    """«fails» shows «Falla», «Aprobado» (already Spanish) stays, and sorting reads the raw word."""
    QApplication.instance() or QApplication([])
    model = Rows()
    rows = [
        {"identity": str(i), "name": f"S{i}", "values": [f"S{i}", v], "states": {}}
        for i, v in enumerate(["survives", "Aprobado", "fails"])
    ]
    model.fill(
        rows,
        [
            {
                "id": "crossTF.verdict",
                "group": "Estudio",
                "header": "x",
                "index": 1,
                "union": None,
            }
        ],
        None,
    )
    shown = [model.data(model.index(r, 1)) for r in range(3)]
    assert shown == ["Sobrevive", "Aprobado", "Falla"]
    model.sort(1, Qt.AscendingOrder)
    assert [model.rows[model.order[r]]["values"][1] for r in range(3)] == [
        "Aprobado",
        "fails",
        "survives",
    ]
    assert verdict_word("watch") == "Vigilar" and verdict_word(0.5) == 0.5


if __name__ == "__main__":
    test_words_and_sort()
    print("ok")

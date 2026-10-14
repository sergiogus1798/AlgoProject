"""«Descartar seleccionadas» sends the selected rows' identities; a row without one is skipped."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.desktop.workspace.filters import FiltersStrip  # noqa: E402
from ui.desktop.workspace.table import DataTable  # noqa: E402


def main() -> None:
    """The table is a QTableView: discard() read rows through QTableWidget.item() and crashed."""
    app = QApplication.instance() or QApplication([])
    table = DataTable()
    table.paint(
        [
            {"name": "a", "identity": "id-a", "values": []},
            {"name": "b", "identity": None, "values": []},
        ],
        [],
        [],
    )
    table.selectAll()
    sent: list[tuple[str, dict]] = []
    strip = SimpleNamespace(
        panel=SimpleNamespace(table=table),
        at=("P", "B"),
        say=print,
        send=lambda url, body: sent.append((url, body)),
    )
    FiltersStrip.discard(strip)  # type: ignore[arg-type]
    assert sent == [
        ("filters/discard", {"project": "P", "databank": "B", "identities": ["id-a"]})
    ], sent
    app.processEvents()
    print(
        "ok: descartar seleccionadas manda las identidades y salta la fila sin identidad"
    )


if __name__ == "__main__":
    main()

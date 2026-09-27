"""The run history of one study here, and the two ways to put results side by side."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour, label
from ui.desktop.theme import T


def line(run: dict) -> str:
    """One run as the list prints it.

    Args:
        run: A row of `/api/history`.

    Returns:
        Day, the study's own word, the hash, and «CADUCADO» when today's config would not
        sign it.
    """
    stale = " · CADUCADO" if run["stale"] else ""
    return (f"{run['day']}  {label(run['state'])} «{run['label'] or '—'}»  "
            f"config {run['config_hash']}{stale}")


class History(QFrame):
    """The runs of the study on screen, newest first. One click shows that run; two selected
    and «comparar» shows them side by side; the picker compares with another strategy."""

    picked = Signal(str)            # day
    compare_runs = Signal(str, str)  # day, day
    versus = Signal(str, str)        # strategy, identity

    def __init__(self) -> None:
        """Build the list, the compare button and the strategy picker, empty."""
        super().__init__()
        self.setObjectName("term")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.addWidget(text("HISTORIAL", T["text"], 12, True))
        lay.addWidget(text("Clic: ver esa corrida. Ctrl+clic en dos y «comparar»: una al lado "
                           "de la otra.", T["muted"], 12))
        self.runs = QListWidget()
        self.runs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.runs.itemClicked.connect(lambda it: self.picked.emit(it.data(Qt.UserRole)))
        self.runs.itemSelectionChanged.connect(self._selection)
        lay.addWidget(self.runs, 1)
        self.both = QPushButton("comparar las dos corridas elegidas")
        self.both.clicked.connect(self._compare)
        lay.addWidget(self.both)
        self.skipped = text("", T["faint"], 12)
        lay.addWidget(self.skipped)
        self.rival_title = text("COMPARAR CON OTRA ESTRATEGIA DE ESTE DATABANK", T["text"], 11,
                                True)
        lay.addWidget(self.rival_title)
        self.rival = QComboBox()
        self.rival.setToolTip("Solo las de este databank: el mismo nombre en otro databank es "
                              "otra estrategia (otra identidad).")
        lay.addWidget(self.rival)
        self.go = QPushButton("comparar con esta estrategia")
        self.go.clicked.connect(lambda: self.versus.emit(self.rival.currentText(),
                                                         self.rival.currentData()))
        lay.addWidget(self.go)
        self._selection()

    def fill(self, got: dict, strategies: list[dict] | None) -> None:
        """Replace the list.

        Args:
            got: `/api/history`'s body (`runs`, `skipped`), or `{"error"}`.
            strategies: The databank's other strategies for the picker; None on the
                population page, which hides it.
        """
        self.runs.clear()
        for run in got.get("runs") or []:
            item = QListWidgetItem(line(run))
            item.setData(Qt.UserRole, run["day"])
            item.setForeground(QColor(colour(run["state"])))
            item.setToolTip(f"calculado {run['computed_at']} · config {run['config_hash']}"
                            + (" — calculado con otra configuración que la de hoy"
                               if run["stale"] else ""))
            self.runs.addItem(item)
        if "error" in got:
            self.skipped.setText(got["error"])
        elif not got.get("runs"):
            self.skipped.setText("Ninguna corrida de este estudio en este databank.")
        else:
            self.skipped.setText("")
        passed = [f"{s['day']}: {s['reason']}" for s in got.get("skipped") or []]
        if passed:
            self.skipped.setText("Días con informe que no se muestran:\n" + "\n".join(passed))
        self.rival.clear()
        for s in strategies or []:
            self.rival.addItem(s["strategy"], s["identity"])
        for w in (self.rival_title, self.rival, self.go):
            w.setVisible(strategies is not None)
        self.go.setEnabled(bool(strategies))
        self._selection()

    def mark(self, day: str | None) -> None:
        """Select the run on screen, without emitting a pick.

        Args:
            day: The shown run's day, None for none.
        """
        self.runs.blockSignals(True)
        for i in range(self.runs.count()):
            self.runs.item(i).setSelected(self.runs.item(i).data(Qt.UserRole) == day)
        self.runs.blockSignals(False)
        self._selection()

    def _selection(self) -> None:
        """«comparar» works with exactly two runs chosen."""
        n = len(self.runs.selectedItems())
        self.both.setEnabled(n == 2)
        self.both.setToolTip("Elige exactamente dos corridas (Ctrl+clic)." if n != 2 else
                             "Las dos corridas, misma pestaña abierta en ambas.")

    def _compare(self) -> None:
        """Emit the two chosen days, older on the left."""
        days = sorted(it.data(Qt.UserRole) for it in self.runs.selectedItems())
        self.compare_runs.emit(days[0], days[1])

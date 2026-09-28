"""The rail's drawer: one step's tests, each with its box, state, configuration and run button."""

import httpx
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout)

from ui.desktop import client
from ui.text.glossary import knob, label
from ui.desktop.workspace.railrow import ink, readable, small, value_words, word


def knobs(key: str) -> str:
    """Every knob of a study as its next run reads it, one per line, with its tooltip.

    Args:
        key: Study key.

    Returns:
        The lines, or the reason they could not be read (ui boundary: shown, never raised).
    """
    try:
        got = client.get("config", study=key)
    except httpx.HTTPError as failed:
        return f"El demonio no respondió: {failed}"
    lines = [f"{knob(k['key'])} = {value_words(k['value'])}"
             + (f"   — {k['tip']}" if k["tip"] else "")
             for s in got.get("sections", []) for k in s["knobs"]]
    return "\n".join(lines) or "Sin configuración: este estudio no tiene config.yaml."


class Drawer(QFrame):
    """The tests of the step chosen on the rail. `ticked(n, key, on)` follows a box;
    `ran([{n, key}])` asks to run tests now; `tab_ran(tab)` asks for every ticked test of
    the step's tab."""

    ticked = Signal(str, str, bool)
    ran = Signal(list)
    tab_ran = Signal(str)

    def __init__(self) -> None:
        """Build the empty drawer; `show_step` fills it."""
        super().__init__()
        self.setObjectName("term")
        self.head = small("", "mono")
        self.why = small("")
        self.why.setWordWrap(True)
        self.tab_button = QPushButton("")
        self.tab_button.clicked.connect(lambda: self.tab_ran.emit(self.step["tab"]))
        top = QHBoxLayout()
        top.addWidget(self.head, 1)
        top.addWidget(self.tab_button)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(2)
        self.knobs = QLabel("")
        self.knobs.setObjectName("dim")
        self.knobs.setWordWrap(True)
        self.knobs.hide()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(3)
        lay.addLayout(top)
        lay.addWidget(self.why)
        lay.addLayout(self.grid)
        lay.addWidget(self.knobs)
        self.step: dict = {}

    def show_step(self, step: dict, ticks: dict[tuple[str, str], bool], sealed: bool) -> None:
        """Lay out one step's tests.

        Args:
            step: One step as GET /api/workflow sends it.
            ticks: (step, study) → ticked.
            sealed: Whether the ledger's door is shut: a sealed step's tests show no number
                and no verdict, only that they ran.
        """
        self.step = step
        while self.grid.count():
            gone = self.grid.takeAt(0).widget()
            gone.hide()          # hidden first, or it paints under the new ones until deleted
            gone.deleteLater()
        self.knobs.hide()
        self.head.setText(f"PASO {step['n']} · {label(step['title'])} — "
                          f"{word(step['state']).upper()}")
        self.head.setStyleSheet(f"color: {ink(step['state'])};")
        self.why.setText(label(step["why"]) if step["why"] else "")
        self.tab_button.setVisible(bool(step["tab"]))
        self.tab_button.setText(f"▶ correr los marcados de «{step['tab']}»")
        if step["kind"] == "sqx":
            self.grid.addWidget(small("Tarea de SQX: la ventana la enseña y no la lanza "
                                      "(«Continuar workflow», más adelante)."), 0, 0, 1, 5)
        for row, test in enumerate(step["tests"], start=1):
            self.add_test(row, step["n"], test, ticks.get((step["n"], test["key"]), False),
                          sealed and step["n"] in ("17", "18", "19"), step["kind"] != "sqx")

    def add_test(self, row: int, n: str, test: dict, on: bool, sealed: bool,
                 playable: bool) -> None:
        """One test's row: box, title, state, configuration, its drawer button and ▶.

        Args:
            row: Grid row.
            n: The step's number.
            test: One entry of the step's `tests`.
            on: Whether it is ticked.
            sealed: Whether its result must not be described.
            playable: False on an SQX step: no ▶, its analysis runs from the panel.
        """
        box = QCheckBox(label(test["title"]).replace("&", "&&"))   # «&» is Qt's mnemonic
        box.setChecked(on)
        box.setEnabled(test["runnable"])
        box.toggled.connect(lambda v, k=test["key"]: self.ticked.emit(n, k, v))
        state = "sealed" if sealed and test["state"] == "done" else test["state"]
        why = ("hecho; el resultado se lee cuando 17, 18 y 19 estén los tres"
               if state == "sealed" else test["why"])
        self.grid.addWidget(box, row, 0)
        word_label = QLabel(word(state))
        word_label.setObjectName("mono")
        word_label.setStyleSheet(f"color: {ink(state)};")
        word_label.setMinimumWidth(90)
        self.grid.addWidget(word_label, row, 1)
        cost = f"⚠ {test['spends'].upper()}   ·   " if test["spends"] else ""   # first: never cut
        self.grid.addWidget(small(f"{cost}{readable(test['config'])}   ·   {label(why)}"), row, 2)
        show = QPushButton("configuración")
        show.clicked.connect(lambda _=False, k=test["key"], t=test["title"]: self.reveal(k, t))
        self.grid.addWidget(show, row, 3)
        self.grid.setColumnStretch(2, 1)
        if not playable:
            return
        run = QPushButton("▶")
        run.setFixedWidth(26)
        run.setEnabled(test["runnable"] and test["state"] != "running")
        run.setToolTip(label(f"Correr solo «{test['title']}»"))
        run.clicked.connect(lambda _=False, k=test["key"]: self.ran.emit([{"n": n, "key": k}]))
        self.grid.addWidget(run, row, 4)

    def reveal(self, key: str, title: str) -> None:
        """Show every knob of one study under the tests, or hide them on a second press."""
        text = f"{label(title)} — configuración\n{knobs(key)}"
        self.knobs.setVisible(not (self.knobs.isVisible() and self.knobs.text() == text))
        self.knobs.setText(text)

"""The databank panel's filters strip: AND rows over real columns, discards, and the ledger (22 §7.1)."""

import httpx
import numpy as np
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QWidget)

from ui.desktop import client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.workspace.filtersaved import SavedFilters

# The operators a metric's kind admits, as the daemon spells them → what the owner reads.
OPS = {"numeric": [(">", ">"), ("<", "<"), (">=", "≥"), ("<=", "≤"), ("=", "="),
                   ("entre", "entre")],
       "text": [("=", "=")],
       "dist": [("dentro", "mediana dentro del intervalo"),
                ("fuera", "mediana fuera del intervalo")]}


def shown_metric(m: dict) -> str:
    """A metric as the dropdown lists it: the words the daemon gave (`evaluate.named`), the
    glossary's for an older daemon that sent none."""
    return m.get("label") or label(m["key"])


def typed(value: object) -> str:
    """A saved value as the box shows it, so it reads back the same: exact, never scientific."""
    return np.format_float_positional(value, trim="-") if isinstance(value, float) else str(value)


class FilterRow(QWidget):
    """One condition: metric, operator, value (two for «entre», an interval % for a
    distribution) and «×». `gone` when removed."""

    gone = Signal(object)

    def __init__(self, metrics: list[dict]) -> None:
        """Build the row over the metrics the daemon offered."""
        super().__init__()
        self.metrics = {m["key"]: m for m in metrics}
        # `column`, never `metric`: that name hides QPaintDevice.metric() and the first paint
        # segfaults (knowhow/eng/qt-painting-traps.md)
        self.column, self.op = QComboBox(), QComboBox()
        self.column.setMinimumWidth(320)
        for m in metrics:
            self.column.addItem(shown_metric(m), m["key"])
            self.column.setItemData(self.column.count() - 1, m.get("reading") or
                                    f"{num(m['n'])} estrategias tienen valor", Qt.ToolTipRole)
        self.column.currentIndexChanged.connect(self.retype)
        self.value, self.upper = QLineEdit(), QLineEdit()
        for w in (self.value, self.upper):
            w.setFixedWidth(110)
        self.op.currentIndexChanged.connect(self.reshape)
        drop = QPushButton("×")
        drop.setFixedWidth(28)
        drop.clicked.connect(lambda: self.gone.emit(self))
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        for w in (self.column, self.op, self.value, self.upper, drop):
            lay.addWidget(w)
        lay.addStretch(1)
        self.retype()

    def kind(self) -> str:
        """numeric, text or dist: which operators the chosen metric admits."""
        m = self.metrics.get(self.column.currentData(), {"kind": "metric", "numeric": True})
        return "dist" if m["kind"] == "dist" else ("numeric" if m["numeric"] else "text")

    def retype(self) -> None:
        """Offer the chosen metric's operators."""
        self.op.clear()
        for code, words in OPS[self.kind()]:
            self.op.addItem(words, code)

    def reshape(self) -> None:
        """Two value boxes for «entre», an interval % for a distribution."""
        code = self.op.currentData()
        self.upper.setVisible(code == "entre")
        self.value.setPlaceholderText("intervalo %: 50, 80, 90, 98" if code in ("dentro", "fuera")
                                      else ("desde" if code == "entre" else "valor"))
        self.upper.setPlaceholderText("hasta")

    def spec(self) -> dict:
        """The row as the daemon reads it."""
        code, text = self.op.currentData(), self.value.text().strip().replace(",", ".")
        value = [text, self.upper.text().strip().replace(",", ".")] if code == "entre" else text
        return {"metric": self.column.currentData(), "op": code, "value": value}

    def put(self, row: dict) -> None:
        """Show a saved row."""
        self.column.setCurrentIndex(max(self.column.findData(row["metric"]), 0))
        self.op.setCurrentIndex(max(self.op.findData(row["op"]), 0))
        low, high = row["value"] if isinstance(row["value"], list) else (row["value"], "")
        self.value.setText(typed(low))
        self.upper.setText(typed(high))


class FiltersStrip(QFrame):
    """Below the panel's header: the rows (AND), Aplicar, the saved list, «Quitar filtros» and
    «Descartar seleccionadas». It follows the panel's databank on its own, hides what is set
    aside through `panel.set_hidden` (which re-aggregates the visible ids) and reloads the
    funnel. Nothing here touches SQX: the databank there stays whole."""

    def __init__(self, panel: QWidget, funnel: QWidget | None = None) -> None:
        """Build the strip over a `workspace.panel.Panel` and, optionally, its `Funnel`."""
        super().__init__()
        self.setObjectName("term")
        self.panel, self.funnel, self.at, self.offer = panel, funnel, ("", ""), []
        self.anonymous = 0
        kicker = QLabel("FILTROS")
        kicker.setObjectName("kicker")
        add, apply_, clear, drop = (QPushButton("+ condición"), QPushButton("▶ Aplicar"),
                                    QPushButton("Quitar filtros"),
                                    QPushButton("Descartar seleccionadas"))
        apply_.setToolTip("Aplica todas las condiciones a la vez (AND) a lo que se ve. Se apunta "
                          "en el Ledger como una búsqueda. No toca SQX.")
        drop.setToolTip("Oculta las filas seleccionadas; también se apunta en el Ledger.")
        clear.setToolTip("Vuelve a mostrar todo. Lo ya apuntado en el Ledger se queda: se miró.")
        add.clicked.connect(lambda: self.add())
        apply_.clicked.connect(self.apply)
        clear.clicked.connect(self.clear)
        drop.clicked.connect(self.discard)
        self.saved = SavedFilters()
        self.saved.chosen.connect(self.show_rows)
        self.saved.said.connect(self.say)
        self.saved.store.clicked.connect(lambda: self.saved.save(self.rows()))
        self.said = QLabel("")
        self.said.setObjectName("dim")
        self.said.setWordWrap(True)
        head = QHBoxLayout()
        for w in (kicker, add, apply_, clear, drop):
            head.addWidget(w)
        head.addStretch(1)
        head.addWidget(self.saved)
        self.box = QVBoxLayout()
        self.box.setSpacing(2)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(3)
        lay.addLayout(head)
        lay.addLayout(self.box)
        lay.addWidget(self.said)
        panel.table.model().modelReset.connect(lambda: QTimer.singleShot(0, self.follow))

    def bank(self) -> tuple[str, str]:
        """The project and the databank the panel shows, or '' when it shows no live one."""
        spec = self.panel.sub_spec() if self.panel.live else {}
        return self.panel.project, ("" if spec.get("blocked") else spec.get("databank", ""))

    def follow(self) -> None:
        """The panel painted a table: read this databank's metrics and discards if it changed."""
        at = self.bank()
        self.setEnabled(bool(at[1]))
        if at == self.at or not at[1]:
            return
        self.at = at
        try:
            got = client.get("filters/metrics", project=at[0], databank=at[1])
            state = client.get("filters/state", project=at[0], databank=at[1])
        except httpx.HTTPError as failed:
            self.say(f"El demonio no respondió: {failed}")
            return
        self.offer, self.anonymous = got.get("metrics", []), got.get("anonymous") or 0
        self.show_rows([])
        self.hide_ids(state)
        self.say(got.get("error") or got.get("refused") or self.counts(state))

    def counts(self, state: dict) -> str:
        """The databank's discards in one line, and the rows no filter can hide."""
        loose = state.get("anonymous") or self.anonymous
        tail = f" · {num(loose)} sin identidad, no filtrables" if loose else ""
        if not state.get("steps"):
            return (f"{self.at[1]}: sin filtros · {num(len(self.offer))} métricas filtrables "
                    f"(OOS2 no){tail}")
        return (f"{self.at[1]}: {num(state['entered'])} → {num(state['remaining'])} visibles · "
                f"{num(state['hidden'])} descartadas · {num(len(state['steps']))} filtro(s) o "
                f"borrado(s){tail}")

    def add(self, row: dict | None = None) -> None:
        """One more condition, empty or a saved one."""
        line = FilterRow(self.offer)
        line.gone.connect(lambda w: (self.box.removeWidget(w), w.deleteLater()))
        if row:
            line.put(row)
        self.box.addWidget(line)

    def rows(self) -> list[dict]:
        """Every condition on screen."""
        return [self.box.itemAt(i).widget().spec() for i in range(self.box.count())
                if isinstance(self.box.itemAt(i).widget(), FilterRow)]

    def show_rows(self, rows: list[dict]) -> None:
        """Replace the conditions on screen; one empty row when there are none."""
        while self.box.count():
            self.box.takeAt(0).widget().deleteLater()
        for row in rows or [None]:
            self.add(row)

    def send(self, path: str, body: dict) -> None:
        """POST to the daemon, then hide what it says is set aside and say how it went."""
        try:
            got = client.post(path, body)
        except httpx.HTTPError as failed:
            self.say(f"El demonio no respondió: {failed}")
            return
        if "error" in got:
            self.say(got["error"])
            return
        self.hide_ids(got)
        done = self.counts(got)
        if "ledger" in got:
            led = got["ledger"]
            done = (f"{num(got['n_in'])} → {num(got['n_out'])}"
                    + (f" ({num(got['blank'])} sin valor, siguen visibles)" if got.get("blank") else "")
                    + f" · apuntado en el Ledger: {led['study']}, paso {num(led['step'])}, "
                    f"{led['segment']}  ·  {done}")
        self.say(done)

    def hide_ids(self, state: dict) -> None:
        """Hand the hidden identities to the panel and reload the funnel."""
        self.panel.set_hidden(set(state.get("hidden_ids", [])))
        if self.funnel is not None:
            self.funnel.load(self.at[0])

    def apply(self) -> None:
        """«Aplicar»: the AND of the rows on what is visible."""
        self.send("filters/apply", {"project": self.at[0], "databank": self.at[1],
                                    "rows": self.rows()})

    def discard(self) -> None:
        """«Descartar seleccionadas»: the selected rows' identities, set aside by hand."""
        table = self.panel.table
        ids = sorted({table.rows[table.item(i.row(), 0).data(Qt.UserRole)]["identity"]
                      for i in table.selectionModel().selectedRows()} - {None})
        if not ids:
            self.say("Selecciona filas con identidad en la tabla para descartarlas")
            return
        self.send("filters/discard", {"project": self.at[0], "databank": self.at[1],
                                      "identities": ids})

    def clear(self) -> None:
        """«Quitar filtros»: everything visible again."""
        self.send("filters/clear", {"project": self.at[0], "databank": self.at[1]})

    def say(self, text: str) -> None:
        """One line under the rows."""
        self.said.setText(text)

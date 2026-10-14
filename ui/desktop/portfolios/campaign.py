"""PORTFOLIOS › Campaña: the workflows the campaign saved, each one's funnel, time per phase and strategies."""

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.theme import T
from ui.text.numbers import num

FLOWS = (("Fecha", "Cuándo se guardó el workflow."), ("Activo", "El símbolo de la celda."),
         ("TF", "El timeframe de la celda."), ("Plantilla", "La plantilla de la celda; «simple_long» es una Simple Strategy sin plantilla."),
         ("Dir.", "Una sola dirección por estrategia: long o short."),
         ("Estado", "done: terminó; failed: falló tres veces; interrupted: se paró antes del final."),
         ("Min", "Minutos de reloj de todos los pasos, del 6 al 25."),
         ("Finales", "Las estrategias que salieron del paso 25: las que se guardaron en el archivo."))
STEPS = (("Paso", "El número del WORKFLOW."), ("Tipo", "sqx: corre en StrategyQuant; python: un estudio; judge: aplica el criterio."),
         ("Seg", "Segundos de reloj que tardó."), ("Qué hizo", "Lo que dijo el autopiloto, con «entran → quedan» donde cribó."))
STRATS = (("Final", "La estrategia superviviente, sin stop por operación: lo que se llevaría a probar."),
          ("Madre", "La estrategia de SQX de la que sale: casi todos los estudios llevan su firma."))
INTRO = ("Cada workflow completo que la campaña guardó, con TODOS sus resultados. Elige uno para ver su embudo y cuánto "
         "tardó cada fase; elige estrategias y «Abrir» las enseña en Estrategia, una a una, con «anterior / siguiente».")


def _table(cols: tuple, multi: bool = False) -> QTableWidget:
    """A read-only table with the column tooltips."""
    t = QTableWidget(0, len(cols))
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.ExtendedSelection if multi else QAbstractItemView.SingleSelection)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.verticalHeader().hide()
    t.horizontalHeader().setStretchLastSection(True)
    t.setStyleSheet("font-size: 14px;")
    for i, (head, tip) in enumerate(cols):
        item = QTableWidgetItem(head)
        item.setToolTip(tip)
        t.setHorizontalHeaderItem(i, item)
    return t


def _fill(t: QTableWidget, rows: list[tuple], tips: list[str] | None = None) -> None:
    """Replace a table's rows."""
    t.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            item = QTableWidgetItem(str(v))
            if tips:
                item.setToolTip(tips[i])
            t.setItem(i, j, item)
    t.resizeColumnsToContents()


class CampaignPage(QFrame):
    """List on the left (filterable); on the right the chosen workflow's funnel, steps and strategies.
    `campaign_requested(workflow, names, index)` is what the shell wires to the Estrategia page."""

    campaign_requested = Signal(str, list, int)

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch) -> None:
        """Build it empty; `reload` reads the daemon.

        Args:
            fetch: GET a daemon route, never raising; injectable for a test.
        """
        super().__init__()
        self.setObjectName("term")
        self.fetch, self.rows, self.shown, self.flow = fetch, [], [], {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.addWidget(QLabel("Campaña", objectName="h1"))
        lay.addWidget(text(INTRO, T["muted"], 13))
        self.said = text("", T["muted"], 13)
        lay.addWidget(self.said)
        self.find = QLineEdit()
        self.find.setPlaceholderText("Filtrar por activo, plantilla o timeframe…")
        self.find.setToolTip("Escribe parte del activo (NIKKEI225), de la plantilla o del timeframe (M30).")
        self.find.textChanged.connect(self._filter)
        lay.addWidget(self.find)
        self.table = _table(FLOWS)
        self.table.itemSelectionChanged.connect(self._picked)
        self.funnel = text("", T["text"], 15)
        self.steps, self.strats = _table(STEPS), _table(STRATS, multi=True)
        self.strats.itemDoubleClicked.connect(lambda *_: self._open())
        self.go = QPushButton("Abrir en Estrategia")
        self.go.setToolTip("Abre las estrategias elegidas con todos sus resultados, una tras otra. Con una sola "
                           "elegida, «anterior / siguiente» recorre las demás del workflow. No calcula nada.")
        self.go.clicked.connect(self._open)
        self.kept = text("", T["muted"], 12)
        right = QWidget()
        side = QVBoxLayout(right)
        side.setContentsMargins(12, 0, 0, 0)
        for w in (QLabel("Embudo", objectName="mono"), self.funnel, QLabel("Tiempo por fase", objectName="mono")):
            side.addWidget(w)
        side.addWidget(self.steps, 3)
        side.addWidget(QLabel("Estrategias", objectName="mono"))
        side.addWidget(self.strats, 2)
        row = QHBoxLayout()
        row.addWidget(self.kept, 1)
        row.addWidget(self.go)
        side.addLayout(row)
        split = QSplitter()
        split.addWidget(self.table)
        split.addWidget(right)
        split.setSizes([700, 840])
        lay.addWidget(split, 1)

    def reload(self) -> None:
        """Read the saved workflows again."""
        got = self.fetch("campaign/list")
        if "error" in got:
            return self.said.setText(f'<span style="color:{colour("fail")}">{got["error"]}</span>')
        self.rows = got["workflows"]
        self.said.setText(f"{num(len(self.rows))} workflow{'s' * (len(self.rows) != 1)} guardado"
                          f"{'s' * (len(self.rows) != 1)}." if self.rows else
                          "Todavía no hay ninguno: la campaña guarda uno al terminar cada celda.")
        self._filter()

    def _filter(self) -> None:
        """Show the rows whose asset, template or timeframe holds what was typed."""
        word = self.find.text().strip().lower()
        self.shown = [r for r in self.rows if word in f"{r['symbol']} {r['template']} {r['timeframe']}".lower()]
        _fill(self.table, [(r["when"], r["symbol"], r["timeframe"], r["template"], r["direction"], r["state"],
                            num(r["minutes"]), num(r["finalists"])) for r in self.shown],
              [r["name"] for r in self.shown])
        if self.shown:
            self.table.selectRow(0)

    def _picked(self) -> None:
        """A workflow was chosen: its funnel, its phases and its strategies."""
        picked = self.table.selectionModel().selectedRows()
        if not picked:
            return
        got = self.fetch("campaign/show", workflow=self.shown[picked[0].row()]["name"])
        if "error" in got:
            return self.said.setText(f'<span style="color:{colour("fail")}">{got["error"]}</span>')
        self.flow = got
        counts = [c for r in got["steps"] for c in r["counts"]]
        self.funnel.setText("  ›  ".join(f"<b>{c['what']}</b> {num(c['in'])} → {num(c['out'])}" for c in counts)
                            or "sin cifras")
        self.funnel.setToolTip("Cada tramo es «qué se cribó: cuántas entraron → cuántas quedaron», en el orden en que "
                               "corrió el workflow.")
        _fill(self.steps, [(r["step"], r["kind"], num(r["seconds"]), r["what"]) for r in got["steps"]])
        _fill(self.strats, [(s["name"], s["mother"]) for s in got["strategies"]])
        lost = got["not_kept"]
        self.kept.setText(f"{num(len(lost))} cosas no se copiaron (ficheros grandes o intermedios)." if lost else "")
        self.kept.setToolTip("\n".join(f"{x['path']}: {x['reason']}" for x in lost[:30]))
        if got["strategies"]:
            self.strats.selectRow(0)

    def _open(self) -> None:
        """«Abrir»: the chosen strategies, or the whole workflow from the chosen one when only one is."""
        names = [s["name"] for s in self.flow.get("strategies", [])]
        picked = sorted(i.row() for i in self.strats.selectionModel().selectedRows())
        if not picked:
            return
        if len(picked) == 1:
            return self.campaign_requested.emit(self.flow["name"], names, picked[0])
        self.campaign_requested.emit(self.flow["name"], [names[i] for i in picked], 0)

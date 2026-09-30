"""«Registro de búsquedas»: one study's searches, its funnel and the history it has already spent."""

import httpx
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout)

from ui.desktop import client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C, T

FUNNEL = [("cuándo", "ts"), ("paso", "step"), ("tramo", "segment"), ("entran", "n_in"),
          ("salen", "n_out"), ("conserva", "kept"), ("criterio", "criterion")]
SEARCHES = [("cuándo", "ts"), ("paso", "step"), ("tramo", "segment"), ("criterio", "criterion"),
            ("entran", "n_in"), ("salen", "n_out"), ("hash", "config_hash"),
            ("lanzado por", "launched_by"), ("nota", "note")]
SEGMENTS = ["tramo", "ventana", "lecturas", "pasos que lo leyeron",
            "reservado (sólo agente autónomo)"]
EXPLAIN = ("Una línea por búsqueda que miró datos y redujo una población, en todo el estudio "
           "(activo + timeframe + familia). Sólo lectura: el ledger no se edita. Tres "
           "supervivientes de 10.000 no valen lo que tres de 50.")
WHY = ("Por qué importa: cada mirada a los datos es una prueba más, y cuantas más pruebas, más "
       "fácil es que el mejor resultado sea suerte. Este registro las cuenta todas — las de los "
       "estudios, las del SQX y los filtros que aplicas en la ventana («lanzado por: ventana») — "
       "para que el Sharpe desinflado sepa cuánto se ha buscado.")
WINDOW = "ventana"          # `launched_by` of the rows the window's filters write (plan 24, F6)


def cell(value: object) -> str:
    """One value as a table prints it: numbers through `num` (a step keeps no trailing .0),
    «—» for nothing; anything else as its text."""
    return num(value) if value is None or isinstance(value, (int, float, str)) else str(value)


def when(ts: str) -> str:
    """A ledger timestamp to the minute: ISO with or without zone, or a bare backfill date."""
    return ts[:16].replace("T", " ")


def table(headers: list[str], rows: list[list[str]], tips: list[str] | None = None) -> QTableWidget:
    """A read-only table.

    Args:
        headers: Column titles.
        rows: Cell texts.
        tips: One tooltip per row, optional.

    Returns:
        The widget.
    """
    t = QTableWidget(len(rows), len(headers))
    t.setHorizontalHeaderLabels([label(h) for h in headers])
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            item = QTableWidgetItem(text)
            if tips:
                item.setToolTip(tips[r])
            t.setItem(r, c, item)
    t.resizeColumnsToContents()
    t.horizontalHeader().setStretchLastSection(True)
    return t


class Ledger(QFrame):
    """The global search ledger of one study, read-only, through `/api/ledger`."""

    def __init__(self) -> None:
        """Build the header, the spent summary and the two tables."""
        super().__init__(objectName="term")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        head = QHBoxLayout()
        head.addWidget(QLabel("Registro de búsquedas", objectName="h1"))
        head.addWidget(QLabel("ESTUDIO", objectName="kicker"))
        self.pick = QComboBox(minimumWidth=380)
        self.pick.setToolTip("Un estudio es un activo, un timeframe y una familia de plantillas: "
                             "la unidad a la que se le debe la corrección por multiplicidad.")
        self.pick.activated.connect(lambda: self.load(self.pick.currentText()))
        head.addWidget(self.pick)
        head.addStretch(1)
        lay.addLayout(head)
        box = QFrame()
        box.setStyleSheet(f"QFrame {{ border: 1px solid {T['rule']}; border-radius: 4px; }} "
                          "QLabel { border: none; }")
        inside = QVBoxLayout(box)
        inside.setContentsMargins(12, 8, 12, 8)
        inside.addWidget(QLabel(EXPLAIN, wordWrap=True, styleSheet="font-weight: 600;"))
        inside.addWidget(QLabel(WHY, objectName="dim", wordWrap=True))
        lay.addWidget(box)
        self.window_rows = QLabel("", objectName="dim", wordWrap=True)
        lay.addWidget(self.window_rows)
        self.blind = QLabel("", wordWrap=True)
        self.trials = QLabel("", objectName="mono", wordWrap=True)
        lay.addWidget(self.blind)
        lay.addWidget(self.trials)
        self.tabs = QTabWidget()
        lay.addWidget(self.tabs, 1)

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Load the newest study the first time the zone is shown.

        Args:
            event: Qt's show event, unused.
        """
        if not self.pick.count():
            self.load("")

    def load(self, study: str) -> None:
        """Read one study from the daemon, or say why not.

        Args:
            study: Its id; empty for the one written last.
        """
        try:
            data = client.get("ledger", study=study)
        except httpx.HTTPError as down:
            self.blind.setText(f"demonio no responde: {type(down).__name__}")
            return
        if "error" in data:
            self.blind.setText(data["error"])
            return
        self.show_ledger(data)

    def show_ledger(self, data: dict) -> None:
        """Paint one study.

        Args:
            data: What `/api/ledger` returned.
        """
        self.pick.clear()
        self.pick.addItems(data["studies"])
        self.pick.setCurrentText(data["study"] or "")
        spent = data["spent"]
        self.tabs.clear()
        if not spent:
            self.blind.setText("sin búsquedas registradas todavía")
            self.trials.setText("")
            self.window_rows.setText("")
            return
        blind = spent["blind"]
        steps = " · ".join(f"{s} {'hecho' if ran else 'pendiente'}" for s, ran in blind["done"].items())
        colour = C["promising"] if blind["open"] else C["weak"]
        self.blind.setText(f"PASOS 17, 18 Y 19 · {steps}\n{blind['text']}")
        self.blind.setStyleSheet(f"color: {colour}; font-weight: 600;")
        pooled = spent["trials"]
        self.trials.setText(pooled["error"] if "error" in pooled else
                            f"PROBADO EN TOTAL · N = {num(pooled['n'])} candidatos en "
                            f"{num(pooled['searches'])} búsqueda(s) · σ = {num(pooled['sigma'])} "
                            f"({pooled['unit']}) — la σ que necesita el Sharpe desinflado")
        self.trials.setToolTip("N y σ agrupan exactamente todas las búsquedas que registraron "
                               "la distribución de sus candidatos. Cuanto mayor N, más alto el "
                               "listón que tiene que superar el mejor Sharpe.")
        self.tabs.addTab(self.funnel(data["funnel"], data["rows"]), "Embudo")
        self.tabs.addTab(self.spent(spent), "Historia gastada")
        self.tabs.addTab(self.searches(data["rows"]), "Búsquedas")
        mine = sum(1 for r in data["rows"] if r.get("launched_by") == WINDOW)
        self.window_rows.setText(
            f"{num(mine)} de {num(len(data['rows']))} búsquedas de este estudio son filtros "
            "aplicados o borrados a mano en la ventana; su criterio sale en violeta."
            if mine else "Ningún filtro de la ventana en este estudio todavía: cuando apliques "
                         "uno en «Proyecto», su fila aparece aquí como cualquier búsqueda.")

    def searches(self, rows: list[dict]) -> QTableWidget:
        """Every search of the study, the window's own filters marked in the accent colour.

        Args:
            rows: `/api/ledger` `rows`.

        Returns:
            The table.
        """
        t = table([h for h, _ in SEARCHES],
                  [[when(r[k]) if k == "ts" else cell(r[k]) for _, k in SEARCHES] for r in rows],
                  [f"umbrales: {r['thresholds']}\nnota: {r['note']}" for r in rows])
        for i, r in enumerate(rows):
            if r.get("launched_by") == WINDOW:
                for c in range(t.columnCount()):
                    t.item(i, c).setForeground(QColor(C["accent"]))
        return t

    def funnel(self, funnel: list[dict], rows: list[dict]) -> QTableWidget:
        """The funnel, one row per search, the share kept coloured.

        Args:
            funnel: `/api/ledger` `funnel`.
            rows: The searches, for each row's note on hover.

        Returns:
            The table.
        """
        t = table([h for h, _ in FUNNEL],
                  [[when(f[k]) if k == "ts" else num(round(f[k] * 100, 1), "%")
                    if k == "kept" and f[k] is not None
                    else cell(f[k]) for _, k in FUNNEL] for f in funnel],
                  [f"{r['criterion']}\nnota: {r['note']}" for r in rows])
        for r, f in enumerate(funnel):
            if rows[r].get("launched_by") == WINDOW:
                t.item(r, len(FUNNEL) - 1).setForeground(QColor(C["accent"]))
            share = f["kept"] if f["kept"] is not None else 1
            colour = C["dead"] if share < 0.5 else C["weak"] if share < 1 else T["muted"]
            t.item(r, 5).setForeground(QColor(colour))
            t.item(r, 5).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return t

    def spent(self, spent: dict) -> QTableWidget:
        """Every declared segment: its window, how often it was read, by whom, for whom kept.

        Args:
            spent: `/api/ledger` `spent`.

        Returns:
            The table; a reserved segment still virgin is green, one already read amber.
        """
        virgin = spent["virgin"]
        if "error" in virgin:
            return table(["tramo"], [[virgin["error"]]])
        by = {s["segment"]: s["steps"] for s in spent["segments"]}
        names = list(virgin)
        t = table(SEGMENTS, [[n, f"{virgin[n]['from']} → {virgin[n]['to']}",
                              f"{num(virgin[n]['reads'])}×",
                              ", ".join(cell(s) for s in by.get(n, [])) or "ninguno",
                              ", ".join(virgin[n]["reserved_for"] or []) or "—"]
                             for n in names])
        for r, n in enumerate(names):
            if virgin[n]["reserved_for"]:
                colour = C["promising"] if virgin[n]["reads"] == 0 else C["weak"]
                t.item(r, 2).setForeground(QColor(colour))
                t.item(r, 2).setToolTip("Cuántas veces se ha leído el tramo. Informativo: "
                                        "sólo un agente autónomo tiene prohibido mirarlo.")
        return t

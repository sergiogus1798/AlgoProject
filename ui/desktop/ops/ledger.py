"""The ledger zone: one study's searches, its funnel and the history it has already spent."""

import httpx
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout)

from ui.desktop import client
from ui.desktop.theme import C, T

FUNNEL = [("cuándo", "ts"), ("paso", "step"), ("tramo", "segment"), ("entran", "n_in"),
          ("salen", "n_out"), ("conserva", "kept"), ("criterio", "criterion")]
SEARCHES = [("cuándo", "ts"), ("paso", "step"), ("tramo", "segment"), ("criterio", "criterion"),
            ("entran", "n_in"), ("salen", "n_out"), ("hash", "config_hash"),
            ("lanzado por", "launched_by"), ("nota", "note")]
SEGMENTS = ["tramo", "ventana", "lecturas", "pasos que lo leyeron", "reservado para"]
EXPLAIN = ("Una línea por búsqueda que miró datos y redujo una población, en todo el estudio "
           "(activo + timeframe + familia). Sólo lectura: el ledger no se edita. Tres "
           "supervivientes de 10.000 no valen lo que tres de 50.")


def cell(value: object) -> str:
    """One value as a table prints it: steps without a trailing .0, «—» for nothing."""
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


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
    t.setHorizontalHeaderLabels(headers)
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
        head.addWidget(QLabel("Ledger", objectName="h1"))
        head.addWidget(QLabel("ESTUDIO", objectName="kicker"))
        self.pick = QComboBox(minimumWidth=380)
        self.pick.setToolTip("Un estudio es un activo, un timeframe y una familia de plantillas: "
                             "la unidad a la que se le debe la corrección por multiplicidad.")
        self.pick.activated.connect(lambda: self.load(self.pick.currentText()))
        head.addWidget(self.pick)
        head.addStretch(1)
        lay.addLayout(head)
        lay.addWidget(QLabel(EXPLAIN, objectName="dim", wordWrap=True))
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
            return
        blind = spent["blind"]
        steps = " · ".join(f"{s} {'hecho' if ran else 'pendiente'}" for s, ran in blind["done"].items())
        colour = C["promising"] if blind["open"] else C["weak"]
        self.blind.setText(f"PUERTA CIEGA DEL PASO 20 · {steps}\n{blind['text']}")
        self.blind.setStyleSheet(f"color: {colour}; font-weight: 600;")
        pooled = spent["trials"]
        self.trials.setText(pooled["error"] if "error" in pooled else
                            f"PROBADO EN TOTAL · N = {pooled['n']} candidatos en "
                            f"{pooled['searches']} búsqueda(s) · σ = {pooled['sigma']:.4f} "
                            f"({pooled['unit']}) — la σ que necesita el Sharpe desinflado")
        self.trials.setToolTip("N y σ agrupan exactamente todas las búsquedas que registraron "
                               "la distribución de sus candidatos. Cuanto mayor N, más alto el "
                               "listón que tiene que superar el mejor Sharpe.")
        self.tabs.addTab(self.funnel(data["funnel"], data["rows"]), "Embudo")
        self.tabs.addTab(self.spent(spent), "Historia gastada")
        self.tabs.addTab(table([h for h, _ in SEARCHES],
                               [[when(r[k]) if k == "ts" else cell(r[k]) for _, k in SEARCHES]
                                for r in data["rows"]],
                               [f"umbrales: {r['thresholds']}\nnota: {r['note']}"
                                for r in data["rows"]]), "Búsquedas")

    def funnel(self, funnel: list[dict], rows: list[dict]) -> QTableWidget:
        """The funnel, one row per search, the share kept coloured.

        Args:
            funnel: `/api/ledger` `funnel`.
            rows: The searches, for each row's note on hover.

        Returns:
            The table.
        """
        t = table([h for h, _ in FUNNEL],
                  [[when(f[k]) if k == "ts" else f"{f[k]:.1%}" if k == "kept" and f[k] is not None
                    else cell(f[k]) for _, k in FUNNEL] for f in funnel],
                  [f"{r['criterion']}\nnota: {r['note']}" for r in rows])
        for r, f in enumerate(funnel):
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
                              f"{virgin[n]['reads']}×",
                              ", ".join(cell(s) for s in by.get(n, [])) or "ninguno",
                              ", ".join(virgin[n]["reserved_for"] or []) or "—"]
                             for n in names])
        for r, n in enumerate(names):
            if virgin[n]["reserved_for"]:
                colour = C["promising"] if virgin[n]["reads"] == 0 else C["weak"]
                t.item(r, 2).setForeground(QColor(colour))
                t.item(r, 2).setToolTip("Tramo reservado: cada lectura lo gasta. Cero es "
                                        "el único valor que lo deja virgen.")
        return t

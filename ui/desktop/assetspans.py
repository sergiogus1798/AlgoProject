"""One asset's windows: its data, the three segments, the MC Retest ranges and the Cross Market."""

from PySide6.QtCore import QDate, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDateEdit, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.assetcard import cell, clear, fit, grid, send, val
from ui.desktop.assetforms import FIXED_FIRST, MarketBox, TextBox, now, word
from ui.desktop.theme import C

EMPTY = QDate(1970, 1, 1)   # the date edit's floor, shown as «sin decidir»: `null` in the file
TINT = {"family": C["accent"], "structural": C["promising"]}   # a group's background, faint


def qdate(bound: object, end: bool) -> QDate:
    """One segment bound — a year, an ISO date or None — as the day it means, or EMPTY."""
    if bound is None:
        return EMPTY
    if isinstance(bound, int):
        return QDate(bound, 12, 31) if end else QDate(bound, 1, 1)
    return QDate.fromString(str(bound), "yyyy-MM-dd")


def bound_text(day: QDate, end: bool) -> str:
    """A picked day as `_policy.yaml` writes it: a whole year when the day is its edge.

    Args:
        day: What the selector holds.
        end: True for the closing bound.

    Returns:
        "" for «sin decidir» (written `null`), "2008" for 1 January of an opening bound or
        31 December of a closing one — the file's own convention —, the ISO date otherwise.
    """
    if day == EMPTY:
        return ""
    edge = (12, 31) if end else (1, 1)
    whole = (day.month(), day.day()) == edge
    return str(day.year()) if whole else day.toString("yyyy-MM-dd")


def picker(day: QDate) -> QDateEdit:
    """A date selector with a calendar, able to say «sin decidir»."""
    edit = QDateEdit(day)
    edit.setCalendarPopup(True)
    edit.setDisplayFormat("yyyy-MM-dd")
    edit.setMinimumDate(EMPTY)
    edit.setSpecialValueText("sin decidir")
    return edit


class AssetSpans(QWidget):
    """Where an asset is built and tested, and against which other markets."""

    changed = Signal()

    def __init__(self) -> None:
        """Build the segment rows, the MC Retest table and the Cross Market groups."""
        super().__init__()
        self.data: dict = {}
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(10)
        self.lay.addWidget(QLabel("Tramos — elige fechas y Aplicar", objectName="h2"))
        self.dates = QGridLayout()
        self.dates.setHorizontalSpacing(10)
        self.lay.addLayout(self.dates)

        self.lay.addWidget(QLabel("MC Retest — rangos en puntos", objectName="h2"))
        self.mc = grid(["range", "min", "max", "sqx_now"], 3)
        self.mc.cellDoubleClicked.connect(self.on_mc)
        self.lay.addWidget(self.mc)

        head = QHBoxLayout()
        self.markets_head = QLabel(objectName="h2")
        self.markets_head.setWordWrap(True)
        self.add = QPushButton("Añadir")
        self.add.clicked.connect(self.on_add)
        head.addWidget(self.markets_head, 1)
        head.addWidget(self.add)
        self.lay.addLayout(head)
        self.groups = QVBoxLayout()
        self.lay.addLayout(self.groups)

    def fill(self, data: dict) -> None:
        """Draw one asset's windows.

        Args:
            data: What `/api/asset/{symbol}` returned.
        """
        self.data = data
        self.fill_dates()
        self.fill_mc()
        self.fill_markets()

    def fill_dates(self) -> None:
        """One row per segment, under the row of what SQX has, each with its two selectors."""
        clear(self.dates)
        span = self.data["data"] or {}
        self.dates.addWidget(QLabel(word("data")), 0, 0)
        have = QLabel(f"{span.get('from', 'sin datos')} → {span.get('to', 'sin datos')}")
        have.setToolTip("Lo que SQX tiene para el feed de este activo. No se edita: lo refresca "
                        "`python3 -m core.assets --dataranges`.")
        self.dates.addWidget(have, 0, 1, 1, 3)
        for i, seg in enumerate(self.data["segments"]):
            first, last = picker(qdate(seg["from"], False)), picker(qdate(seg["to"], True))
            go = QPushButton("Aplicar")
            go.setEnabled(False)
            for edit in (first, last):
                edit.dateChanged.connect(
                    lambda *_, s=seg, a=first, b=last, g=go: self.dirty(s, a, b, g))
            go.clicked.connect(lambda *_, s=seg, a=first, b=last: self.on_dates(s, a, b))
            name = QLabel(word(seg["name"]))
            name.setToolTip(seg["purpose"])
            kept = seg["reserved_for"]
            note = QLabel(f"Spread {word(seg['spread'])}"
                          + (f" · reservado para {', '.join(kept)}" if kept else ""))
            note.setStyleSheet(f"color:{C['weak'] if kept else C['muted']};")
            note.setWordWrap(True)
            note.setToolTip(seg["purpose"])
            for j, w in enumerate((name, first, last, go)):
                self.dates.addWidget(w, 2 * i + 1, j)
            self.dates.addWidget(note, 2 * i + 2, 1, 1, 4)   # under its selectors: a page is half wide
        self.dates.setColumnStretch(4, 1)

    def dirty(self, seg: dict, first: QDateEdit, last: QDateEdit, go: QPushButton) -> None:
        """Enable Aplicar only for a change that makes a window.

        Args:
            seg: The segment as the daemon sent it.
            first, last: Its two selectors.
            go: Its button.
        """
        moved = (first.date() != qdate(seg["from"], False)
                 or last.date() != qdate(seg["to"], True))
        backwards = EMPTY not in (first.date(), last.date()) and first.date() > last.date()
        go.setEnabled(moved and not backwards)
        go.setToolTip("«Desde» va después de «hasta»." if backwards else
                      "Escribe en assets/_policy.yaml solo el extremo que cambió.")

    def on_dates(self, seg: dict, first: QDateEdit, last: QDateEdit) -> None:
        """Write whichever bound of one segment moved.

        Args:
            seg: The segment as the daemon sent it.
            first, last: Its two selectors.
        """
        for edge, edit, end in (("from", first, False), ("to", last, True)):
            if edit.date() != qdate(seg[edge], end):
                send("policy", ["segments", self.data["symbol"], seg["name"], edge],
                     bound_text(edit.date(), end))
        self.changed.emit()

    def fill_mc(self) -> None:
        """Draw the MC Retest ranges beside the ones the master still carries."""
        rows = self.data["mc_retest"]
        self.mc.setRowCount(len(rows))
        for i, r in enumerate(rows):
            # Min Distance undecided means «no perturbation», so it reads 0 (plan 24 Q5); the
            # file keeps its null and the MinDist task is still not written.
            zero = r["name"] == "min_distance"
            ends = [cell("0", "Sin decidir en el fichero (null): sin perturbación.")
                    if zero and r[k] is None else cell(val(r[k])) for k in ("min", "max")]
            for j, item in enumerate([cell(word(r["name"]), r["name"]), *ends,
                                      cell(now(r["sqx_now"]), "Lo que el maestro lleva hoy.")]):
                self.mc.setItem(i, j, item)
        fit(self.mc)

    def fill_markets(self) -> None:
        """Draw the Cross Market check as one coloured group per category, a row per market."""
        clear(self.groups)
        cats = self.data["markets"]["categories"]
        self.add.setVisible(bool(cats) and bool(self.data["markets"]["candidates"]))
        self.markets_head.setText(
            "Check de Cross Market" if cats else
            "Check de Cross Market — este activo no es un main declarado en _markets.yaml")
        for name, rows in cats.items():
            box = QFrame(objectName="market")
            tint = QColor(TINT.get(name, C["muted"]))
            box.setStyleSheet(f"QFrame#market {{ background: rgba({tint.red()},{tint.green()},"
                              f"{tint.blue()},0.14); border-radius: 6px; }}")
            inner = QVBoxLayout(box)
            inner.addWidget(QLabel(f"<b>{word(name)}: {len(rows)}</b>"))
            for row in rows:
                line = QHBoxLayout()
                text = QLabel(f"{row['asset']}  ·  datos desde {row['data_from']}")
                text.setToolTip(row["feed"])
                drop = QPushButton("Quitar")
                drop.clicked.connect(lambda *_, c=name, f=row["feed"]: self.on_drop(c, f))
                line.addWidget(text, 1)
                line.addWidget(drop)
                inner.addLayout(line)
            self.groups.addWidget(box)

    def on_add(self) -> None:
        """Ask for a category and a market, and append it to that category."""
        m = self.data["markets"]
        box = MarketBox(self.data["symbol"], list(m["categories"]), m["candidates"])
        if box.exec():
            category, market = box.payload()
            self.write(category, [*m["categories"][category], market])

    def on_drop(self, category: str, feed: str) -> None:
        """Take one market out of one category, after saying what that costs.

        Args:
            category: family or structural.
            feed: The market's feed.
        """
        rows = self.data["markets"]["categories"][category]
        asset = next(r["asset"] for r in rows if r["feed"] == feed)
        if QMessageBox.question(self, f"Quitar {asset}", f"{FIXED_FIRST} ¿Lo quito de "
                                f"{word(category)}?") == QMessageBox.Yes:
            self.write(category, [r for r in rows if r["feed"] != feed])

    def write(self, category: str, rows: list[dict]) -> None:
        """Send the category's whole list; `set_market` turns it into a one-line change."""
        client.post("assets/market", {"symbol": self.data["symbol"], "category": category,
                                      "feeds": [{"feed": r["feed"], "data_from": r["data_from"]}
                                                for r in rows]})
        self.changed.emit()

    def on_mc(self, row: int, column: int) -> None:
        """Change one end of one MC Retest range.

        Args:
            row: Which range.
            column: 1 for min, 2 for max; anything else is not a decision.
        """
        if column not in (1, 2):
            return
        r, edge = self.data["mc_retest"][row], "min" if column == 1 else "max"
        box = TextBox(f"{self.data['symbol']} · MC Retest {word(r['name'])} · {word(edge)}",
                      "En PUNTOS y absoluto, no un múltiplo del spread real: un rango sólo "
                      "significa algo a la escala del propio instrumento. Vacío = sin decidir.",
                      "" if r[edge] is None else str(r[edge]), False)
        if box.exec():
            send(self.data["symbol"], ["mc_retest", r["name"], edge], box.text())
            self.changed.emit()


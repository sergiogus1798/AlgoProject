"""One asset's Cross Market check: declare it a main, then add or drop the markets it retests on."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.desktop import client
from ui.desktop.assetforms import FIXED_FIRST, MarketBox, word
from ui.desktop.theme import C

TINT = {
    "family": C["accent"],
    "structural": C["promising"],
}  # a group's background, faint


class CrossMarketCheck(QWidget):
    """The «Declarar como main» / «Añadir» header and one coloured group per category."""

    changed = Signal()

    def __init__(self) -> None:
        """Build the header and the groups column; `fill` draws them."""
        super().__init__()
        self.data: dict = {}
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(6)
        head = QHBoxLayout()
        self.markets_head = QLabel(objectName="h2")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.markets_head.setWordWrap(True)
        self.declare = QPushButton("Declarar como main")
        self.declare.setToolTip(
            "Le da un bloque vacío en _markets.yaml: todo activo con ficha "
            "es un main (dueño, 2026-09-29), no solo los que alguien ya "
            "declaró. Después se le añaden mercados con «Añadir»."
        )
        self.declare.clicked.connect(self.on_declare)
        self.add = QPushButton("Añadir")
        self.add.clicked.connect(self.on_add)
        head.addWidget(self.markets_head, 1)
        head.addWidget(self.declare)
        head.addWidget(self.add)
        self.lay.addLayout(head)
        self.groups = QVBoxLayout()
        self.groups.setSpacing(6)
        self.lay.addLayout(self.groups)
        self.lay.addStretch()

    def fill(self, data: dict) -> None:
        """Draw the Cross Market check as one coloured group per category, a row per market.

        Args:
            data: What `/api/asset/{symbol}` returned.
        """
        self.data = data
        while self.groups.count():
            item = self.groups.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        m = data["markets"]
        cats, declared = m["categories"], bool(m["main"])
        self.declare.setVisible(not declared)
        self.add.setVisible(declared and bool(m["candidates"]))
        self.markets_head.setText(
            "Check de Cross Market"
            if declared
            else "Check de Cross Market — todavía sin declarar como main"
        )
        for name, rows in cats.items():
            box = QFrame(objectName="market")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
            tint = QColor(TINT.get(name, C["muted"]))
            box.setStyleSheet(
                f"QFrame#market {{ background: rgba({tint.red()},{tint.green()},"
                f"{tint.blue()},0.14); border-radius: 6px; }}"
            )
            inner = QGridLayout(box)
            inner.setContentsMargins(10, 6, 8, 8)
            inner.setHorizontalSpacing(10)
            inner.setVerticalSpacing(1)
            inner.setColumnStretch(1, 1)
            inner.addWidget(QLabel(f"<b>{word(name)}: {len(rows)}</b>"), 0, 0, 1, 3)
            for i, row in enumerate(rows, 1):
                asset = QLabel(row["asset"])
                asset.setToolTip(row["feed"])
                since = QLabel(f"desde {row['data_from']}", objectName="muted")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
                drop = QPushButton("×")
                drop.setToolTip(f"Quitar {row['asset']} de {word(name)}.")
                drop.setFixedSize(22, 20)
                drop.setStyleSheet("padding: 0;")
                drop.clicked.connect(
                    lambda *_, c=name, f=row["feed"]: self.on_drop(c, f)
                )
                inner.addWidget(asset, i, 0)
                inner.addWidget(since, i, 1)
                inner.addWidget(drop, i, 2)
            self.groups.addWidget(box)

    def on_declare(self) -> None:
        """Give this asset its own empty Cross Market block, then re-read it."""
        client.post(f"asset/{self.data['symbol']}/market/main", {})
        self.changed.emit()

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
        if (
            QMessageBox.question(
                self,
                f"Quitar {asset}",
                f"{FIXED_FIRST} ¿Lo quito de "  # pyright: ignore[reportCallIssue]  # PySide6 stub lists the deprecated overload that wants buttons
                f"{word(category)}?",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.write(category, [r for r in rows if r["feed"] != feed])

    def write(self, category: str, rows: list[dict]) -> None:
        """Send the category's whole list; `set_market` turns it into a one-line change."""
        client.post(
            "assets/market",
            {
                "symbol": self.data["symbol"],
                "category": category,
                "feeds": [
                    {"feed": r["feed"], "data_from": r["data_from"]} for r in rows
                ],
            },
        )
        self.changed.emit()

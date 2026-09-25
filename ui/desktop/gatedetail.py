"""One strategy after the gate: what each screen measured on it, its IS/OOS pairs, its curve."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from ui.desktop.equitychart import EquityChart
from ui.desktop.resultspanel import kicker, rule, short
from ui.desktop.theme import C, chip


def number(value: object) -> str:
    """A metric as the sheet prints it.

    Args:
        value: The harvest's figure, or None when that side does not carry it.

    Returns:
        Thousands separated above 1000, four significant digits below, «·» for none.
    """
    if value is None:
        return "·"
    return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.4g}"


class GateDetail(QScrollArea):
    """The right-hand column of the gate zone."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.show_empty("Elige una estrategia en el scorecard.")

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 — Qt's name
        """Keep the page as wide as the viewport so lines wrap.

        Args:
            event: Qt's resize event.
        """
        super().resizeEvent(event)
        self.widget().setFixedWidth(self.viewport().width())

    def show_empty(self, text: str) -> None:
        """Replace the page with one line.

        Args:
            text: What to say.
        """
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(QLabel(text, objectName="dim"))
        lay.addStretch()
        self.setWidget(page)

    def show(self, row: dict, screens: list[dict], data: dict) -> None:
        """Draw one strategy.

        Args:
            row: Its scorecard row.
            screens: The screens in cascade order.
            data: Its metrics and curve, as `/api/gate/strategy` returns.
        """
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 12, 0)
        lay.setSpacing(6)
        lay.addWidget(kicker("estrategia"))
        lay.addWidget(QLabel(row["strategy"] or row["strategy_build"], objectName="figure"))
        verdict = ("sobrevive" if row["survives"] else f"murió en {row['died_at']}")
        colour = C["promising"] if row["survives"] else C["dead"]
        lay.addWidget(QLabel(chip(verdict, colour) + f" &nbsp;<span style='color:{C['faint']}'>"
                             f"identidad {row['identity'][:16]}…</span>", objectName="mono"))
        lay.addWidget(rule())
        lay.addWidget(kicker("curva diaria · build, y el retest empalmado a su último nivel"))
        chart = EquityChart()
        chart.show_curve(data["curve"])
        lay.addWidget(chart)
        lay.addWidget(rule())
        lay.addWidget(kicker("dentro y fuera de muestra"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(1)
        for j, head in enumerate(("", "IS · build", "OOS · retest")):
            grid.addWidget(QLabel(head, objectName="dim"), 0, j)
        for i, (label, a, b) in enumerate(data["metrics"], start=1):
            grid.addWidget(QLabel(label, objectName="dim"), i, 0)
            for j, v in enumerate((a, b), start=1):
                cell = QLabel(number(v), objectName="mono")
                cell.setAlignment(Qt.AlignRight)
                if v is not None and v < 0:
                    cell.setStyleSheet(f"color:{C['dead']};")
                grid.addWidget(cell, i, j)
        grid.setColumnStretch(3, 1)
        lay.addLayout(grid)
        lay.addWidget(rule())
        lay.addWidget(kicker("las cribas, una a una"))
        for s in screens:
            name = s["name"]
            value, passed, note = row[f"{name}_value"], row[f"{name}_passed"], row[f"{name}_note"]
            if value is None:
                colour = C["faint"]
                state = "no llegó"
            else:
                colour = C["pending"] if s["kind"] == "soft" else (
                    C["promising"] if passed else C["dead"])
                state = short(str(value)) + ("" if s["kind"] != "soft" else (
                    "  ✓" if passed else "  ✗"))
            line = QLabel(f"{chip(name, colour)} &nbsp;{state}"
                          f"<span style='color:{C['faint']}'>  {note or ''}</span>",
                          objectName="mono")
            line.setWordWrap(True)
            line.setToolTip(s["why"])
            lay.addWidget(line)
        lay.addStretch()
        self.setWidget(page)

"""The funnel: one bar per screen, what entered, what passed and what died, painted to scale."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from ui.desktop.theme import C, MONO, T

ROW = 26
LABEL = 110
NUMBERS = 150


class Funnel(QWidget):
    """The cascade as bars: green for what passed, red for what died, grey when the screen
    is soft and eliminates nobody. The first bar is the population; each next one is what
    the previous left, so the shrinking is seen and not read."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.rows: list[dict] = []
        self.screens: dict[str, dict] = {}
        self.setMouseTracking(True)

    def fill(self, funnel: list[dict], screens: list[dict]) -> None:
        """Replace the funnel.

        Args:
            funnel: `funnel.csv` rows: screen, kind, entered, passed, died.
            screens: The config's screens, for the why and the thresholds on hover.
        """
        self.rows = funnel
        self.screens = {s["name"]: s for s in screens}
        self.setFixedHeight(ROW * len(funnel) + 8)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 — Qt's name
        """Draw the bars.

        Args:
            event: Qt's paint event, unused.
        """
        if not self.rows:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(QFont(MONO.split(",")[0].strip('"'), 10))
        total = max(self.rows[0]["entered"], 1)
        span = self.width() - LABEL - NUMBERS - 8
        for i, r in enumerate(self.rows):
            y = i * ROW + 4
            soft = r["kind"] == "soft"
            p.setPen(QColor(T["muted"]))
            p.drawText(QRectF(0, y, LABEL - 8, ROW - 6), Qt.AlignVCenter | Qt.AlignRight,
                       r["screen"])
            passed = span * r["passed"] / total
            died = span * r["died"] / total
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(C["pending"] if soft else C["promising"]))
            p.drawRect(QRectF(LABEL, y + 4, passed, ROW - 12))
            p.setBrush(QColor(C["dead"]))
            p.drawRect(QRectF(LABEL + passed, y + 4, died, ROW - 12))
            p.setPen(QColor(T["text"]))
            text = (f"{r['entered']:>5} → {r['passed']:>5}"
                    + (f"  −{r['died']}" if r["died"] else "") + ("  soft" if soft else ""))
            p.drawText(QRectF(LABEL + span + 8, y, NUMBERS, ROW - 6), Qt.AlignVCenter, text)
        p.setPen(QPen(QColor(T["rule"]), 1))
        p.drawLine(LABEL, 0, LABEL, self.height())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt's name
        """Explain the screen under the pointer: its why and its thresholds.

        Args:
            event: Qt's mouse event, for the row.
        """
        i = int((event.position().y() - 4) // ROW)
        if 0 <= i < len(self.rows):
            s = self.screens[self.rows[i]["screen"]]
            thresholds = ", ".join(f"{k}={v}" for k, v in s["thresholds"].items()) or "sin umbral"
            self.setToolTip(f"{s['name']} · {s['kind']}\n{s['why']}\n\numbrales: {thresholds}")

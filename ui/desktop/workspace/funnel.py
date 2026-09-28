"""The middle strip of a project: the population's funnel, and why the fallen fell (22 §4.2)."""

import httpx
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from ui.desktop import client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C, MONO, T

ROW = 24
LABEL = 190
NUMBERS = 230
FACE = MONO.split(",")[0].strip('"')


class Bars(QWidget):
    """One bar per screen, to the scale of the first: green what passed, red what died, grey
    a soft screen or one still running. A row with no count yet (sealed by the ledger, still
    running) has no bar, only its state and why. The why is written beside, not hidden."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.rows: list[dict] = []

    def fill(self, rows: list[dict]) -> None:
        """Replace the funnel.

        Args:
            rows: GET /api/databank/funnel rows: screen, entered, passed,
                died, why, and optionally kind and state.
        """
        self.rows = rows
        self.setFixedHeight(ROW * len(rows) + 6)
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
        total = max(next((r["entered"] for r in self.rows if r["entered"]), 1), 1)
        span = (self.width() - LABEL - NUMBERS) * 0.45
        why_x = LABEL + span + NUMBERS + 12
        for i, r in enumerate(self.rows):
            y = i * ROW + 3
            p.setFont(QFont(FACE, 10, QFont.Bold))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(0, y, LABEL - 10, ROW - 4), Qt.AlignVCenter | Qt.AlignRight,
                       label(r["screen"]))
            p.setPen(Qt.NoPen)
            soft = r.get("kind") == "soft"
            if r["entered"] is None:
                text = r.get("state", "")
            elif r["passed"] is None:
                p.setBrush(QColor(C["pending"]))
                p.drawRect(QRectF(LABEL, y + 5, span * r["entered"] / total, ROW - 12))
                text = f"{num(r['entered']):>6} → …"
            else:
                passed = span * min(r["passed"] / total, 1)
                p.setBrush(QColor(C["pending"] if soft else C["promising"]))
                p.drawRect(QRectF(LABEL, y + 5, passed, ROW - 12))
                p.setBrush(QColor(C["dead"]))
                p.drawRect(QRectF(LABEL + passed, y + 5,
                                  span * min(r["died"] / total, 1 - r["passed"] / total),
                                  ROW - 12))
                text = f"{num(r['entered']):>6} → {num(r['passed']):>6}"
            p.setPen(QColor(T["text"] if r["entered"] is not None else C["weak"]))
            p.drawText(QRectF(LABEL + span + 10, y, NUMBERS, ROW - 4), Qt.AlignVCenter, text)
            if r["died"]:
                p.setPen(QColor(C["dead"]))
                p.drawText(QRectF(LABEL + span + 10 + 150, y, 70, ROW - 4), Qt.AlignVCenter,
                           f"−{num(r['died'])}")
            p.setFont(QFont(FACE, 10))
            p.setPen(QColor(T["muted"] if r["passed"] is not None else C["accent"]))
            p.drawText(QRectF(why_x, y, self.width() - why_x, ROW - 4), Qt.AlignVCenter,
                       p.fontMetrics().elidedText(r["why"], Qt.ElideRight,
                                                  int(self.width() - why_x)))


class Funnel(QFrame):
    """The strip: a kicker, one line of what the funnel counts, and the bars."""

    def __init__(self) -> None:
        """Build it empty."""
        super().__init__()
        self.setObjectName("term")
        kicker = QLabel("EMBUDO DE LA POBLACIÓN")
        kicker.setObjectName("kicker")
        self.note = QLabel("")
        self.note.setObjectName("dim")
        self.note.setWordWrap(True)
        self.note.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.bars = Bars()
        # Seventeen rows are ~420 px: scrolled, so the strip never sets the window's height.
        scroll = QScrollArea()
        scroll.setWidget(self.bars)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(4)
        lay.addWidget(kicker)
        lay.addWidget(self.note)
        lay.addWidget(scroll, 1)

    def fill(self, rows: list[dict], source: str = "") -> None:
        """Paint the funnel.

        Args:
            rows: Funnel rows.
            source: Where the gate's rows came from, said under the kicker.
        """
        self.note.setText("Cuántas estrategias entran en cada criba, cuántas pasan y por qué "
                          "caen las que caen. Las barras van a escala de la población del build; "
                          "cada paso posterior lee su propio databank."
                          + (f"  Puerta: {source}." if source else ""))
        self.bars.fill(rows)

    def load(self, project: str) -> None:
        """Read the project's funnel, and the filters' counts once F6 serves them.

        Args:
            project: Project name. `/api/filters/state` (F6, wave 3) is read when it answers
                and adds its rows after the gate's; a 404 or a daemon without it adds none.
        """
        try:
            got = client.get("databank/funnel", project=project)
        except httpx.HTTPError as failed:
            got = {"error": f"El demonio no respondió: {failed}"}
        if "error" in got:
            self.fill([], got["error"])
            return
        rows = got["rows"]
        try:
            rows = rows + client.get("filters/state", project=project).get("rows", [])
        except httpx.HTTPError:
            pass
        self.fill(rows, got["source"])

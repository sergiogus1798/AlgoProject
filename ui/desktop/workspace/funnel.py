"""The middle strip of a project: the population's funnel, and why the fallen fell (22 §4.2)."""

import re

import httpx
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from ui.desktop import background, client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C, MONO, T

ROW = 24
LABEL = 250
NUMBERS = 230
FACE = MONO.split(",")[0].strip('"')
# The header row over the columns (owner, 2026-09-28: «Razón · Steps» on top).
HEAD = ("Criba (pasos del workflow)", "Entran → pasan", "Razón")
SENTENCE = re.compile(r"(^|[.·]\s+)([a-záéíóúñ])(?!\w*_)")
LEADING_KEY = re.compile(r"^[a-z]\w*(?= sobre |: )")     # «wfc: 1 lote…», «spp sobre SPP_IS…»


def capital(text: str) -> str:
    """Every sentence of a why starting with a capital: the gate's own lines start lower-case,
    and a later step's opens with its study key, said in the glossary's words («WFC»)."""
    text = LEADING_KEY.sub(lambda m: label(m.group(0)), text)
    return SENTENCE.sub(lambda m: m.group(1) + m.group(2).upper(), text)


def step_numbers(steps: list[dict]) -> dict[str, str]:
    """Which of the workflow's steps each funnel row stands for, from the rail's own steps.

    Args:
        steps: GET /api/workflow's steps.

    Returns:
        Row screen → «6, 7»: the build row is the build and the OOS retest it was judged on,
        a gate screen is the step whose study is the gate, a later row is its step by title.
    """
    out = {s["title"]: s["n"] for s in steps}
    out["Build"] = ", ".join(s["n"] for s in steps if s.get("stage") in ("build", "oos"))
    out["gate"] = next((s["n"] for s in steps if "gate" in s["studies"]), "")
    return out


class Bars(QWidget):
    """One bar per screen, to the scale of the first: green what passed, red what died, grey
    a soft screen or one still running. A row with no count yet (sealed by the ledger, still
    running) has no bar, only its state and why. The why is written beside, not hidden."""

    def __init__(self) -> None:
        """Start empty."""
        super().__init__()
        self.rows: list[dict] = []
        self.steps: dict[str, str] = {}      # row screen → its steps, `step_numbers`

    def name(self, r: dict) -> str:
        """A row's label with the steps it stands for: «Estáticas (8)»."""
        n = self.steps.get(r["screen"]) or (self.steps.get("gate", "")
                                           if r.get("kind") in ("hard", "soft")
                                           and not r["screen"].startswith("Filtro") else "")
        return label(r["screen"]) + (f" ({n})" if n else "")

    def fill(self, rows: list[dict]) -> None:
        """Replace the funnel.

        Args:
            rows: GET /api/databank/funnel rows: screen, entered, passed,
                died, why, and optionally kind and state.
        """
        self.rows = rows
        self.setFixedHeight(ROW * (len(rows) + 1) + 6)
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
        p.setFont(QFont(FACE, 9, QFont.Bold))
        p.setPen(QColor(T["muted"]))
        for x, w, text, align in ((0, LABEL - 10, HEAD[0], Qt.AlignRight),
                                  (LABEL + span + 10, NUMBERS, HEAD[1], Qt.AlignLeft),
                                  (why_x, self.width() - why_x, HEAD[2], Qt.AlignLeft)):
            p.drawText(QRectF(x, 3, w, ROW - 4), Qt.AlignVCenter | align, text.upper())
        for i, r in enumerate(self.rows, start=1):
            y = i * ROW + 3
            p.setFont(QFont(FACE, 10, QFont.Bold))
            p.setPen(QColor(T["text"]))
            p.drawText(QRectF(0, y, LABEL - 10, ROW - 4), Qt.AlignVCenter | Qt.AlignRight,
                       self.name(r))
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
                       p.fontMetrics().elidedText(capital(r["why"]), Qt.ElideRight,
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
                          "caen las que caen. El número entre paréntesis es el paso del workflow "
                          "(de los 25) al que pertenece la criba. Las barras van a escala de la "
                          "población del build; cada paso posterior lee su propio databank."
                          + (f"  Puerta: {source}." if source else ""))
        self.bars.fill(rows)

    def name_steps(self, steps: list[dict]) -> None:
        """Take the rail's steps, to write each row's step numbers (`step_numbers`)."""
        self.bars.steps = step_numbers(steps)
        self.bars.update()

    def load(self, project: str) -> None:
        """Read the project's funnel, and the filters' counts once F6 serves them, off the GUI
        thread; `landed` paints them.

        Args:
            project: Project name. `/api/filters/state` (F6, wave 3) is read when it answers
                and adds its rows after the gate's; a 404 or a daemon without it adds none.
        """
        def both() -> dict:
            """The funnel and the filters' rows, on the pool's thread."""
            got = client.get("databank/funnel", project=project)
            if "error" in got:
                return got
            try:
                extra = client.get("filters/state", project=project).get("rows", [])
            except httpx.HTTPError:
                extra = []
            return got | {"rows": got["rows"] + extra}
        background.run(both, self.landed, key=f"funnel:{id(self)}")

    def landed(self, got: dict) -> None:
        """The funnel's rows arrived: paint them, or the reason there are none."""
        if "error" in got:
            self.fill([], got["error"])
            return
        self.fill(got["rows"], got["source"])

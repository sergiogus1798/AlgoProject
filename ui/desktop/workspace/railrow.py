"""One card of the rail: a step's box, number, kind, title, target tab, configuration and state."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from ui.text.glossary import label
from ui.desktop.theme import C, T
from ui.desktop.workspace.railwords import KIND, gear, ink, readable, run_button, runnable, small, word
from ui.text.brief import brief, busy


def off_reason(step: dict, sqx: dict | None) -> tuple[str, bool]:
    """Why a step's run button is off, and whether that is a real failure.

    Red is for a real failure only (CLAUDE.md feedback, 2026-09-29): a step done elsewhere
    (its ▶ SQX never launches it, `steps.ELSEWHERE`), a study only run from the terminal, or
    a step simply busy right now are expected states, not something broken.

    Args:
        step: One step as GET /api/workflow sends it.
        sqx: For an SQX step, its entry of GET /api/launch/steps; None while unknown.

    Returns:
        `(why, fails)` — `why` is '' when it may run; `fails` is False for an expected state.
    """
    if step["kind"] == "sqx":
        if sqx is None:
            return "sin comprobar todavía si SQX puede lanzarlo", False
        if sqx["ok"]:
            return "", False
        return sqx["reasons"][0], not sqx.get("elsewhere", False)
    tests = runnable(step)
    if not tests:
        return (step["tests"][0]["why"], False) if step["tests"] else \
               ("no tiene pruebas que se corran desde aquí", False)
    if step["state"] == "blocked":
        return step["why"], True
    if all(t["state"] == "running" for t in tests):
        return "todas sus pruebas están en marcha", False
    return "", False


class StepCard(QFrame):
    """One step. A click outside the box and the button opens its tab and shows its tests;
    the box ticks every runnable test of the step. «▶ PY» runs the step's ticked tests, or
    all of them when none is ticked (`ran`); «▶ SQX» launches every task of the step in one
    start of its worker (`launched`); the ⚙ left of it asks for the screen that edits the
    step's configuration (`configured`). Off, the button is dashed and its reason replaces the
    configuration line."""

    opened = Signal(str)
    ticked = Signal(str, bool)
    ran = Signal(str)
    launched = Signal(str)
    configured = Signal(str)

    def __init__(self, step: dict, checked: bool, chosen: bool, sqx: dict | None = None) -> None:
        """Build the card.

        Args:
            step: One step as GET /api/workflow sends it.
            checked: Whether every runnable test of it is ticked.
            chosen: Whether it is the step the drawer shows.
            sqx: An SQX step's entry of GET /api/launch/steps, None until it is read.
        """
        super().__init__()
        self.step = step
        self.why, self.fails = ("", False) if step["kind"] == "person" else off_reason(step, sqx)
        colour = ink(step["state"])
        self.setObjectName("stepcard")
        edge = T["accent"] if chosen else T["line"]
        self.setStyleSheet(f"QFrame#stepcard {{ border: 1px solid {edge}; "
                           f"border-top: 3px solid {colour}; border-radius: 4px; }}")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(self.explain())
        top = QHBoxLayout()
        top.setSpacing(4)
        box = QCheckBox(step["n"])
        box.setChecked(checked)
        box.setEnabled(bool(runnable(step)))
        box.setToolTip(label("Marca o desmarca todas sus pruebas que se pueden correr aquí."))
        box.toggled.connect(lambda on: self.ticked.emit(step["n"], on))
        top.addWidget(box)
        top.addStretch(1)
        if step["kind"] == "person":
            top.addWidget(small(KIND["person"][0]))
        else:
            kind = step["kind"]
            run = run_button(kind, f"▶ {KIND[kind][0]}", self.why)
            if not self.why:
                run.setToolTip(label(
                    f"Lanzar en SQX todas las tareas del paso {step['n']} juntas"
                    if kind == "sqx" else
                    f"Correr las pruebas marcadas del paso {step['n']}; si no hay ninguna, "
                    "pregunta y corre las que ni leen oos2 ni escriben en el Ledger"
                    + (" sobre el databank que enseña Databanks" if step.get("panel") else "")))
            run.clicked.connect(lambda: (self.launched if kind == "sqx"
                                         else self.ran).emit(step["n"]))
            top.addWidget(gear(step["n"], self.configured))
            top.addWidget(run)
        title = QLabel(label(step["title"]))
        title.setWordWrap(True)
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        title.setFixedHeight(30)
        title.setStyleSheet("font-weight: 700; font-size: 11px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 3, 6, 4)
        lay.setSpacing(0)
        lay.addLayout(top)
        lay.addWidget(title)
        where = step["tab"] + (f" › {step['sub']}" if step["sub"] else "")
        lay.addWidget(small(f"→ {where or label('sin panel')}", "mono"))
        # A few words on a card that fits two lines; its full reason is in its tooltip.
        short = "workflow corriendo" if busy(self.why) else brief(label(self.why), 30)
        status = (small(f"✖ {short}", "dim", C["dead"]) if self.fails and not busy(self.why)
                  else small(f"· {short}", "dim") if self.why
                  else small(self.config()))
        status.setWordWrap(True)
        lay.addWidget(status)
        lay.addWidget(small(word(step["state"]).upper(), "mono", colour))

    def config(self) -> str:
        """The configuration line: the first test's knobs, or how many tests it has."""
        tests = self.step["tests"]
        if not tests:
            return "—"
        return readable(tests[0]["config"]) if len(tests) == 1 else f"{len(tests)} pruebas"

    def explain(self) -> str:
        """The card in words, for its tooltip."""
        s = self.step
        tests = ", ".join(label(t["title"]) for t in s["tests"]) or "ninguna"
        return (f"Paso {s['n']} · {s['title']} — {word(s['state'])}\n{KIND[s['kind']][1]}\n"
                f"Pruebas: {tests}\nResultado en el panel: {s['tab'] or 'ninguno'}"
                + (f"\n\n{s['why']}" if s["why"] else "")
                + (f"\n\nNo se puede correr ahora: {self.why}" if self.why else ""))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt's name
        """Show the step in the drawer and its tab in the panel.

        Args:
            event: Qt's mouse event, unused.
        """
        self.opened.emit(self.step["n"])

"""One card of the rail: a step's box, number, kind, title, target tab, configuration and state."""

import ast
import re

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QVBoxLayout)

from ui.text.glossary import knob, label
from ui.text.numbers import num
from ui.desktop.theme import C, T

# The daemon's state words (ui/daemon/workflow) as the rail says and paints them. `sealed` is
# a finished 17-19 whose numbers stay hidden until 20 opens; `missing`, nothing to read.
STATE = {"done": ("hecho", C["promising"]), "running": ("en marcha", C["accent"]),
         "pending": ("pendiente", C["pending"]), "blocked": ("bloqueado", C["dead"]),
         "sealed": ("sellado", C["weak"]), "missing": ("sin dato", T["faint"])}
KIND = {"sqx": ("SQX", "corre en StrategyQuant X: la ventana lo enseña y no lo lanza"),
        "python": ("PY", "corre en Python, desde aquí"),
        "person": ("TÚ", "lo haces tú, en el chat")}
MORE = re.compile(r" \(\+(\d+)\)$")      # the «(+9)» tail of a test's one-line config


def value_words(value: object) -> str:
    """A knob's value as the window prints it: a number exact and never scientific (a knob
    is copied, not read at a glance, so no K or M), None as «—», a boolean as sí/no, a list
    item by item, text as the study spells it. A value that arrives as its Python text
    («2500», «None», «['NetProfit']») is read back first."""
    if isinstance(value, str):
        try:
            value = ast.literal_eval(value) if value else None
        except (ValueError, SyntaxError):      # a word: `hard`, `ReturnDDRatio (build)`
            return value
    if isinstance(value, (list, tuple)):
        return ", ".join(value_words(v) for v in value) or "—"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}".replace(",", " ")       # exact: a seed is not «20.3 M»
    if isinstance(value, float):
        return np.format_float_positional(value, trim="-")    # exact and never «1e-05»
    return num(value) if value is None or isinstance(value, (bool, str)) else str(value)


def readable(config: str) -> str:
    """A test's one-line config («nulls.draws=2500 · run.blocks=None (+9)», as
    `ui.daemon.workflow.tests.summary` writes it) in the window's words:
    «Nulos › Corridas 2 500 · Ejecución › Bloques — · y 9 más». Anything else passes."""
    more = MORE.search(config)
    body = config[:more.start()] if more else config
    if "=" not in body:
        return config
    parts = [f"{knob(k)} {value_words(v)}" for k, v in
             (item.split("=", 1) for item in body.split(" · "))]
    return " · ".join(parts) + (f" · y {more.group(1)} más" if more else "")


def word(state: str) -> str:
    """The Spanish word of a state, the raw one quoted when the rail does not know it."""
    return STATE.get(state, (f"«{state}»",))[0]


def ink(state: str) -> str:
    """The colour of a state, the pending grey when the rail does not know it."""
    return STATE.get(state, ("", C["pending"]))[1]


def small(text: str, name: str = "dim", colour: str = "") -> QLabel:
    """One line of a card, in the term look, cut rather than widening the card.

    Args:
        text: What it says.
        name: The term style to wear (dim, mono).
        colour: A colour that overrides the style's, or '' to keep it.
    """
    line = QLabel(text)
    line.setObjectName(name)
    line.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
    if colour:
        line.setStyleSheet(f"color: {colour};")
    return line


def runnable(step: dict) -> list[dict]:
    """The tests of a step the window may start: Python studies, never an SQX task."""
    return [t for t in step["tests"] if t["runnable"]]


class StepCard(QFrame):
    """One step. A click outside the box and the button opens its tab and shows its tests;
    the box ticks every runnable test of the step; ▶ runs the step's ticked tests. An SQX
    step has no ▶: the window starts nothing in SQX."""

    opened = Signal(str)
    ticked = Signal(str, bool)
    ran = Signal(str)

    def __init__(self, step: dict, checked: bool, chosen: bool) -> None:
        """Build the card.

        Args:
            step: One step as GET /api/workflow sends it.
            checked: Whether every runnable test of it is ticked.
            chosen: Whether it is the step the drawer shows.
        """
        super().__init__()
        self.step = step
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
        top.addWidget(small(KIND[step["kind"]][0]))
        if step["kind"] != "sqx" and runnable(step):
            run = QPushButton("▶")
            run.setFixedWidth(26)
            run.setToolTip(label(f"Correr las pruebas marcadas del paso {step['n']}"))
            run.setEnabled(step["state"] != "blocked")
            run.clicked.connect(lambda: self.ran.emit(step["n"]))
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
        lay.addWidget(small(self.config()))
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
                + (f"\n\n{s['why']}" if s["why"] else ""))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 — Qt's name
        """Show the step in the drawer and its tab in the panel.

        Args:
            event: Qt's mouse event, unused.
        """
        self.opened.emit(self.step["n"])

"""Words, colours and small widgets the rail and its drawer both draw a step's card with."""

import ast
import re

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QToolButton

from ui.text.glossary import knob, label
from ui.text.numbers import num
from ui.desktop.theme import C, T

# The daemon's state words (ui/daemon/workflow) as the rail says and paints them. `sealed` is
# a finished 17-19 whose numbers stay hidden until 20 opens; `missing`, nothing to read.
STATE = {"done": ("hecho", C["promising"]), "running": ("en marcha", C["accent"]),
         "pending": ("pendiente", C["pending"]), "blocked": ("bloqueado", C["dead"]),
         "sealed": ("sellado", C["weak"]), "missing": ("sin dato", T["faint"])}
KIND = {"sqx": ("SQX", "corre en StrategyQuant X: su ▶ SQX lanza todas sus tareas juntas en el "
                      "worker del proyecto, que se para al acabar"),
        "python": ("PY", "corre en Python, desde aquí: su ▶ PY corre sus pruebas"),
        "person": ("TÚ", "lo haces tú, en el chat")}
# The run buttons' colours: Python in the accent, SQX in amber — a different machine, and
# the one whose runs take hours and touch a worker.
RUN = {"python": C["accent"], "sqx": C["weak"]}
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


def run_button(kind: str, text: str, why: str) -> QPushButton:
    """A run button in its kind's colour, greyed when off; the reason is its tooltip and,
    because a disabled button shows none, also a visible line wherever it sits."""
    button = QPushButton(text)
    colour = RUN[kind]
    button.setStyleSheet(f"QPushButton {{ color: {colour}; border: 1px solid {colour}; "
                         f"padding: 1px 5px; }} QPushButton:disabled {{ color: {T['faint']}; "
                         f"border: 1px dashed {T['line']}; }}")
    button.setEnabled(not why)
    button.setToolTip(label(why) if why else "")
    return button


def gear(n: str, configured: Signal) -> QToolButton:
    """The ⚙ left of a step's run button: it opens the screen where the step's configuration is
    edited (`railrun.configure`). A frameless tool button, so ten cards do not widen, with no
    «?» of its own: its tooltip says it."""
    button = QToolButton()
    button.setText("⚙")
    button.setAutoRaise(True)
    button.setProperty("helpmark", False)
    button.setFixedWidth(16)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(f"QToolButton {{ color: {T['muted']}; border: none; padding: 0; "
                         f"font-size: 14px; }} QToolButton:hover {{ color: {T['accent']}; }}")
    button.setToolTip(label(f"Editar la configuración del paso {n}: abre la pantalla donde se "
                            "cambia; luego vuelves aquí a lanzarlo"))
    button.clicked.connect(lambda: configured.emit(n))
    return button

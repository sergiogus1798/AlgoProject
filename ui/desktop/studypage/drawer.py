"""The configuration drawer: every knob of a study, its sentence, and the hash the next run would sign."""

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.studypage.net import fetch, send
from ui.desktop.theme import T
from ui.text.glossary import knob as knob_words

EDITED = f"border: 2px solid {colour('info')};"


def as_text(value: object) -> str:
    """A knob's value as `--set` takes it: YAML, which JSON is a subset of.

    Args:
        value: The value in the study's config.

    Returns:
        A string is written bare; everything else as JSON (lists, numbers, null).
    """
    return value if isinstance(value, str) else json.dumps(value)


def editor(knob: dict) -> QWidget:
    """The widget one knob is edited with, by its type.

    Args:
        knob: `{"key", "value", "default", "type", "tip"}` from `/api/config`, and `choices`
            when the knob only takes a fixed list of values.

    Returns:
        A check box for a bool, a drop-down for a fixed list, a line for anything else.
    """
    if knob["type"] == "bool":
        box = QCheckBox("sí")
        box.setChecked(bool(knob["value"]))
        return box
    if knob.get("choices"):
        pick = QComboBox()
        pick.addItems([as_text(c) for c in knob["choices"]])
        pick.setCurrentText(as_text(knob["value"]))
        return pick
    line = QLineEdit(as_text(knob["value"]))
    line.setMinimumWidth(140)
    line.setCursorPosition(0)         # a long value shows its start, not its end
    return line


def read(widget: QWidget) -> str:
    """What an editor now holds, in `--set` spelling.

    Args:
        widget: A widget made by `editor`.

    Returns:
        "true"/"false" for a check box, else the text as typed.
    """
    if isinstance(widget, QCheckBox):
        return "true" if widget.isChecked() else "false"
    if isinstance(widget, QComboBox):
        return widget.currentText()
    return widget.text().strip()


def put(widget: QWidget, value: str) -> None:
    """Set an editor to a value in `--set` spelling, the inverse of `read`.

    Args:
        widget: A widget made by `editor`.
        value: As `read` returns it.
    """
    if isinstance(widget, QCheckBox):
        widget.setChecked(value == "true")
    elif isinstance(widget, QComboBox):
        widget.setCurrentText(value)
    else:
        widget.setText(value)


class Drawer(QFrame):
    """The drawer of one study. Edits live here per study until reset; they reach only the
    next run, as `--set`, and never the config.yaml."""

    changed = Signal()

    def __init__(self) -> None:
        """Start with no study."""
        super().__init__()
        self.setObjectName("term")
        self.study = ""
        self.shown_hash: str | None = None
        self.editors: dict[str, tuple[QWidget, str]] = {}   # key -> (widget, default text)
        self.edits: dict[str, dict[str, str]] = {}          # study -> {key: text}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        self.title = text("CONFIGURACIÓN", T["text"], 12, True)
        lay.addWidget(self.title)
        lay.addWidget(text("Cambia solo la próxima ejecución, como --set. El config.yaml no se "
                           "toca nunca.", T["muted"], 12))
        row = QHBoxLayout()
        reset = QPushButton("restablecer valores de fábrica")
        reset.setToolTip("Vuelve cada mando al valor de config.yaml y olvida lo editado aquí.")
        reset.clicked.connect(self.reset)
        row.addWidget(reset)
        row.addStretch(1)
        lay.addLayout(row)
        self.sign = text("", T["text"], 12)
        lay.addWidget(self.sign)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body = QWidget()
        scroll.setWidget(self.body)
        self.scroll = scroll
        lay.addWidget(scroll, 1)

    def load(self, study: str, title: str) -> None:
        """Show one study's knobs, with what was edited for it before.

        Args:
            study: Study key.
            title: Its title on screen.
        """
        self.study = study
        self.title.setText(f"CONFIGURACIÓN · {title}")
        got = fetch("config", study=study)
        self.editors = {}
        self.body = QWidget()
        grid = QVBoxLayout(self.body)
        grid.setContentsMargins(0, 0, 16, 0)
        if "error" in got:
            grid.addWidget(text(got["error"], colour("fail"), 13, True))
        elif not got["sections"]:
            grid.addWidget(text("Este estudio no tiene config.yaml: no hay mandos que cambiar.",
                                T["muted"], 13))
        for section in got.get("sections", []):
            grid.addWidget(text(knob_words(section["name"]).upper(), T["text"], 11, True))
            for knob in section["knobs"]:
                grid.addWidget(self._knob(knob, section["name"]))
        grid.addStretch(1)
        self.scroll.setWidget(self.body)
        self.refresh()

    def _knob(self, knob: dict, section: str) -> QWidget:
        """One knob: its words and editor on a line, its sentence visible under them. The
        words drop the section its header already says; the raw key, which `--set` takes,
        stays in the tooltip."""
        box = QWidget()
        lay = QGridLayout(box)
        lay.setContentsMargins(0, 2, 0, 6)
        lay.setVerticalSpacing(2)
        key = text(knob_words(knob["key"].removeprefix(f"{section}.")), T["text"], 12, True)
        widget = editor(knob)
        default = as_text(knob["default"]) if knob["type"] != "bool" else \
            ("true" if knob["default"] else "false")
        saved = self.edits.get(self.study, {}).get(knob["key"])
        if saved is not None:
            put(widget, saved)
        tip = knob["tip"] or "El estudio no escribió frase para este mando."
        for w in (key, widget):
            w.setToolTip(f"{knob['key']} ({knob['type']}) — {tip}\nDe fábrica: {default}")
        if isinstance(widget, QCheckBox):
            widget.toggled.connect(self._edited)
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(self._edited)
        else:
            widget.editingFinished.connect(self._edited)
        self.editors[knob["key"]] = (widget, default)
        lay.addWidget(key, 0, 0)
        lay.addWidget(widget, 0, 1)
        lay.addWidget(text(tip, T["faint"], 11), 1, 0, 1, 2)
        lay.setColumnStretch(0, 1)
        return box

    def overrides(self) -> list[str]:
        """The knobs that differ from the factory value, as `--set` strings.

        Returns:
            ["section.key=value", ...], empty when nothing was edited.
        """
        return [f"{k}={read(w)}" for k, (w, default) in self.editors.items()
                if read(w) != default]

    def _edited(self) -> None:
        """Remember the edits of this study, mark the edited knobs, re-sign."""
        self.edits[self.study] = {k: read(w) for k, (w, d) in self.editors.items()
                                  if read(w) != d}
        self.refresh()

    def reset(self) -> None:
        """Every knob back to its factory value, the edits forgotten."""
        self.edits.pop(self.study, None)
        for w, default in self.editors.values():
            w.blockSignals(True)
            put(w, default)
            w.blockSignals(False)
        self.refresh()

    def set_shown(self, config_hash: str | None) -> None:
        """Say which configuration signed the result on screen, to compare against.

        Args:
            config_hash: `meta.config_hash` of the shown result, None when none is shown.
        """
        self.shown_hash = config_hash
        self.refresh()

    def refresh(self) -> None:
        """Mark edited knobs and say whether the next run would sign what is on screen."""
        for w, default in self.editors.values():
            w.setStyleSheet(EDITED if read(w) != default else "")
        n = len(self.overrides())
        got = send("config/hash", {"study": self.study, "overrides": self.overrides()}) \
            if self.study else {"hash": None}
        if "error" in got:
            self.sign.setText(f'<span style="color:{colour("fail")}">{got["error"]}</span>')
        elif got["hash"] is None:
            self.sign.setText("Sin configuración: nada que firmar.")
        else:
            shown = self.shown_hash
            if shown is None:
                verdict = "no hay resultado en pantalla con el que comparar"
            elif shown == got["hash"]:
                verdict = f'<b style="color:{colour("pass")}">coincide</b> con el mostrado'
            else:
                verdict = (f'<b style="color:{colour("watch")}">distinta configuración</b> '
                           f"que el mostrado ({shown})")
            self.sign.setText(f"próxima ejecución firma <b>{got['hash']}</b> · {verdict}"
                              f" · {n} mando{'s' if n != 1 else ''} cambiado{'s' if n != 1 else ''}")
        self.changed.emit()

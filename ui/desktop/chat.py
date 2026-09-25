"""The chat that turns an idea into a draft brief and the command that authors it."""

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.theme import C

OPENING = ("Cuatro o cinco preguntas y te dejo el brief escrito y el comando listo para pegar "
           "en Claude Code. Lo que no contestes lleva el default del dueño, y el brief dirá "
           "cuál se aplicó.")


def drop(layout: QVBoxLayout | QHBoxLayout) -> None:
    """Delete everything in a layout, however deeply nested.

    Args:
        layout: The layout to empty. It survives; its contents do not.

    A stretch is an item with neither a widget nor a layout, which is why this is a
    recursion and not a loop over widgets.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            # setParent(None) as well as deleteLater(): the deletion is deferred to the
            # event loop, and until it runs the old controls keep painting under the new.
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout():
            drop(item.layout())


def bubble(text: str, mine: bool) -> QFrame:
    """One message in the transcript.

    Args:
        text: What it says.
        mine: True for the reader's own answers, which sit right and accented.

    Returns:
        A framed label.
    """
    f = QFrame()
    f.setStyleSheet(f"background:{C['accent'] if mine else C['raised']}; border-radius:10px;")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(13, 9, 13, 9)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("background:transparent; color:#ffffff;" if mine else "background:transparent;")
    lay.addWidget(label)
    return f


class Chat(QWidget):
    """The interview, one question at a time, ending in a brief on disk."""

    authored = Signal()

    def __init__(self) -> None:
        """Build the transcript, the answer area and the reset button."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        head = QHBoxLayout()
        head.addWidget(QLabel("Nueva plantilla", objectName="h1"))
        head.addStretch()
        restart = QPushButton("Empezar de nuevo")
        restart.clicked.connect(self.start)
        head.addWidget(restart)
        lay.addLayout(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        lay.addWidget(self.scroll, 1)

        self.answer_area = QFrame(objectName="panel")
        self.answer_lay = QVBoxLayout(self.answer_area)
        self.answer_lay.setContentsMargins(14, 12, 14, 12)
        self.answer_lay.setSpacing(8)
        lay.addWidget(self.answer_area)

        self.answers: dict[str, str] = {}
        self.start()

    def start(self) -> None:
        """Clear the transcript and ask the first question."""
        self.answers = {}
        body = QWidget()
        self.thread = QVBoxLayout(body)
        self.thread.setContentsMargins(4, 4, 4, 4)
        self.thread.setSpacing(10)
        self.thread.addStretch()
        self.scroll.setWidget(body)
        self.say(OPENING, mine=False)
        self.next()

    def say(self, text: str, mine: bool) -> None:
        """Add a message to the transcript and scroll to it.

        Args:
            text: What it says.
            mine: Whether it is the reader's.
        """
        row = QHBoxLayout()
        if mine:
            row.addStretch()
        b = bubble(text, mine)
        b.setMaximumWidth(620)
        row.addWidget(b)
        if not mine:
            row.addStretch()
        self.thread.insertLayout(self.thread.count() - 1, row)
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def attach(self, widget: QWidget) -> None:
        """Put a whole widget in the transcript, not just a line of text.

        Args:
            widget: What to show. The result of the interview goes here rather than under
                it: the answer area holds controls, and a growing panel of results down
                there pushes the conversation off the screen.
        """
        row = QHBoxLayout()
        row.addWidget(widget)
        row.addStretch()
        self.thread.insertLayout(self.thread.count() - 1, row)

    def clear_answer_area(self) -> None:
        """Empty the controls under the transcript before drawing the next ones."""
        drop(self.answer_lay)

    def next(self) -> None:
        """Ask the daemon what comes next and draw either the question or the result."""
        step = client.post("interview/step", {"answers": self.answers})
        self.clear_answer_area()
        if step["done"]:
            self.finish()
            return
        q = step["question"]
        n, total = step["progress"]
        self.say(f"{q['ask']}\n\n{q['why']}", mine=False)
        self.answer_lay.addWidget(QLabel(f"Pregunta {n} de {total}", objectName="faint"))
        if q["kind"] == "choice":
            self.draw_options(q)
        else:
            self.draw_text(q)

    def draw_options(self, q: dict) -> None:
        """Draw one button per option, plus a skip when the question has a default.

        Args:
            q: The question the daemon returned.
        """
        row = QHBoxLayout()
        for opt in q["options"]:
            b = QPushButton(opt["label"])
            b.clicked.connect(lambda _, i=q["id"], o=opt: self.answer(i, o["value"], o["label"]))
            row.addWidget(b)
        if q["default"]:
            skip = QPushButton("Elige tú")
            skip.setToolTip(f"Aplica el default documentado: {q['default']}")
            skip.clicked.connect(lambda _, i=q["id"]: self.answer(i, "", "elige tú"))
            row.addWidget(skip)
        row.addStretch()
        self.answer_lay.addLayout(row)

    def draw_text(self, q: dict) -> None:
        """Draw the free-text field for a question with no options.

        Args:
            q: The question the daemon returned.
        """
        row = QHBoxLayout()
        field = QLineEdit()
        field.setPlaceholderText("Escribe y pulsa Enter")
        send = QPushButton("Enviar", objectName="primary")
        act = lambda: self.answer(q["id"], field.text().strip(), field.text().strip())
        field.returnPressed.connect(act)
        send.clicked.connect(act)
        row.addWidget(field, 1)
        row.addWidget(send)
        self.answer_lay.addLayout(row)
        field.setFocus()

    def answer(self, qid: str, value: str, shown: str) -> None:
        """Record one answer and move on.

        Args:
            qid: Which question.
            value: The stored value; "" means the default applies.
            shown: What to echo in the transcript.
        """
        self.answers[qid] = value
        self.say(shown or "elige tú", mine=True)
        self.next()

    def finish(self) -> None:
        """Write the draft brief and show the prompt and the commands."""
        result = client.post("interview/finish", {"answers": self.answers})
        applied = result["brief"]["defaults_applied"]
        self.say(f"Listo. Brief escrito en {result['path']}."
                 + (f"\n\nDefaults aplicados: {', '.join(applied)}." if applied else ""),
                 mine=False)

        panel = QFrame(objectName="panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        panel.setFixedWidth(780)
        lay.addWidget(QLabel("Pega esto en Claude Code", objectName="h2"))
        box = QPlainTextEdit(result["prompt"])
        box.setReadOnly(True)
        box.setFixedHeight(170)
        lay.addWidget(box)
        lay.addWidget(QLabel("Y esto es lo que la skill ejecutará:", objectName="muted"))
        cmds = QLabel("\n".join(f"·  {c['what']}\n    {c['cmd']}" for c in result["commands"]))
        cmds.setObjectName("faint")
        cmds.setWordWrap(True)
        cmds.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cmds.setToolTip("Esta ventana no los corre: instalar un bloque escribe en una instalación "
                        "de SQX de verdad, y eso es el carril del conductor.")
        lay.addWidget(cmds)
        self.attach(panel)

        row = QHBoxLayout()
        copy = QPushButton("Copiar el prompt", objectName="primary")
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(result["prompt"]))
        row.addWidget(copy)
        as_json = QPushButton("Copiar el brief en JSON")
        as_json.clicked.connect(lambda: QGuiApplication.clipboard().setText(
            json.dumps(result["brief"], indent=2, ensure_ascii=False)))
        row.addWidget(as_json)
        row.addStretch()
        self.answer_lay.addLayout(row)
        self.authored.emit()

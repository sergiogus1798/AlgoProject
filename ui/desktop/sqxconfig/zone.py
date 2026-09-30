"""Configuración SQX: every setting a new project is built and tested with, one section per test."""

import httpx
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.sqxconfig.section import Section, words
from ui.desktop.theme import C

# The owner's words for what a write here does (plan 24 §10, Q17).
WARNING = ("Se aplica a los proyectos que se creen a partir de ahora; los existentes no cambian. "
           "Cada cambio se escribe en assets/ conservando los comentarios, y git lo ve. WFC y "
           "CSCV escriben además en los config.yaml de sus estudios y, los bloques del CSCV, en "
           "ledger/thresholds.yaml, sellado con tu nombre y la fecha.")
FILES = {"build": "Construcción y tests · _build.yaml", "classes": "Esquemas de coste · _classes.yaml",
         "policy": "Política común · _policy.yaml", "markets": "Universo de retest · _markets.yaml"}


class SqxConfigZone(QFrame):
    """The zone: an index of sections on the left, the sections on the right, the warning and
    the line saying what the last write did on top. Reads the daemon on first show."""

    def __init__(self) -> None:
        """Build the frame; `load` fills it."""
        super().__init__()
        self.setObjectName("term")
        self.sections: list[Section] = []
        kicker = QLabel("BIBLIOTECA · CONFIGURACIÓN SQX")
        kicker.setObjectName("kicker")
        title = QLabel("Configuración SQX")
        title.setObjectName("h1")
        warning = QLabel(WARNING)
        warning.setWordWrap(True)
        warning.setStyleSheet(f"color: {C['weak']}; font-weight: 700;")
        self.status = QLabel("")
        self.status.setObjectName("dim")
        reload_ = QPushButton("recargar")
        reload_.setToolTip("Volver a leer los ficheros por si otro los cambió")
        reload_.clicked.connect(self.load)
        top = QHBoxLayout()
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(reload_)
        self.index = QListWidget()
        self.index.setFixedWidth(300)
        self.index.itemClicked.connect(self.jump)
        self.column = QVBoxLayout()
        self.column.setSpacing(2)
        inner = QWidget()
        inner.setLayout(self.column)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidget(inner)
        split = QHBoxLayout()
        split.addWidget(self.index)
        split.addWidget(self.scroll, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(6)
        lay.addWidget(kicker)
        lay.addLayout(top)
        lay.addWidget(warning)
        lay.addWidget(self.status)
        lay.addLayout(split, 1)

    def showEvent(self, event: object) -> None:
        """Read the daemon the first time the zone is shown, not when the window starts."""
        super().showEvent(event)
        if not self.sections:
            self.load()

    def load(self) -> None:
        """Read `/api/sqxconfig` and rebuild the index and the sections, all folded."""
        try:
            state = client.get("sqxconfig")
        except httpx.HTTPError as err:
            self.say(f"El demonio no contesta: {err}", C["dead"])
            return
        while self.column.count():
            item = self.column.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.index.clear()
        self.sections, current = [], None
        for sec in state["sections"]:
            if sec["file"] != current:
                current = sec["file"]
                self.header(FILES[current])
            section = Section(sec)
            section.written.connect(lambda text: self.say(text, C["promising"]))
            section.refused.connect(lambda text: self.say(f"no escrito — {text}", C["dead"]))
            # queued: the section asking is itself rebuilt by the re-read
            section.stale.connect(lambda: QTimer.singleShot(0, self.refresh))
            self.column.addWidget(section)
            item = QListWidgetItem(f"  {words(sec['key'])}")
            item.setData(Qt.UserRole, len(self.sections))
            self.index.addItem(item)
            self.sections.append(section)
        self.column.addStretch(1)
        self.say(f"{len(self.sections)} secciones leídas", C["muted"])

    def refresh(self) -> None:
        """Re-read after a write other rows depend on, keeping what was open, the scroll and
        the status line that said what was written."""
        opened = [s.section["key"] for s in self.sections if s.head.isChecked()]
        said, style = self.status.text(), self.status.styleSheet()
        at = self.scroll.verticalScrollBar().value()
        self.load()
        for s in self.sections:
            if s.section["key"] in opened:
                s.head.setChecked(True)
        self.status.setText(said)
        self.status.setStyleSheet(style)
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(at))

    def header(self, text: str) -> None:
        """A file's heading, in the index and above its sections."""
        head = QListWidgetItem(text.upper())
        head.setFlags(Qt.NoItemFlags)
        self.index.addItem(head)
        label = QLabel(text.upper())
        label.setObjectName("kicker")
        label.setContentsMargins(0, 14, 0, 2)
        self.column.addWidget(label)

    def jump(self, item: QListWidgetItem) -> None:
        """Open the chosen section and scroll it to the top."""
        at = item.data(Qt.UserRole)
        if at is None:
            return
        self.open(at)

    def open(self, at: int) -> None:
        """Unfold section `at` and bring it into view.

        Args:
            at: Its position in `self.sections`.
        """
        section = self.sections[at]
        section.head.setChecked(True)
        # After the unfolded rows are laid out, or the section's y is the folded one.
        QTimer.singleShot(0, lambda: self.scroll_to(section))

    def scroll_to(self, section: Section) -> None:
        """Bring a section to the top, or as near as the scroll reaches, on a section's edge.

        Args:
            section: The section to show.

        Near the end the bar cannot reach the section's y; stopping at its maximum would cut
        the first visible row in half, so it stops at the last section top above that.
        """
        bar = self.scroll.verticalScrollBar()
        target = min(section.y(), bar.maximum())
        bar.setValue(max([s.y() for s in self.sections if s.y() <= target], default=0))

    def say(self, text: str, colour: str) -> None:
        """Put one line on the status bar of the zone, in the colour of what happened."""
        self.status.setText(text)
        self.status.setStyleSheet(f"color: {colour};")

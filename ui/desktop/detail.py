"""One template's page: what it is, what is on disk, where it ran, and the two writes."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QPlainTextEdit, QPushButton, QScrollArea, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.shape import shape_panel
from ui.desktop.theme import (C, STATUS_COLOUR, STATUS_HELP, VERDICT_LABEL, chip,
                              verdict_colour, verdict_label)

RUN_COLUMNS = ("Activo", "TF", "Fecha", "Proyecto", "Constr.", "Retenidas", "Veredicto")


class Detail(QWidget):
    """The right-hand page of the catalogue, one template at a time."""

    changed = Signal()

    def __init__(self) -> None:
        """Build the scrolling page; it stays empty until a template is selected."""
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(self.scroll)
        self.name = ""
        self.show_empty()

    def page(self) -> QVBoxLayout:
        """Swap in a fresh page and hand back its layout.

        Returns:
            The layout to fill. Rebuilding beats updating: a template's page has a variable
            number of runs, and a diffing path would be more code than a redraw of ten rows.
        """
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(22, 18, 22, 22)
        lay.setSpacing(14)
        self.scroll.setWidget(body)
        return lay

    def show_empty(self) -> None:
        """The placeholder shown before anything is selected."""
        lay = self.page()
        msg = QLabel("Elige una plantilla a la izquierda, o una celda de la matriz.",
                     objectName="muted")
        msg.setAlignment(Qt.AlignCenter)
        lay.addStretch()
        lay.addWidget(msg)
        lay.addStretch()

    def load(self, name: str) -> None:
        """Draw one template's whole record.

        Args:
            name: Template name as it appears in the registry.
        """
        self.name = name
        t = client.get(f"template/{name}")
        lay = self.page()
        lay.addWidget(QLabel(name, objectName="h1"))
        lay.addWidget(self.chips(t))
        lay.addWidget(self.disk(t))
        if t.get("entry"):
            entry = QLabel(t["entry"])
            entry.setWordWrap(True)
            lay.addWidget(entry)
        lay.addWidget(self.controls(t))
        if t.get("reach"):
            lay.addWidget(QLabel("Qué rellena el builder", objectName="h2"))
            lay.addWidget(shape_panel(t))
        lay.addWidget(QLabel("Corridas", objectName="h2"))
        lay.addWidget(self.runs(t))
        if t["brief_md"]:
            lay.addWidget(QLabel("Brief", objectName="h2"))
            lay.addWidget(self.brief(t["brief_md"]))
        lay.addStretch()

    def chips(self, t: dict) -> QLabel:
        """The status, archetype and shape of a template, as coloured labels.

        Args:
            t: The template record.

        Returns:
            A rich-text label carrying one chip per fact that is present.
        """
        parts = [chip(t.get("status") or "sin estado", STATUS_COLOUR.get(t.get("status", ""),
                                                                        C["faint"]))]
        for field in ("archetype", "shape", "origin", "created"):
            if t.get(field):
                parts.append(chip(t[field], C["muted"]))
        label = QLabel(" ".join(parts))
        label.setToolTip(STATUS_HELP.get(t.get("status", ""), ""))
        return label

    def disk(self, t: dict) -> QLabel:
        """What the folder under the library actually holds.

        Args:
            t: The template record.

        Returns:
            A one-line label. The registry is a claim and this is the evidence: a row whose
            folder is missing has to be visible, because SQX fails silently on a template
            whose blocks are not installed.
        """
        d = t["disk"]
        if not d["exists"]:
            text = f'<span style="color:{C["dead"]}">La carpeta no existe: {d["path"]}</span>'
        else:
            bits = [("template.sqx", d["sqx"]), ("brief.md", d["brief"]),
                    (f"deps/ ({len(d['deps'])})", bool(d["deps"]))]
            text = " · ".join(chip(n, C["promising"] if ok else C["dead"]) for n, ok in bits)
        label = QLabel(text)
        label.setToolTip(f"{d['path']}\n\ndeps/ es lo que hace la carpeta autocontenida: sin los "
                         "bloques al lado, la plantilla desaparece en silencio del builder de otra "
                         "instalación.")
        return label

    def controls(self, t: dict) -> QFrame:
        """The status selector and the note field — the only two writes this page makes.

        Args:
            t: The template record.

        Returns:
            A framed row of controls wired to the daemon.
        """
        f = QFrame(objectName="panel")
        lay = QHBoxLayout(f)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)
        lay.addWidget(QLabel("Estado:", objectName="muted"))
        box = QComboBox()
        statuses = client.get("templates")["statuses"]
        box.addItems(statuses)
        box.setCurrentText(t.get("status") or "draft")
        box.setToolTip("\n".join(f"{s}: {STATUS_HELP[s]}" for s in statuses))
        lay.addWidget(box)
        note = QPlainTextEdit(t.get("notes", ""))
        note.setFixedHeight(38)
        note.setPlaceholderText("Nota — por qué está en este estado, qué falta")
        lay.addWidget(note, 1)
        save = QPushButton("Guardar", objectName="primary")
        save.clicked.connect(lambda: self.save_status(box.currentText(), note.toPlainText()))
        lay.addWidget(save)
        return f

    def save_status(self, status: str, notes: str) -> None:
        """Write the status and note back through the daemon and redraw.

        Args:
            status: The chosen lifecycle state.
            notes: The note as typed; it replaces whatever was stored.
        """
        client.post(f"template/{self.name}/status", {"status": status, "notes": notes})
        self.load(self.name)
        self.changed.emit()

    def runs(self, t: dict) -> QTableWidget:
        """Every market this template was tried on, with an editable verdict.

        Args:
            t: The template record.

        Returns:
            A table, one row per run, the verdict column a live selector.
        """
        table = QTableWidget(len(t["runs"]), len(RUN_COLUMNS))
        table.setHorizontalHeaderLabels(RUN_COLUMNS)
        table.verticalHeader().hide()
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        table.setColumnWidth(6, 170)
        table.setFixedHeight(46 + 40 * max(len(t["runs"]), 1))
        table.verticalHeader().setDefaultSectionSize(40)
        for r, run in enumerate(t["runs"]):
            for c, key in enumerate(("symbol", "timeframe", "date", "project",
                                     "strategies_built", "strategies_kept")):
                item = QTableWidgetItem(run.get(key, ""))
                item.setFlags(Qt.ItemIsEnabled)
                item.setToolTip(run.get("report", ""))
                table.setItem(r, c, item)
            table.setCellWidget(r, 6, self.verdict_box(run))
        return table

    def verdict_box(self, run: dict) -> QComboBox:
        """The verdict selector for one run.

        Args:
            run: The run row.

        Returns:
            A combo that writes straight through on change. The verdict is the owner's
            judgement of a run, so it is one click and not a form with a save button.
        """
        box = QComboBox()
        for value, label in VERDICT_LABEL.items():
            box.addItem(label, value)
        stored = run.get("verdict", "")
        # A value outside the three is kept as its own entry rather than dropped: the row
        # says something, and a combo that quietly showed «sin veredicto» would lose it the
        # next time anyone touched it.
        if stored not in VERDICT_LABEL:
            box.addItem(verdict_label(stored), stored)
        box.setCurrentIndex(box.findData(stored))
        box.setStyleSheet(f"color: {verdict_colour(stored)};")
        box.currentIndexChanged.connect(
            lambda _, b=box, r=run: self.save_verdict(r, b.currentData()))
        return box

    def save_verdict(self, run: dict, verdict: str) -> None:
        """Record a run's verdict through the daemon.

        Args:
            run: The run row being judged.
            verdict: One of the verdicts, or "" to take it back.
        """
        client.post("verdict", {"template": run["template"], "symbol": run["symbol"],
                                "timeframe": run["timeframe"], "verdict": verdict})
        self.load(self.name)
        self.changed.emit()

    def brief(self, text: str) -> QPlainTextEdit:
        """The Spanish brief, shown verbatim and read-only.

        Args:
            text: The contents of brief.md.

        Returns:
            A read-only box. The brief is the author's own words; this window does not
            summarise it and does not let it be edited behind the file's back.
        """
        box = QPlainTextEdit(text)
        box.setReadOnly(True)
        box.setFixedHeight(280)
        return box

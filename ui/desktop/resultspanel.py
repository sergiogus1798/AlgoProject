"""One strategy's page: what every module already said about it, and the command for what none did."""

import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ui.desktop.theme import C, chip, state_colour

# The row fields that carry the module's decision, in the order one is looked for.
DECISION = ("verdict", "tier", "reason", "confidence")
# A module that wrote about the strategy many times (curate keeps every pass) shows this
# many, newest first, and says how many more there are.
SHOWN = 3


def rule() -> QFrame:
    """A one-pixel horizontal line.

    Returns:
        The frame the stylesheet paints as a rule.
    """
    return QFrame(objectName="rule")


def kicker(text: str) -> QLabel:
    """A small spaced-out heading.

    Args:
        text: Upper-cased on screen.

    Returns:
        The label.
    """
    return QLabel(text.upper(), objectName="kicker")


class ResultsPanel(QScrollArea):
    """The right-hand column: the strategy's name, then one block per module."""

    run = Signal(str)   # module key

    def __init__(self) -> None:
        """Start empty, saying that nothing is selected."""
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.show_empty("Elige una estrategia en la tabla.")

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 — Qt's name
        """Keep the page exactly as wide as the viewport, so long lines wrap instead of
        pushing the buttons off the right edge.

        Args:
            event: Qt's resize event.
        """
        super().resizeEvent(event)
        self.widget().setFixedWidth(self.viewport().width())

    def show_empty(self, text: str) -> None:
        """Replace the page with one line.

        Args:
            text: What to say.
        """
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(QLabel(text, objectName="dim"))
        lay.addStretch()
        self.setWidget(page)

    def show(self, strategy: str, data: dict, jobs: list[dict]) -> None:
        """Draw one strategy's results.

        Args:
            strategy: Its name.
            data: What `/api/results` returned.
            jobs: The daemon's jobs on this strategy still running or just ended, whose
                block shows their state and the end of their log instead of a button.
        """
        by_module = {j["label"]: j for j in jobs}
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 12, 0)
        lay.setSpacing(6)
        lay.addWidget(kicker("estrategia"))
        lay.addWidget(QLabel(strategy, objectName="figure"))
        have = sum(1 for m in data["modules"] if m["hits"])
        lay.addWidget(QLabel(f"{have} de {len(data['modules'])} módulos con resultado · "
                             f"{len(data['pages'])} páginas · "
                             f"{'en el pipeline' if data['stages'] else 'fuera del pipeline'}",
                             objectName="dim"))
        for path in data["pages"]:
            b = QPushButton("abrir informe html")
            b.setToolTip(path)
            b.clicked.connect(lambda _, p=path: webbrowser.open(f"file://{p}"))
            lay.addWidget(b, alignment=Qt.AlignLeft)
        if data["stages"]:
            lay.addWidget(rule())
            lay.addWidget(self.stages(data["stages"]))
        for m in data["modules"]:
            lay.addWidget(rule())
            lay.addWidget(self.module(m, by_module.get(m["module"])))
        for name, hits in data["others"].items():
            lay.addWidget(rule())
            lay.addWidget(self.module({"module": name, "label": name, "step": "?",
                                       "hits": hits, "reason": ""}, None))
        lay.addStretch()
        self.setWidget(page)

    def stages(self, state: dict) -> QWidget:
        """The pipeline ledger's stages, each with its progress and status line.

        Args:
            state: `state.json` decoded.

        Returns:
            A block headed «pipeline».
        """
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(2)
        lay.addWidget(kicker(f"pipeline · etapa {state['stage']}"))
        for name, s in state["stages"].items():
            colour = C["promising"] if s.get("done_at") else C["weak"]
            line = QLabel(f"{chip(name, colour)} &nbsp;{s['progress']:>3}%  "
                          f"<span style='color:{C['faint']}'>{s['status']}</span>",
                          objectName="mono")
            line.setWordWrap(True)
            lay.addWidget(line)
        return box

    def module(self, m: dict, job: dict | None) -> QWidget:
        """One module's block: its results, then the button that runs it or why there is none.

        Args:
            m: An entry of `modules`, carrying `argv` or `reason`.
            job: The daemon's job of this module on this strategy, when one runs or just
                ended; its state and log tail take the button's place.

        Returns:
            The block.
        """
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(3)
        head = QHBoxLayout()
        head.addWidget(kicker(f"{m['label']}"))
        head.addWidget(QLabel(f"paso {m['step']}", objectName="dim"))
        head.addStretch()
        if job:
            head.addWidget(self.job_state(job))
        elif "argv" in m:
            b = QPushButton("correr" if not m["hits"] else "correr otra vez")
            b.setToolTip("python3 " + " ".join(m["argv"]) + "\n\nEl demonio lo lanza en "
                         "segundo plano; la ficha se redibuja cuando termina.")
            b.clicked.connect(lambda _, k=m["module"]: self.run.emit(k))
            head.addWidget(b)
        lay.addLayout(head)
        if not job and "argv" not in m and m["reason"]:
            reason = QLabel(m["reason"], objectName="dim")
            reason.setWordWrap(True)
            lay.addWidget(reason)
        if job:
            log = QLabel("\n".join(job["tail"]), objectName="dim")
            log.setWordWrap(True)
            log.setTextInteractionFlags(Qt.TextSelectableByMouse)
            log.setToolTip(job["log"])
            lay.addWidget(log)
        if not m["hits"] and not job:
            lay.addWidget(QLabel("sin resultado", objectName="dim"))
        for h in m["hits"][:SHOWN]:
            lay.addWidget(self.hit(h))
        if len(m["hits"]) > SHOWN:
            lay.addWidget(QLabel(f"y {len(m['hits']) - SHOWN} resultados más antiguos",
                                 objectName="dim"))
        return box

    def job_state(self, job: dict) -> QLabel:
        """How one job stands, as a chip.

        Args:
            job: The daemon's record.

        Returns:
            Amber while it runs, green when it ended with exit code 0, red otherwise.
        """
        if job["rc"] is None:
            return QLabel(chip(f"en curso desde {job['started'][11:]}", C["weak"]))
        if job["rc"] == 0:
            return QLabel(chip("terminó", C["promising"]))
        return QLabel(chip(f"falló, código {job['rc']}", C["dead"]))

    def hit(self, h: dict) -> QWidget:
        """One report row about the strategy.

        Args:
            h: `{databank, date, file, n, row}`.

        Returns:
            The where-and-when line, the decision as a chip, then every other field.
        """
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 2, 0, 4)
        lay.setSpacing(2)
        more = f" · {h['n']} filas, se muestra la primera" if h["n"] > 1 else ""
        where = QLabel(f"{h['databank']} · {h['date']} · {h['file']}{more}", objectName="dim")
        where.setWordWrap(True)
        lay.addWidget(where)
        row = dict(h["row"])
        chips = "".join(chip(f"{k} {row.pop(k)}", state_colour(str(h['row'][k])))
                        + " " for k in DECISION if k in row)
        if chips:
            lay.addWidget(QLabel(chips, objectName="mono"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(1)
        for i, (k, v) in enumerate(row.items()):
            grid.addWidget(QLabel(k, objectName="dim"), i // 2, (i % 2) * 2)
            value = QLabel(short(v), objectName="mono")
            value.setWordWrap(True)
            grid.addWidget(value, i // 2, (i % 2) * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        lay.addLayout(grid)
        return box


def short(value: str) -> str:
    """A report figure as the panel prints it.

    Args:
        value: The CSV text.

    Returns:
        Floats to four significant digits, anything else cut at 40 characters.
    """
    try:
        return f"{float(value):.4g}"
    except ValueError:
        return value if len(value) <= 40 else value[:39] + "…"

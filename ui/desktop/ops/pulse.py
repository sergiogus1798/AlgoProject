"""The custodian's pulse inside «En marcha»: the line of a long run, its figures explained, the last readings."""

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QVBoxLayout)

from ui.desktop import client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C, MONO, T

POLL_MS = 60_000            # each reading costs the daemon half a second of CPU sampling
KEPT = 30                   # readings the history keeps, newest first
HISTORY_PX = 120            # the history is a strip under the figures, not the zone's body

# Every figure on screen carries what it is and where it comes from.
FIGURES = [
    ("proyecto", "project", "El último proyecto arrancado según el log de hoy del custodio."),
    ("tarea", "task", "La tarea que el log de SQX da por empezada y no terminada."),
    ("ritmo", "rate_per_min", "Backtests por minuto desde que arrancó el proyecto: hechos ÷ "
                              "minutos transcurridos."),
    ("falta", "eta_min", "Minutos hasta terminar al ritmo medio de hasta ahora."),
    ("JVM / techo", "jvm", "Memoria proporcional (PSS de /proc/<pid>/smaps_rollup, no RSS) "
                           "del ./sqcli contra el -Xmx de sqcli.config."),
    ("caben", "fits_more", "Backtests que caben todavía: el menor de (techo − JVM) y la RAM "
                           "libre, dividido por lo que crece el JVM por backtest."),
    ("pendiente", "slope", "MB que crece el JVM por backtest. «medida» sale de las lecturas "
                           "de este run; «supuesta» es 10 MB, el centro de los 8–12 MB "
                           "medidos en el retest de 5.000 variantes."),
    ("avance de", "progress_from", "De dónde sale la cuenta: el log del trabajo de la ventana "
                                   "que imprimió la última línea «PROGRESS n de N», o, para un "
                                   "run lanzado fuera de la ventana, el estado del custodio "
                                   "(action=status) de la tarea en curso. «?» cuando ninguno "
                                   "da cuenta."),
]


def figure(p: dict, key: str) -> str:
    """One figure of a pulse as the zone prints it.

    Args:
        p: The `custodian` block of `/api/pulse`.
        key: A key of `FIGURES`.

    Returns:
        The text, «—» when the reading has no such figure.
    """
    if key == "jvm":
        return ("—" if p.get("jvm_gb") is None else
                f"{num(round(p['jvm_gb'], 1))} de {num(round(p['xmx_gb']))} GB")
    if key == "slope":
        return ("—" if p.get("slope_mb") is None else
                f"{num(round(p['slope_mb'], 1))} MB "
                f"({'medida' if p['slope_measured'] else 'supuesta'})")
    value = p.get(key)
    if value is None:
        return "—"
    if key == "rate_per_min":
        return f"{num(round(value))} / min"
    if key == "eta_min":
        return f"{num(round(value))} min"
    if key == "fits_more":
        return num(value)
    return str(value)


class Pulse(QFrame):
    """The custodian's pulse, read from the daemon every minute while the zone is on screen."""

    def __init__(self) -> None:
        """Build the line, the figures, the warnings and the history."""
        super().__init__(objectName="term")
        self.last: dict = {}            # the newest reading, for «En marcha»'s own line
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        head = QHBoxLayout()
        head.addWidget(QLabel("PULSO DEL CUSTODIO · SQX_w2 · /proc, LOGS Y SU LÍNEA DE ESTADO",
                              objectName="kicker"))
        head.addStretch(1)
        now = QPushButton("Leer ahora")
        now.clicked.connect(self.refresh)
        head.addWidget(now)
        lay.addLayout(head)
        self.line = QLabel("sin lectura todavía", styleSheet=f"font-family: {MONO}; "
                                                              "font-size: 20px; font-weight: 700;")
        self.line.setToolTip("hora · backtests hechos de total · memoria del JVM · CPU (100% = "
                             "un núcleo) · RAM libre de la máquina (MemAvailable) · cuántos "
                             "backtests caben todavía")
        lay.addWidget(self.line)
        self.warn = QLabel("", wordWrap=True, styleSheet=f"color: {C['dead']}; "
                                                         f"font-family: {MONO}; font-size: 14px;")
        lay.addWidget(self.warn)
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        self.values: dict[str, QLabel] = {}
        for i, (name, key, tip) in enumerate(FIGURES):
            title = QLabel(label(name), objectName="kicker", toolTip=tip)
            value = QLabel("—", objectName="mono", toolTip=tip)
            grid.addWidget(title, i // 4 * 2, i % 4)
            grid.addWidget(value, i // 4 * 2 + 1, i % 4)
            self.values[key] = value
        lay.addLayout(grid)
        lay.addWidget(QLabel("ÚLTIMAS LECTURAS · EN MEMORIA, SE PIERDEN AL CERRAR",
                             objectName="kicker"))
        self.history = QListWidget()
        self.history.setMaximumHeight(HISTORY_PX)
        lay.addWidget(self.history)
        self.poll = QTimer(self)
        self.poll.setInterval(POLL_MS)
        self.poll.timeout.connect(self.refresh)

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Read at once and keep reading while on screen.

        Args:
            event: Qt's show event, unused.
        """
        self.refresh()
        self.poll.start()

    def hideEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Stop reading: nobody is looking.

        Args:
            event: Qt's hide event, unused.
        """
        self.poll.stop()

    def refresh(self) -> None:
        """Ask the daemon for one reading, or say it is not answering."""
        try:
            self.show_pulse(client.get("pulse")["custodian"])
        except httpx.HTTPError as down:
            self.warn.setText(f"demonio no responde: {type(down).__name__}")

    def show_pulse(self, p: dict) -> None:
        """Paint one reading and push it onto the history.

        Args:
            p: The `custodian` block of `/api/pulse`.
        """
        self.last = p
        colour = C["dead"] if p["warn"] else (C["promising"] if p["up"] else T["muted"])
        self.line.setText(p["line"])
        self.line.setStyleSheet(f"font-family: {MONO}; font-size: 20px; font-weight: 700; "
                                f"color: {colour};")
        self.warn.setText("\n".join(f"⚠ {w}" for w in p["warn"]))
        for key, value in self.values.items():
            value.setText(figure(p, key))
        item = QListWidgetItem(p["line"] + ("   ⚠ " + " · ".join(p["warn"]) if p["warn"] else ""))
        item.setForeground(QColor(C["dead"] if p["warn"] else T["text"]))
        self.history.insertItem(0, item)
        while self.history.count() > KEPT:
            self.history.takeItem(KEPT)

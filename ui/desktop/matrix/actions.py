"""The two things the matrix does besides looking: run one study on the chosen rows, and show the /curate command."""

import httpx
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout, QWidget)

from ui.desktop import client
from ui.desktop.theme import C

CURATE_WHY = ("La ventana nunca toca SQX: copia este comando en una sesión de Claude. Aplicar un "
              "veredicto es una búsqueda más que reduce la población, y el skill la anota en el "
              "ledger; las estrategias con DESCARTAR se borran del databank tras dejar registro.")


def curate_command(project: str, databank: str, study: str, day: str) -> str:
    """The line the owner pastes to apply one study's verdict.

    Args:
        project: SQX project name.
        databank: Databank name as the report folder spells it.
        study: Study key whose verdict.csv drops strategies.
        day: Report day of that verdict.

    Returns:
        The `/curate` invocation naming the verdict file under the data root.
    """
    return (f"/curate {project} {databank} con el veredicto "
            f"AlgoData/reports/{project}/{databank}/{day}/{study}/verdict.csv")


class RunBar(QWidget):
    """Pick a study that runs on one strategy, press ▶, and one job per chosen row is queued."""

    def __init__(self) -> None:
        """Build the combo, the button and the line that answers."""
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        self.study = QComboBox()
        self.study.setToolTip("Estudios que se corren sobre una estrategia a la vez. Los que "
                              "no pueden empezar desde la ventana dicen por qué al pulsar.")
        self.go = QPushButton("▶ correr en las seleccionadas")
        self.go.setToolTip("Una tarea por estrategia seleccionada (Ctrl/Mayús + clic en el "
                           "nombre para elegir varias). Se encola; el resultado aparece aquí "
                           "al volver a leer.")
        self.answer = QLabel("")
        self.answer.setObjectName("dim")
        self.answer.setWordWrap(True)
        row.addWidget(QLabel("CORRER"))
        row.addWidget(self.study)
        row.addWidget(self.go)
        row.addWidget(self.answer, 1)

    def offer(self, catalogue: list[dict]) -> None:
        """Fill the combo with the studies that have a per-strategy run.

        Args:
            catalogue: `/api/catalogue` rows.
        """
        self.study.clear()
        for e in catalogue:
            if e["one"] and e["runnable"]:
                self.study.addItem(f"{e['title']} ({e['key']})", e["key"])

    def say(self, text: str, tone: str) -> None:
        """Print the answer in one of the verdict colours."""
        self.answer.setText(text)
        self.answer.setStyleSheet(f"color: {C[tone]};")

    def run(self, project: str, databank: str, asset: str, names: list[str]) -> dict:
        """Ask the daemon to queue the chosen study on these strategies.

        Args:
            project, databank, asset: Where they live.
            names: Strategy names of the selected rows.

        Returns:
            The daemon's answer, or `{"error"}` when nothing was selected or the daemon
            could not be reached — shown, never raised (ui boundary).
        """
        if not names:
            answer = {"error": "Selecciona antes al menos una estrategia (clic en su nombre)."}
        else:
            try:
                answer = client.post("study/run", {
                    "study": self.study.currentData(), "scope": "one", "project": project,
                    "databank": databank, "strategies": names, "asset": asset or ""})
            except httpx.HTTPError as e:
                answer = {"error": f"El demonio no respondió: {e}"}
        if "error" in answer:
            self.say(f"No se lanzó: {answer['error']}", "dead")
        else:
            self.say(f"{len(answer['jobs'])} tareas de {self.study.currentData()} en cola "
                     f"(ver Trabajos).", "promising")
        return answer


class CurateStrip(QFrame):
    """The /curate command of one gate column, to copy, and the sentence that says what applying it means."""

    def __init__(self) -> None:
        """Build the hidden strip."""
        super().__init__()
        self.setStyleSheet(f"CurateStrip {{ border: 1px solid {C['dead']}; }}")
        box = QVBoxLayout(self)
        box.setContentsMargins(8, 6, 8, 6)
        top = QHBoxLayout()
        self.title = QLabel("")
        self.title.setObjectName("kicker")
        close = QPushButton("✕")
        close.clicked.connect(self.hide)
        top.addWidget(self.title, 1)
        top.addWidget(close)
        box.addLayout(top)
        line = QHBoxLayout()
        self.command = QLineEdit()
        self.command.setReadOnly(True)
        copy = QPushButton("copiar")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.command.text()))
        line.addWidget(self.command, 1)
        line.addWidget(copy)
        box.addLayout(line)
        why = QLabel(CURATE_WHY)
        why.setWordWrap(True)
        why.setObjectName("dim")
        box.addWidget(why)
        self.hide()

    def show_for(self, project: str, databank: str, entry: dict, day: str, drops: int) -> None:
        """Show the command for one gate study.

        Args:
            project, databank: Where.
            entry: The study's catalogue row.
            day: Its newest report day in this databank.
            drops: How many of its cells here read `fail`.
        """
        self.title.setText(f"⊘ APLICAR {entry['title'].upper()} ({day}) · {drops:,} con «falla»")
        self.command.setText(curate_command(project, databank, entry["key"], day))
        self.show()

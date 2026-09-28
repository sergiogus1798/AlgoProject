"""«En marcha»: the custodian's pulse and one project's tasks — the same project, one screen."""

import httpx
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QSplitter, QVBoxLayout

from ui.desktop import client
from ui.desktop.ops.pulse import Pulse
from ui.desktop.ops.tasks import Tasks
from ui.desktop.selection import SELECTION
from ui.desktop.theme import C, kicker

ROLE = {"custodian": "custodio · SQX_w2", "conductor": "conductor · SQX_w1", "master": "maestro"}
ORDER = ("custodian", "conductor", "master")     # where a selected project is looked for first
EVERY_MS = 3000
PICKER_TIP = ("La ventana lee ficheros del install y, solo mientras un worker corre el proyecto, "
              "le pide su línea de estado (action=status, lo único que el custodio puede recibir "
              "a mitad de trabajo). No arranca, no para, no reconfigura. Al abrir se elige sola "
              "el proyecto que corre; si nada corre, el proyecto elegido en la ventana.")


class Running(QFrame):
    """One picker for both halves: the pulse above, the project's tasks below."""

    def __init__(self) -> None:
        """Build the header with its pickers, the line that ties both halves, and the split."""
        super().__init__(objectName="term")
        self.data: dict[str, list[str]] = {}
        self.by_hand = False                 # once the owner picks, the zone stops choosing
        self.timer = QTimer(self)
        self.timer.setInterval(EVERY_MS)
        self.timer.timeout.connect(self.refresh)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)
        head = QHBoxLayout()
        head.addWidget(QLabel("En marcha", objectName="h1"))
        head.addSpacing(12)
        head.addWidget(kicker("install"))
        self.install = QComboBox(toolTip=PICKER_TIP)
        self.install.activated.connect(self.install_picked)
        head.addWidget(self.install)
        head.addWidget(kicker("proyecto"))
        self.project = QComboBox(toolTip=PICKER_TIP, minimumWidth=300)
        self.project.activated.connect(self.project_picked)
        head.addWidget(self.project)
        head.addStretch()
        lay.addLayout(head)
        self.note = QLabel("", objectName="dim", wordWrap=True)
        lay.addWidget(self.note)
        split = QSplitter(Qt.Vertical)
        self.pulse = Pulse()
        self.tasks = Tasks()
        split.addWidget(self.pulse)
        split.addWidget(self.tasks)
        split.setSizes([300, 540])
        lay.addWidget(split, 1)

    def reload(self) -> None:
        """Ask the daemon which installs and projects exist, and choose what to show."""
        self.data = client.get("progress/installs")
        role, project = self.install.currentText(), self.project.currentText()
        if not self.by_hand:
            role, project = self.default()
        self.install.clear()
        for r in self.data:
            self.install.addItem(r)
            self.install.setItemData(self.install.count() - 1, ROLE.get(r, r), Qt.ToolTipRole)
        self.install.setCurrentText(role if role in self.data else "custodian")
        self.fill_projects(project)

    def default(self) -> tuple[str, str]:
        """What the zone shows when the owner has not picked: the running project first.

        Returns:
            The install and project of the first worker running something (custodian
            first); else the window's selected project on the first install holding it;
            else the custodian with no project.
        """
        runs = client.get("ops/sqx")["runs"]
        if runs:
            return runs[0]["role"], runs[0]["project"]
        chosen = SELECTION.now["project"]
        for role in ORDER:
            if chosen and chosen in self.data.get(role, []):
                return role, chosen
        # Never a stock project (Builder, Retester) by default: no run of ours lives there
        # (CLAUDE.md rule 10), and ours are the ones named Test_ or Trade_ (rule 6).
        ours = [p for p in self.data.get("custodian", []) if p.startswith(("Test_", "Trade_"))]
        return "custodian", ours[0] if ours else ""

    def fill_projects(self, keep: str) -> None:
        """List the picked install's projects, keep one if it is there, and redraw.

        Args:
            keep: The project to leave selected when the install holds it.
        """
        names = self.data.get(self.install.currentText(), [])
        self.project.clear()
        self.project.addItems(names)
        self.project.setCurrentText(keep if keep in names else (names[0] if names else ""))
        self.refresh()

    def install_picked(self) -> None:
        """The owner chose an install: from now on the zone keeps his choice."""
        self.by_hand = True
        self.fill_projects(self.project.currentText())

    def project_picked(self) -> None:
        """The owner chose a project: from now on the zone keeps his choice."""
        self.by_hand = True
        self.refresh()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 — Qt's name
        """Fill on first sight, then refresh the tasks every three seconds while on screen.

        Args:
            event: Qt's show event.
        """
        super().showEvent(event)
        if not self.data:
            self.reload()
        self.timer.start()

    def hideEvent(self, event: QHideEvent) -> None:  # noqa: N802 — Qt's name
        """Stop asking when nobody is looking.

        Args:
            event: Qt's hide event.
        """
        super().hideEvent(event)
        self.timer.stop()

    def refresh(self) -> None:
        """Redraw the tasks and the line that says whether both halves are one run."""
        role, project = self.install.currentText(), self.project.currentText()
        if not project:
            self.note.setText("Este install no tiene proyectos.")
            return
        try:
            self.tasks.load(role, project)
        except httpx.HTTPError as down:
            self.note.setText(f"demonio no responde: {type(down).__name__}")
            return
        self.note.setText(self.relation(role, project))

    def relation(self, role: str, project: str) -> str:
        """Whether the pulse above and the table below describe the same run.

        Args:
            role: The install picked.
            project: The project picked.

        Returns:
            One sentence; amber when the two halves are different runs.
        """
        p = self.pulse.last
        where = ROLE.get(role, role)
        self.note.setStyleSheet("")
        if not p.get("up"):
            return (f"El custodio está parado: el pulso solo lee la RAM libre. La tabla es de "
                    f"{project} en {where}.")
        if role == "custodian" and p.get("project") == project:
            return f"El pulso y la tabla son el mismo run: {project} en {where}."
        self.note.setStyleSheet(f"color:{C['weak']};")
        running = p.get("project") or "un proyecto que su log no nombra"
        return (f"El pulso es del custodio, que corre {running}; la tabla es de {project} en "
                f"{where}. Elige ese proyecto arriba para verlos juntos.")

"""«Continuar workflow»: the one button of the window that deletes in SQX, behind its preflight."""

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QSizePolicy, QWidget)

from ui.desktop import background, client
from ui.desktop.workspace.aggregate import ask
from ui.text.brief import full, off

RECHECK_MS = 20_000     # a filter applied or a worker started elsewhere shows up within this


class Advance(QWidget):
    """Its own databank chooser, the button and, beside it, why it is off. It lives in
    Proyecto, away from the panel it acts on: the chooser offers the project's live databanks
    and picks the first with discards (else the one Databanks shows), pinned once on screen
    or picked, until the project changes or a Continuar is queued. `aim(project, databank)` asks the daemon's preflight; the button is enabled only when
    every check passes, and a click asks the owner to confirm the literal sentence of encargo
    22 §7.2 before anything is queued."""

    def __init__(self) -> None:
        """Build it off; nothing is aimed yet."""
        super().__init__()
        self.project, self.databank, self.text, self.pinned = "", "", "", False
        kicker = QLabel("CONTINUAR SOBRE")
        kicker.setObjectName("kicker")
        self.bank = QComboBox()
        self.bank.setMinimumContentsLength(18)
        self.bank.setToolTip("El databank cuyos descartes se borran en SQX antes de arrancar la "
                             "tarea siguiente. Al abrir el proyecto elige el primero con "
                             "descartes (si no, el que muestra Databanks) y ya no cambia solo: "
                             "sólo si eliges otro, cambias de proyecto o se lanza el Continuar.")
        self.bank.activated.connect(self.picked)
        self.button = QPushButton("▶▶ Continuar workflow")
        self.button.clicked.connect(self.confirm)
        # A disabled button never shows its tooltip: the reason is a visible line instead.
        self.why = QLabel("")
        self.why.setObjectName("dim")
        self.why.setWordWrap(True)
        self.why.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(kicker)
        lay.addWidget(self.bank)
        lay.addWidget(self.button)
        lay.addWidget(self.why, 1)
        self.show_state({"ok": False, "reasons": ["elige un databank"]})
        self.panel, self.funnel = None, None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.follow)

    def attach(self, panel: QWidget, funnel: QWidget) -> "Advance":
        """Follow a databank panel: re-aim whenever it paints a table, and every RECHECK_MS.

        Args:
            panel: The Databanks zone's `Panel`: its tabs list the live databanks.
            funnel: Proyecto's `Funnel`: its filter rows say which databanks have discards.

        Returns:
            Itself, so the zone mounts it in one line.
        """
        self.panel, self.funnel = panel, funnel
        panel.table.model().modelReset.connect(lambda: QTimer.singleShot(0, self.follow))
        self.timer.start(RECHECK_MS)
        return self

    def live(self) -> list[str]:
        """The project's databanks that some unlocked sub-panel reads, in the panel's order."""
        banks = [s["databank"] for t in self.panel.tabs for s in t["subs"]
                 if s.get("databank") and not s.get("blocked")] if self.panel.live else []
        return list(dict.fromkeys(banks))

    def default(self, banks: list[str]) -> str:
        """The first databank with discards (what Continuar acts on), else the one Databanks
        shows, else the first."""
        cut = {r["screen"].split(" · ", 1)[1] for r in self.funnel.bars.rows
               if r["screen"].startswith(("Filtro · ", "A mano · "))}
        shown = self.panel.sub_spec().get("databank")
        return next((b for b in banks if b.replace(" ", "_") in cut),
                    shown if shown in banks else banks[0])

    def repoint(self, project: str) -> None:
        """Proyecto filled a project: a different one drops the pin, whether or not the zone
        is on screen (A → B → A while hidden repoints too); then follow."""
        if project != self.project:
            self.project, self.pinned = project, False
        self.follow()

    def follow(self) -> None:
        """Offer the live databanks and aim at the pinned one, or at the default, which is
        pinned the moment it is on screen: the target never moves under the owner's eyes."""
        if not self.isVisible():
            return
        if self.panel.project != self.project:
            self.project, self.pinned = self.panel.project, False
        banks = self.live()
        if banks != [self.bank.itemText(i) for i in range(self.bank.count())]:
            self.bank.blockSignals(True)
            self.bank.clear()
            self.bank.addItems(banks)
            self.bank.blockSignals(False)
        if not banks:
            self.show_state({"ok": False, "reasons": ["el proyecto no tiene ningún databank "
                                                      "vivo"]})
            return
        if not self.pinned or self.bank.currentText() not in banks:
            self.bank.setCurrentText(self.default(banks))
            self.pinned = True
        self.aim(self.project, self.bank.currentText())

    def picked(self, _index: int) -> None:
        """The owner chose a databank: keep it until the project changes or it is continued."""
        self.pinned = True
        self.aim(self.project, self.bank.currentText())

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 — Qt's name
        """Catch up when Proyecto comes into view: the panel may have moved meanwhile."""
        super().showEvent(event)
        if self.panel is not None:
            QTimer.singleShot(0, self.follow)

    def aim(self, project: str, databank: str) -> None:
        """Point the button at one databank and ask the daemon whether it may run.

        Args:
            project: The project on screen.
            databank: The databank of the sub-panel on screen, as SQX spells it.
        """
        self.project, self.databank = project, databank
        background.get("advance/preflight",
                       lambda got: self.show_state(got) if (project, databank) == (
                           self.project, self.databank) else None,
                       key=f"advance:{id(self)}", owner=self, project=project,
                       databank=databank)

    def show_state(self, got: dict) -> None:
        """Enable the button, or disable it with a few words beside it; every reason is in
        their tooltip (owner, 2026-09-30)."""
        reasons = got.get("reasons") or ([got["error"]] if "error" in got else [])
        self.text = got.get("text", "")
        self.button.setEnabled(bool(got.get("ok")))
        self.why.setText("" if got.get("ok") else off(reasons))
        self.why.setToolTip("" if got.get("ok") else full(reasons))

    def confirm(self) -> None:
        """Re-run the preflight on the chosen databank and show its fresh sentence; only «Sí»
        queues the job, and the daemon checks again there. A job queued drops the pin."""
        self.show_state(ask("advance/preflight", project=self.project, databank=self.databank))
        if not self.button.isEnabled():
            return
        if QMessageBox.question(self, "Continuar workflow", self.text + "\n\n¿Confirmas?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            got = client.post("advance/run", {"project": self.project, "databank": self.databank})
        except httpx.HTTPError as failed:
            got = {"ok": False, "reasons": [f"El demonio no respondió: {failed}"]}
        if got.get("job"):
            self.pinned = False
            self.button.setEnabled(False)
            self.why.setText(f"En marcha: {got['task']} — sigue su avance en «En marcha»")
        else:
            self.show_state(got)

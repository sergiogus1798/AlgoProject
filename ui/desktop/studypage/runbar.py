"""The run bar: this strategy, the whole population, one sub-test alone — one job at a time, watched."""

from collections.abc import Callable

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.studypage.net import fetch, send
from ui.desktop.theme import T

POLL_MS = 2000


class RunBar(QWidget):
    """Three buttons and the line of the job they started. Polls `/api/jobs` only while a job
    of this bar runs, and says `finished` when every one of them has ended."""

    finished = Signal()

    def __init__(self, overrides: Callable[[], list[str]]) -> None:
        """Build the buttons, idle.

        Args:
            overrides: Returns the drawer's `--set` strings at the moment of pressing.
        """
        super().__init__()
        self.overrides = overrides
        self.where: dict = {}
        self.entry: dict = {}
        self.ids: list[str] = []
        self.timer = QTimer(self)
        self.timer.setInterval(POLL_MS)
        self.timer.timeout.connect(self.poll)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.one = QPushButton("▶ esta estrategia")
        self.one.setToolTip("Corre el estudio sobre la estrategia elegida, con el cajón de ahora.")
        self.one.clicked.connect(lambda: self.run("one"))
        self.many = QPushButton("▶▶ toda la población")
        self.many.setToolTip("Corre el estudio sobre el databank entero, con el cajón de ahora.")
        self.many.clicked.connect(lambda: self.run("many"))
        self.only = QComboBox()
        self.only.setToolTip("La subprueba que se corre sola; se escribe como una corrida más "
                             "del día y se compara con la anterior desde el historial.")
        self.solo = QPushButton("↻ solo")
        self.solo.clicked.connect(lambda: self.run("one", self.only.currentData()))
        self.cancel = QPushButton("■ cancelar")
        self.cancel.clicked.connect(self.stop)
        for w in (self.one, self.many, self.only, self.solo, self.cancel):
            row.addWidget(w)
        row.addStretch(1)
        lay.addLayout(row)
        self.line = text("", T["text"], 13)
        lay.addWidget(self.line)
        self.error = text("", colour("fail"), 13, True)
        lay.addWidget(self.error)

    def aim(self, entry: dict, where: dict, strategy_page: bool) -> None:
        """Point the bar at one study and one place, showing only what that study can do.

        Args:
            entry: The study's catalogue entry (`one`, `many`, `runnable`, `why_not`).
            where: project, databank, strategy, asset.
            strategy_page: False on the population page, where there is no «esta estrategia».
        """
        same = self.entry.get("key") == entry["key"] and self.where == where
        self.entry, self.where = entry, dict(where)
        if not same:          # the end of the last run stays on screen while it is still this study
            self._say(self.error, "")
            self._say(self.line, "")
        can = entry["runnable"]
        self.one.setVisible(can and entry["one"] and strategy_page)
        self.many.setVisible(can and entry["many"])
        options = (fetch("study/only", study=entry["key"], project=where["project"],
                         databank=where["databank"], asset=where["asset"] or "")
                   .get("options") or []) if can and strategy_page and where["project"] else []
        self.only.clear()
        for o in options:
            self.only.addItem(o["label"], o["key"])
        self.only.setVisible(bool(options))
        self.solo.setVisible(bool(options))
        if not can:
            self._say(self.line, f"No se corre desde aquí: {entry['why_not']}")
        elif not (entry["one"] or entry["many"]):
            self._say(self.line, "Este estudio no tiene orden de corrida para este alcance.")
        self._busy(bool(self.ids))

    def run(self, scope: str, only: str | None = None) -> None:
        """Queue the study through the daemon, and start watching the job.

        Args:
            scope: "one" for the chosen strategy, "many" for the population.
            only: A sub-test key from `/api/study/only`, or None for the whole study.
        """
        w = self.where
        got = send("study/run", {
            "study": self.entry["key"], "scope": scope, "project": w["project"],
            "databank": w["databank"], "asset": w["asset"] or "", "only": only,
            "strategies": [w["strategy"]] if scope == "one" else [],
            "overrides": self.overrides()})
        if "error" in got:
            self._say(self.error, got["error"])
            return
        self._say(self.error, "")
        self.ids = [j["id"] for j in got["jobs"]]
        self._say(self.line, f"en marcha: {self.entry['key']} · {scope}"
                          + (f" · solo {only}" if only else ""))
        self._busy(True)
        self.timer.start()

    def poll(self) -> None:
        """Read this bar's jobs; when all have ended, stop polling and say so."""
        got = fetch("jobs")
        if "error" in got:
            self._say(self.error, got["error"])
            return
        mine = [j for j in got["jobs"] if j["id"] in self.ids]
        parts = []
        for j in mine:
            where = f"en cola, puesto {j['queued']}" if j.get("queued") else j["state"]
            parts.append(f"{j['label']} {j['percent']}% · {where}")
        self._say(self.line, " | ".join(parts) or "el demonio ya no conoce el trabajo")
        if all(j["rc"] is not None for j in mine):
            self.timer.stop()
            failed = [j for j in mine if j["rc"] not in (0, None)]
            if failed:
                tail = "\n".join(failed[0]["tail"][-6:])
                self._say(self.error, f"{failed[0]['state']}:\n{tail}")
            self.ids = []
            self._busy(False)
            self.finished.emit()

    def stop(self) -> None:
        """Cancel this bar's jobs; the next poll reports how they ended."""
        for i in self.ids:
            send(f"jobs/{i}/cancel", {})
        self.poll()

    def _busy(self, busy: bool) -> None:
        """One job at a time: the run buttons wait while one runs, the cancel shows."""
        for b in (self.one, self.many, self.solo):
            b.setEnabled(not busy)
        self.cancel.setVisible(busy)

    def _say(self, label: QLabel, body: str) -> None:
        """Write a line of the bar, hidden while empty so it leaves no gap."""
        label.setText(body)
        label.setVisible(bool(body))

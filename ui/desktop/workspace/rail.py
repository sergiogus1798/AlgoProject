"""The top strip of a project: the workflow rail as map, automation panel and state (22 §4.1)."""

import httpx
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QVBoxLayout)

from ui.desktop import client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C
from ui.desktop.workspace.railconfig import Drawer
from ui.desktop.workspace.railrow import STATE, StepCard, runnable, small

PER_ROW = 10
POLL_MS = 3000


class Rail(QFrame):
    """The whole rail for one project, served by GET /api/workflow. A card click opens its
    tab through the workspace's `show_tab(tab, sub)` (else `opened(tab, sub)`) and shows the
    step's tests in the drawer. While visible and while a job of this project runs it polls
    /api/jobs; each job that ends reloads the rail and emits `finished(study, databank)`."""

    opened = Signal(str, str)
    finished = Signal(str, str)

    def __init__(self) -> None:
        """Build the header, the grid and the drawer; `load` fills them."""
        super().__init__()
        self.setObjectName("term")
        self.project, self.data, self.chosen = "", {}, ""
        self.ticks: dict[tuple[str, str], bool] = {}
        self.live: dict[str, dict] = {}
        head = QHBoxLayout()
        kicker = QLabel("WORKFLOW")
        kicker.setObjectName("kicker")
        head.addWidget(kicker)
        self.summary = small("")
        head.addWidget(self.summary, 1)
        self.backfill = QPushButton(label("Rehacer las filas de 17-19"))
        self.backfill.clicked.connect(self.rebuild)
        head.addWidget(self.backfill)
        self.marked = QPushButton("▶ correr marcados")
        self.marked.clicked.connect(lambda: self.run([k for k, on in self.ticks.items() if on]))
        head.addWidget(self.marked)
        everything = QPushButton("▶▶ correr todo")
        everything.setToolTip(label("Como el play de SQX: toda prueba de Python sin resultado, a la "
                                    "vez, salvo las que gastan oos2 o escriben en el ledger y los "
                                    "pasos 21-25; cada carril un trabajo y paralelo por dentro."))
        everything.clicked.connect(self.run_all)
        head.addWidget(everything)
        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        self.lines = [small("", "mono") for _ in range(4)]
        self.said = self.lines[3]
        self.drawer = Drawer()
        self.drawer.ticked.connect(lambda n, k, on: self.tick([(n, k)], on))
        self.drawer.ran.connect(lambda tests: self.run([(t["n"], t["key"]) for t in tests]))
        self.drawer.tab_ran.connect(self.run_panel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.addLayout(head)
        for line in self.lines:
            line.setWordWrap(True)
            lay.addWidget(line)
        lay.addLayout(self.grid)
        lay.addWidget(self.drawer)
        lay.addStretch(1)       # spare height below, not between the lines
        self.timer = QTimer(self, timeout=self.poll)

    def load(self, project: str) -> None:
        """Ask the daemon for one project's rail and paint it (ui boundary: a failure is shown)."""
        if project != self.project:
            self.project, self.ticks, self.chosen = project, {}, ""
        try:
            got = client.get("workflow", project=project)
        except httpx.HTTPError as failed:
            got = {"error": f"El demonio no respondió: {failed}"}
        if "error" in got:
            self.said.setText(got["error"])
            return
        self.fill(got)

    def fill(self, data: dict) -> None:
        """Lay out the cards, the header's counts, the oos2 and blind lines and the drawer.

        Args:
            data: GET /api/workflow's answer.
        """
        self.data = data
        steps = data["steps"]
        for step in steps:
            for t in step["tests"]:
                self.ticks.setdefault((step["n"], t["key"]), t["auto"]
                                      and t["state"] == "pending" and step["state"] == "pending")
        while self.grid.count():
            gone = self.grid.takeAt(0).widget()
            gone.hide()          # hidden first, or it paints under the new ones until deleted
            gone.deleteLater()
        for i, step in enumerate(steps):
            tests = runnable(step)
            card = StepCard(step, bool(tests) and all(self.ticks[(step["n"], t["key"])]
                                                      for t in tests), step["n"] == self.chosen)
            card.opened.connect(self.open_step)
            card.ticked.connect(lambda n, on: self.tick(
                [(n, t["key"]) for t in runnable(self.step(n))], on))
            card.ran.connect(lambda n: self.run([k for k, on in self.ticks.items()
                                                 if on and k[0] == n]))
            self.grid.addWidget(card, i // PER_ROW, i % PER_ROW)
        for col in range(PER_ROW):
            self.grid.setColumnStretch(col, 1)
        count = {w: sum(s["state"] == k for s in steps) for k, (w, _) in STATE.items()}
        self.summary.setText("   ".join(f"{num(v)} {k}" for k, v in count.items() if v))
        self.marked.setText(f"▶ correr marcados ({num(sum(self.ticks.values()))})")
        offer = data["backfill"]
        self.backfill.setVisible(offer["offer"])
        self.backfill.setToolTip(label(offer["why"]))
        self.lines[0].setText(label(data["oos2"]["text"]))
        blind = data["blind"]
        self.lines[1].setText(("SELLADO — " if blind["sealed"] else "") + label(blind["text"]))
        self.lines[1].setStyleSheet(f"color: {C['weak'] if blind['sealed'] else C['promising']};")
        # A disabled button's tooltip never shows, so a blocked step's reason is a visible line.
        self.lines[2].setText("   ".join(f"paso {s['n']} bloqueado: {s['why']}"
                                         for s in steps if s["state"] == "blocked"))
        self.lines[2].setStyleSheet(f"color: {C['dead']};")
        if self.chosen:
            self.drawer.show_step(self.step(self.chosen), self.ticks, blind["sealed"])
        self.drawer.setVisible(bool(self.chosen))

    def step(self, n: str) -> dict:
        """One step on screen, by number."""
        return next(s for s in self.data["steps"] if s["n"] == n)

    def tick(self, keys: list[tuple[str, str]], on: bool) -> None:
        """Tick or untick tests, then repaint so the step boxes and the count follow."""
        for key in keys:
            self.ticks[key] = on
        self.fill(self.data)

    def open_step(self, n: str) -> None:
        """Show a step's tests in the drawer and its tab in the databank panel."""
        self.chosen = n
        self.fill(self.data)
        step = self.step(n)
        if not step["tab"]:
            return
        zone = self.parentWidget()
        while zone is not None and not hasattr(zone, "show_tab"):
            zone = zone.parentWidget()
        if zone is not None:
            zone.show_tab(step["tab"], step["sub"])
        else:
            self.opened.emit(step["tab"], step["sub"])

    def run(self, keys: list[tuple[str, str]], databank: str = "",
            strategies: list[str] | None = None) -> None:
        """Queue tests through POST /api/workflow/run and say what started and what did not.

        Args:
            keys: (step, study) pairs.
            databank: The panel's databank; '' lets each test find its own.
            strategies: The panel's chosen strategies; None or [] for the population.
        """
        if not keys:
            self.said.setText(label("Nada marcado: marca una prueba o un paso."))
            return
        costly = [f"· {t['title']}: {t['spends']}" for n, k in keys
                  for t in self.step(n)["tests"] if t["key"] == k and t["spends"]]
        if costly and QMessageBox.question(
                self, "Esto gasta oos2 o escribe en el ledger",
                "Cada corrida cuenta y no se deshace:\n" + "\n".join(costly) + "\n\n¿Correr?"
        ) != QMessageBox.Yes:
            self.said.setText("No se lanzó nada.")
            return
        try:
            got = client.post("workflow/run", {
                "project": self.project, "databank": databank, "strategies": strategies or [],
                "tests": [{"n": n, "key": k} for n, k in keys]})
        except httpx.HTTPError as failed:
            got = {"error": f"El demonio no respondió: {failed}"}
        if "error" in got:
            self.said.setText(got["error"])
            return
        refused = "   ".join(f"{r['key']} (paso {r['n']}): {r['why']}" for r in got["refused"])
        self.said.setText(f"{num(len(got['jobs']))} trabajos en cola"
                          + (f"   ·   no se lanzó: {refused}" if refused else ""))
        self.load(self.project)
        self.poll()

    def run_panel(self, tab: str, databank: str = "", strategies: list[str] | None = None) -> None:
        """«Correr los marcados de este panel»: every ticked test of the steps shown in one tab.

        Args:
            tab: The databank panel's top tab.
            databank: The databank the panel shows; '' lets each test find its own.
            strategies: The strategies chosen in the panel; None or [] for all of them.
        """
        in_tab = {s["n"] for s in self.data.get("steps", []) if s["tab"] == tab}
        self.run([k for k, on in self.ticks.items() if on and k[0] in in_tab], databank,
                 strategies)

    def run_all(self) -> None:
        """Every free test with no result yet, whatever is ticked: never one that spends oos2
        or writes the ledger, never a step the rail cannot place (21-25)."""
        self.run([(s["n"], t["key"]) for s in self.data.get("steps", []) for t in runnable(s)
                  if t["auto"] and t["state"] == "pending"])

    def rebuild(self) -> None:
        """Queue `ledger.backfill --blind … --write` for this project."""
        try:
            got = client.post("workflow/backfill", {"project": self.project})
        except httpx.HTTPError as failed:
            got = {"error": f"El demonio no respondió: {failed}"}
        self.said.setText(got.get("error") or "Rehaciendo las filas de 17-19 (ver Trabajos).")
        self.poll()

    def poll(self) -> None:
        """Follow this project's jobs; each one that ended reloads the rail and is announced."""
        try:
            listing = client.get("jobs")["jobs"]
        except httpx.HTTPError:
            return
        mine = {j["id"]: j for j in listing if j.get("project") == self.project}
        ended = [j for i, j in mine.items() if i in self.live and j["rc"] is not None]
        self.live = {i: j for i, j in mine.items() if j["rc"] is None}
        for job in ended:
            self.finished.emit(job["study"], job.get("databank") or "")
        if ended:
            self.load(self.project)
            failed = [j["label"] for j in ended if j["rc"] != 0]
            self.said.setText(f"{num(len(ended))} terminados, {num(len(self.live))} en marcha"
                              + (f"   ·   fallaron: {', '.join(failed)} (ver Trabajos)"
                                 if failed else ""))
        if self.live and self.isVisible():
            self.timer.start(POLL_MS)
        else:
            self.timer.stop()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 — Qt's name
        """Resume following the jobs when the rail comes into view."""
        super().showEvent(event)
        if self.project:
            self.poll()

    def hideEvent(self, event: QHideEvent) -> None:  # noqa: N802 — Qt's name
        """Stop polling while nobody sees the rail."""
        super().hideEvent(event)
        self.timer.stop()

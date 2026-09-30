"""The top strip of a project: the workflow rail as map, automation panel and state (22 §4.1)."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ui.desktop import background, client
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import C, T
from ui.desktop.workspace import railrun, railwatch
from ui.desktop.workspace.aggregate import ask
from ui.desktop.workspace.railconfig import Drawer
from ui.desktop.workspace.railgrid import reflow
from ui.desktop.workspace.railrow import StepCard
from ui.desktop.workspace.railwords import STATE, runnable, small
from ui.text.brief import full, line


class Rail(QFrame):
    """The whole rail for one project, served by GET /api/workflow and, for each SQX step's
    ▶ SQX, GET /api/launch/steps. A card click opens its tab through the workspace's
    `show_tab(tab, sub)` (else `opened(tab, sub)`) and shows the step's tests in the drawer.
    The run buttons live in `railrun`. While visible and while a job of this project runs it
    polls /api/jobs off the GUI thread (`railwatch`); the jobs that ended since the last
    repaint reload the rail and emit ONE `finished(study, databank)`."""

    opened = Signal(str, str)
    finished = Signal(str, str)
    loaded = Signal(str)          # a project's rail was painted from the daemon's answer

    def __init__(self) -> None:
        """Build the header, the grid and the drawer; `load` fills them."""
        super().__init__()
        self.setObjectName("term")
        self.project, self.data, self.chosen = "", {}, ""
        self.sqx: dict[str, dict] = {}      # GET /api/launch/steps: each SQX step's ▶ SQX
        self.ticks: dict[tuple[str, str], bool] = {}
        self.live: dict[str, dict] = {}
        self.ended: list[dict] = []           # jobs that ended since the last repaint
        self.painted = 0.0                    # time.monotonic() of that repaint
        self.cards, self.per_row = [], 0      # the step cards, laid by `reflow`
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
        everything = QPushButton("▶ todas las pruebas Python pendientes")
        everything.setToolTip(label("Toda prueba de Python sin resultado, a la vez, salvo las "
                                    "que leen oos2 o escriben en el ledger y los pasos 21-25; "
                                    "no toca SQX."))
        everything.clicked.connect(self.run_all)
        head.addWidget(everything)
        # «Correr workflow», on its own row: the one button that runs SQX and Python in order.
        self.chain = QPushButton("▶▶ Correr workflow (hasta la próxima decisión)")
        self.chain.setStyleSheet(f"QPushButton {{ background: {C['accent']}; color: {T['bg']}; "
                                 f"border: 1px solid {C['accent']}; padding: 4px 14px; }} "
                                 f"QPushButton:disabled {{ background: {T['bg']}; "
                                 f"color: {T['faint']}; border: 1px dashed {T['line']}; }}")
        self.chain.clicked.connect(lambda: railrun.chain(self))
        self.plan = small("", "mono")
        self.plan.setWordWrap(True)
        chain_row = QHBoxLayout()
        chain_row.addWidget(self.chain)
        chain_row.addWidget(self.plan, 1)
        self.grid = QGridLayout()
        self.grid.setSpacing(5)
        self.lines = [small("", "mono") for _ in range(4)]
        self.said = self.lines[3]
        self.drawer = Drawer()
        self.drawer.ticked.connect(lambda n, k, on: self.tick([(n, k)], on))
        self.drawer.ran.connect(lambda tests: self.run([(t["n"], t["key"]) for t in tests]))
        self.drawer.launched.connect(lambda n: railrun.sqx_step(self, n))
        self.drawer.tab_ran.connect(self.run_panel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.addLayout(head)
        lay.addLayout(chain_row)
        for line in self.lines:
            line.setWordWrap(True)
            lay.addWidget(line)
        lay.addLayout(self.grid)
        lay.addWidget(self.drawer)
        lay.addStretch(1)       # spare height below, not between the lines
        self.timer = QTimer(self, timeout=self.poll)

    def load(self, project: str) -> None:
        """Ask the daemon for one project's rail, off the GUI thread, and paint it when it
        answers (ui boundary: a failure is shown)."""
        if project != self.project:
            self.project, self.ticks, self.chosen = project, {}, ""

        def both() -> dict:
            """The rail and each SQX step's launch state, on the pool's thread."""
            # 10 s cold, past the client's 20 s beside other first reads (📓 2026-09-29).
            got = client.get("workflow", wait=120, project=project)
            return got if "error" in got else got | {"_launch": ask("launch/steps", project=project)}
        background.run(both, lambda got: self.landed(project, got), key=f"rail:{id(self)}",
                       owner=self)

    def landed(self, project: str, got: dict) -> None:
        """The daemon's answer to `load`: paint it, if the rail still shows that project."""
        if project != self.project:
            return
        if "error" in got:
            return self.said.setText(line(got["error"]))
        launch = got.pop("_launch")
        if launch.get("warnings"):          # a closed window's launcher, seen by its marker
            self.said.setText("⚠ " + line(launch["warnings"]))   # the rest on hover
            self.said.setToolTip(full(launch["warnings"]))
            self.said.setStyleSheet(f"color: {C['dead']};")
        self.sqx = launch.get("steps") or {n: {"ok": False, "reasons": [launch.get("error", "?")]}
                                           for n in (s["n"] for s in got["steps"])}
        self.fill(got)
        self.loaded.emit(project)

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
        self.cards = []
        for i, step in enumerate(steps):
            tests = runnable(step)
            card = StepCard(step, bool(tests) and all(self.ticks[(step["n"], t["key"])]
                                                      for t in tests), step["n"] == self.chosen,
                            self.sqx.get(step["n"]))
            card.opened.connect(self.open_step)
            card.ticked.connect(lambda n, on: self.tick(
                [(n, t["key"]) for t in runnable(self.step(n))], on))
            card.ran.connect(lambda n: railrun.step(self, n))
            card.launched.connect(lambda n: railrun.sqx_step(self, n))
            card.configured.connect(lambda n: railrun.configure(self, n))
            self.cards.append(card)
        self.per_row = reflow(self.grid, self.cards, self.width(), 0)
        count = {w: sum(s["state"] == k for s in steps) for k, (w, _) in STATE.items()}
        self.summary.setText("   ".join(f"{num(v)} {k}" for k, v in count.items() if v))
        self.marked.setText(f"▶ correr marcados ({num(sum(self.ticks.values()))})")
        plan = data.get("chain") or {"do": [], "stop": {"n": None, "why": "sin plan"}}
        self.chain.setEnabled(bool(plan["do"]))
        self.plan.setText(railrun.plan_line(plan))
        self.plan.setStyleSheet(f"color: {C['accent'] if plan['do'] else C['dead']};")
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
        self.lines[2].setVisible(bool(self.lines[2].text()))   # no empty band over the cards
        if self.chosen:
            self.drawer.show_step(self.step(self.chosen), self.ticks, blind["sealed"],
                                  self.sqx.get(self.chosen), data)
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
        """Queue tests (`railrun.tests`): (step, study) pairs, the panel's databank and rows."""
        railrun.tests(self, keys, databank, strategies)

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
        got = railrun.post("workflow/backfill", {"project": self.project})
        self.said.setText(got.get("error") or "Rehaciendo las filas de 17-19 (ver Trabajos).")
        self.poll()

    def poll(self) -> None:
        """Follow this project's jobs (`railwatch`): off the GUI thread, repaints grouped."""
        railwatch.poll(self)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 — Qt's name
        """Resume following the jobs when the rail comes into view."""
        super().showEvent(event)
        if self.project:
            self.poll()

    def hideEvent(self, event: QHideEvent) -> None:  # noqa: N802 — Qt's name
        """Stop polling while nobody sees the rail."""
        super().hideEvent(event)
        self.timer.stop()

    def resizeEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Reflow the cards when the rail's width changes how many fit in a row."""
        super().resizeEvent(event)
        self.per_row = reflow(self.grid, self.cards, self.width(), self.per_row)

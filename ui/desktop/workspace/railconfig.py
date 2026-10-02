"""The rail's drawer: one step's tests, each with its box, state, configuration and run button."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from ui.desktop import background
from ui.text.glossary import knob, label
from ui.desktop.theme import C
from ui.desktop.workspace.railrow import off_reason
from ui.desktop.workspace.railwords import ink, readable, run_button, small, value_words, word
from ui.desktop.workspace.texts import STEP_NOTES

# The ▶ SQX of a step whose own words the owner fixed (2026-09-28); the rest say «lanzar el paso N».
LAUNCH_WORDS = {"6": "Activar el builder"}
DONE = ("done", "sealed")        # a step another one needs counts as run in these states


def knob_lines(got: dict) -> str:
    """Every knob of a study as its next run for this project reads it, one per line.

    Args:
        got: GET /api/config?study&project's answer, or `{error}`.

    Returns:
        The lines — a knob the project fills says so, one the run leaves at the file's value
        although the project differs is marked ⚠ — or the reason they could not be read.
    """
    if "error" in got:
        return got["error"]
    lines = [f"{'⚠ ' if k.get('warn') else ''}{knob(k['key'])} = {value_words(k['value'])}"
             + (f"   ({k['note']})" if k.get("note") else "")
             + (f"   — {k['warn']}" if k.get("warn") else f"   — {k['tip']}" if k["tip"] else "")
             for s in got.get("sections", []) for k in s["knobs"]]
    return "\n".join(lines) or "Sin configuración: este estudio no tiene config.yaml."


def needs_line(step: dict, steps: list[dict]) -> tuple[str, bool]:
    """What must be run before this step, from the daemon's `needs` and each one's state.

    Returns:
        The line, and whether anything it needs is still missing.
    """
    by_n = {s["n"]: s for s in steps}
    need = [by_n[n] for n in step.get("needs", []) if n in by_n]
    if not need:
        return "", False
    missing = [s for s in need if s["state"] not in DONE]
    ready = [s for s in need if s["state"] in DONE]
    text = ("ANTES HAY QUE LANZAR: " + "   ·   ".join(
        f"paso {s['n']} ({label(s['title'])}) — {word(s['state'])}" for s in missing)
        if missing else "")
    text += (("   ·   ya hechos: " if missing else "REQUISITOS HECHOS: ")
             + ", ".join(f"✓ {s['n']} {label(s['title'])}" for s in ready) if ready else "")
    return text, bool(missing)


class Drawer(QFrame):
    """The tests of the step chosen on the rail. `ticked(n, key, on)` follows a box;
    `ran([{n, key}])` asks to run tests now; `tab_ran(tab)` asks for every ticked test of
    the step's tab; `launched(n)` asks to launch an SQX step's tasks; `seen(tab, sub)` asks
    to open the Databanks zone on the step's tab."""

    ticked = Signal(str, str, bool)
    ran = Signal(list)
    tab_ran = Signal(str)
    launched = Signal(str)
    seen = Signal(str, str)

    def __init__(self) -> None:
        """Build the empty drawer; `show_step` fills it."""
        super().__init__()
        self.setObjectName("term")
        self.head = small("", "mono")
        self.why = small("")
        self.why.setWordWrap(True)
        self.tab_button = QPushButton("▶ correr los marcados de «»")
        self.tab_button.clicked.connect(lambda: self.tab_ran.emit(self.step["tab"]))
        top = QHBoxLayout()
        top.addWidget(self.head, 1)
        top.addWidget(self.tab_button)
        self.see = QPushButton("→ ver en Databanks")
        self.see.clicked.connect(lambda: self.seen.emit(self.step["tab"], self.step["sub"]))
        top.addWidget(self.see)
        self.note = QLabel("")
        self.note.setObjectName("dim")
        self.note.setWordWrap(True)
        self.all_row = QHBoxLayout()
        self.all_button = QPushButton("▶ Lanzar todos")
        self.all_button.clicked.connect(lambda: self.ran.emit(self.batch))
        self.all_row.addWidget(self.all_button)
        self.all_row.addStretch(1)
        self.batch: list[dict] = []
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(2)
        self.knobs = QLabel("")
        self.knobs.setObjectName("dim")
        self.knobs.setWordWrap(True)
        self.knobs.hide()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(3)
        lay.addLayout(top)
        lay.addWidget(self.why)
        lay.addWidget(self.note)
        lay.addLayout(self.all_row)
        lay.addLayout(self.grid)
        lay.addWidget(self.knobs)
        self.needs = QLabel("")
        self.needs.setObjectName("mono")
        self.needs.setWordWrap(True)
        lay.addWidget(self.needs)
        self.step, self.project = {}, ""

    def show_step(self, step: dict, ticks: dict[tuple[str, str], bool], sealed: bool,
                  sqx: dict | None = None, data: dict | None = None) -> None:
        """Lay out one step's tests, and for an SQX step its launch row.

        Args:
            step: One step as GET /api/workflow sends it.
            ticks: (step, study) → ticked.
            sealed: Whether the ledger's door is shut: a sealed step's tests show no number
                and no verdict, only that they ran.
            sqx: An SQX step's entry of GET /api/launch/steps, None until it is read.
            data: GET /api/workflow's whole answer: the project and every step's state,
                for the line of what must run first.
        """
        self.step, self.project = step, (data or {}).get("project", "")
        while self.grid.count():
            gone = self.grid.takeAt(0).widget()
            gone.hide()          # hidden first, or it paints under the new ones until deleted
            gone.deleteLater()
        self.knobs.hide()
        self.head.setText(f"PASO {step['n']} · {label(step['title'])} — "
                          f"{word(step['state']).upper()}")
        self.head.setStyleSheet(f"color: {ink(step['state'])};")
        self.why.setText(label(step["why"]) if step["why"] else "")
        self.note.setText(STEP_NOTES.get(step["n"], ""))
        self.note.setVisible(step["n"] in STEP_NOTES)
        text, missing = needs_line(step, (data or {}).get("steps", []))
        self.needs.setText(text)
        self.needs.setStyleSheet(f"color: {C['weak'] if missing else C['promising']};")
        self.needs.setVisible(bool(text))
        playable = step["kind"] != "sqx"
        self.batch = [{"n": step["n"], "key": t["key"]} for t in step["tests"]
                      if playable and t["runnable"] and t["state"] != "running"]
        self.all_button.setText(f"▶ Lanzar todos ({len(self.batch)})")
        self.all_button.setToolTip(label("Corre a la vez todas las pruebas de este paso que se "
                                         "pueden correr aquí; antes pregunta por las que leen "
                                         "oos2 o escriben en el ledger"))
        self.all_button.setVisible(len(self.batch) > 1)
        self.tab_button.setVisible(bool(step["tab"]))
        self.see.setVisible(bool(step["tab"]))
        self.tab_button.setText(f"▶ correr los marcados de «{step['tab']}»")
        if step["kind"] == "sqx":
            self.grid.addWidget(self.launch_row(step, sqx), 0, 0, 1, 5)
        for row, test in enumerate(step["tests"], start=1):
            self.add_test(row, step["n"], test, ticks.get((step["n"], test["key"]), False),
                          sealed and step["n"] in ("17", "18", "19"), playable)

    def launch_row(self, step: dict, sqx: dict | None) -> QWidget:
        """An SQX step's ▶ and its tasks, in a row of their own: the button's «?» then sits
        between the two instead of floating over the sentence (owner, 2026-09-28)."""
        why, fails = off_reason(step, sqx)
        titles = ", ".join((sqx or {}).get("titles") or []) or "—"
        words = LAUNCH_WORDS.get(step["n"], f"lanzar el paso {step['n']}")
        launch = run_button("sqx", f"▶ SQX · {words}", why)
        launch.clicked.connect(lambda: self.launched.emit(step["n"]))
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(8)
        line.addWidget(launch)
        # Red only for a real failure (CLAUDE.md feedback, 2026-09-29): a step done elsewhere
        # is expected, not broken.
        line.addWidget(small(f"✖ {label(why)}" if fails else f"· {label(why)}" if why else
                             f"Tareas, todas juntas en un arranque: {titles}. Su análisis se "
                             "corre en el paso de Python siguiente.", "dim",
                             ink("blocked") if fails else ""), 1)
        return row

    def add_test(self, row: int, n: str, test: dict, on: bool, sealed: bool,
                 playable: bool) -> None:
        """One test's row: box, title, state, configuration, its drawer button and ▶.

        Args:
            row: Grid row.
            n: The step's number.
            test: One entry of the step's `tests`.
            on: Whether it is ticked.
            sealed: Whether its result must not be described.
            playable: False on an SQX step: no ▶, its analysis runs from the panel.
        """
        box = QCheckBox(label(test["title"]).replace("&", "&&"))   # «&» is Qt's mnemonic
        box.setChecked(on)
        box.setEnabled(test["runnable"])
        box.toggled.connect(lambda v, k=test["key"]: self.ticked.emit(n, k, v))
        state = "sealed" if sealed and test["state"] == "done" else test["state"]
        why = ("hecho; el resultado se lee cuando 17, 18 y 19 estén los tres"
               if state == "sealed" else test["why"])
        self.grid.addWidget(box, row, 0)
        word_label = QLabel(word(state))
        word_label.setObjectName("mono")
        word_label.setStyleSheet(f"color: {ink(state)};")
        word_label.setMinimumWidth(90)
        self.grid.addWidget(word_label, row, 1)
        cost = f"⚠ {test['spends'].upper()}   ·   " if test["spends"] else ""   # first: never cut
        line = small(f"{cost}{readable(test['config'])}   ·   {label(why)}")
        line.setWordWrap(True)
        self.grid.addWidget(line, row, 2)
        show = QPushButton("configuración")
        show.clicked.connect(lambda _=False, k=test["key"], t=test["title"]: self.reveal(k, t))
        self.grid.addWidget(show, row, 3)
        self.grid.setColumnStretch(2, 1)
        if not playable:
            return
        run = QPushButton("▶")
        run.setFixedWidth(26)
        run.setEnabled(test["runnable"] and test["state"] != "running")
        run.setToolTip(label(f"Correr solo «{test['title']}»"))
        run.clicked.connect(lambda _=False, k=test["key"]: self.ran.emit([{"n": n, "key": k}]))
        self.grid.addWidget(run, row, 4)

    def reveal(self, key: str, title: str) -> None:
        """Show every knob of one study under the tests as this project's run will read them
        (asked off the GUI thread), or hide them on a second press of the same study."""
        head = f"{label(title)} — configuración para {self.project or 'el proyecto'}"
        if self.knobs.isVisible() and self.knobs.text().startswith(head):
            self.knobs.hide()
            return
        self.knobs.setText(f"{head}\nleyendo…")
        self.knobs.show()
        background.get("config", lambda got: self.knobs.setText(f"{head}\n{knob_lines(got)}"),
                       key=f"knobs:{id(self)}", owner=self, study=key, project=self.project)

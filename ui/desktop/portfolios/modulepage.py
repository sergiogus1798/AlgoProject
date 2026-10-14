"""One rail module of PORTFOLIOS: its settings strip with «Calcular», and below it the result's tabs."""

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QTabWidget,
                               QVBoxLayout, QWidget)

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.blocks.tabpage import TabPage
from ui.desktop.portfolios import strips
from ui.desktop.portfolios.calc import CalcButton
from ui.desktop.portfolios.matrix import Matrix, PairDialog
from ui.desktop.theme import T

if TYPE_CHECKING:
    from ui.desktop.portfolios.board import PortfoliosBoard

NOTHING = "Todavía no hay nada que enseñar"
MANY = 1
ONE_ROW = 3     # selectors that fit beside the launchers; more, and the typed ones get a row of their own


def scrolled(inner: QWidget) -> QScrollArea:
    """A tab's content, scrolling when it is taller than the module."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setWidget(inner)
    return area


class ModulePage(QWidget):
    """`board` gives the selection (`board.selection`), the test overrides (`board.overrides()`)
    and is told when a job ended (`board.computed()`)."""

    def __init__(self, name: str, board: "PortfoliosBoard") -> None:
        """Build the strip; the result is asked for on `refresh`."""
        super().__init__()
        self.name, self.board, self.spec = name, board, strips.MODULES[name]
        self.asked, self.want_tab, self.followed = None, "", ""
        self.inputs: dict[str, QComboBox | QLineEdit] = {}
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(QLabel(name, objectName="h1"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        lay.addWidget(text(self.spec["intro"], T["muted"], 14))
        strip, typed = QHBoxLayout(), QHBoxLayout()
        long = len(self.spec["selectors"]) > ONE_ROW       # one row squeezed the combos and cut the button
        for key, label, tip, kind in self.spec["selectors"]:
            row = typed if long and kind != "combo" else strip
            head = QLabel(label)
            head.setToolTip(tip)
            row.addWidget(head)
            box: QComboBox | QLineEdit
            if kind == "combo":
                box = QComboBox()
                box.setToolTip(tip)
                box.setMinimumWidth(150)
                box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
                for value, shown in strips.STATIC.get(key, []):
                    box.addItem(shown, value)
                box.currentIndexChanged.connect(lambda _: self.refresh())
            else:
                box = QLineEdit(strips.PREFILLED.get(key, ""))
                box.setToolTip(tip)
                box.setFixedWidth(130)
                box.setPlaceholderText("decisión tuya")
            self.inputs[key] = box
            row.addWidget(box)
        strip.addStretch(1)
        typed.addStretch(1)
        for n, (label, action, tip) in enumerate(self.spec["launchers"]):
            strip.addWidget(CalcButton(label, action, self.params, self.say, self.ended, tip, primary=n == 0))
        lay.addLayout(strip)
        lay.addLayout(typed)
        self.state = text("", T["muted"], 13)
        self.banner = text("", colour("watch"), 15, True)
        self.lacks = text("", colour("watch"), 14)
        for line in (self.state, self.banner, self.lacks):
            line.hide()
            lay.addWidget(line)
        lay.addWidget(QFrame(objectName="rule"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.body = QWidget()
        lay.addWidget(self.body, 1)

    def value(self, key: str) -> str:
        """What one selector holds now, "" when the module has none of that key."""
        box = self.inputs.get(key)
        if box is None:
            return ""
        return (box.currentData() or "") if isinstance(box, QComboBox) else box.text().strip()

    def params(self) -> dict[str, Any]:
        """What a launcher sends: the databank's selection, this strip, and the test overrides."""
        chosen = {k: self.board.selection.get(k, "") for k in ("pool", "run")}
        return chosen | {k: self.value(k) for k in ("plan", "firm", "horizon", "edge_from", "n_paths")} | {
            "sets": self.board.overrides()}

    def say(self, words: str, ink: str) -> None:
        """The launcher's line under the strip."""
        self.state.setText(words)
        self.state.setStyleSheet(f"color:{ink}; font-size:13px;")
        self.state.show()

    def ended(self, job: dict) -> None:
        """A «Calcular» finished: the zone reads what exists again, and this module repaints — the
        bank on its newest table, the one the decision beside it was just taken from."""
        self.asked = None
        table = self.inputs.get("bank")
        if job.get("rc") == 0 and isinstance(table, QComboBox):   # the table just computed is the one shown
            table.blockSignals(True)
            table.clear()
            table.blockSignals(False)
        self.board.computed()

    def query(self) -> dict[str, str]:
        """What this module asks the daemon now: the selection and the strip, blanks dropped."""
        asked = {"name": self.name, **{k: self.board.selection.get(k, "") for k in ("pool", "run", "strategy")},
                 **{k: self.value(k) for k in ("plan", "firm", "freq", "measure", "bank")}}
        return {k: v for k, v in asked.items() if v}

    def refresh(self) -> None:
        """Ask the daemon for this module's tabs, unless the same question is already on screen."""
        run = self.board.run()
        if self.name == "Fondeo" and run.get("plan") and run["id"] != self.followed:
            self.followed = run["id"]       # a funded run chosen below brings its plan to the strip
            box = self.inputs["plan"]
            assert isinstance(box, QComboBox)
            box.blockSignals(True)
            if box.findData(run["plan"]) < 0:
                box.addItem(run["plan"], run["plan"])
            box.setCurrentIndex(box.findData(run["plan"]))
            box.blockSignals(False)
        if self.query() == self.asked:
            return
        self.asked = self.query()
        background.get("portfolios/module", self.paint, f"portfolios:{self.name}", self, **self.asked)

    def feed(self, got: dict) -> None:
        """Fill the strip's combos from the answer, keeping what was chosen."""
        options = {"plan": [(p, p) for p in got.get("plans", [])], "bank": [(b, f"{b[:8]} {b[9:11]}:{b[11:13]}:{b[13:15]} · {b[16:][-44:]}") for b in got.get("banks", [])],
                   "measure": [(m["key"], m["label"]) for m in got.get("measures", [])],
                   "firm": [("", "—")] + [(f, f) for f in self.board.state.get("firms", [])]}
        for key, box in self.inputs.items():
            if not isinstance(box, QComboBox) or key not in options or not options[key]:
                continue
            box.blockSignals(True)
            keep = got.get(key) or box.currentData()
            if [box.itemData(i) for i in range(box.count())] != [v for v, _ in options[key]]:
                box.clear()
                for value, shown in options[key]:
                    box.addItem(shown, value)
            box.setCurrentIndex(max(0, box.findData(keep)))
            box.blockSignals(False)

    def paint(self, got: dict) -> None:
        """Replace the body with the answer's tabs, or with what is missing and how to get it."""
        got = {"tabs": [], "empty": got["error"]} if "error" in got else got
        self.feed(got)
        self.asked = self.query()
        self.banner.setText(got.get("relaxed") or "")
        self.banner.setVisible(bool(got.get("relaxed")))
        lacks, shown = list(got.get("missing") or []), list(got.get("tabs") or [])
        if len(lacks) > MANY and shown:     # a long list would push the result off the screen: it gets a tab
            shown.append({"name": "falta", "title": f"Lo que falta ({len(lacks)})", "note": "", "selectors": [],
                          "blocks": [{"kind": "table", "title": "Decisiones tuyas sin las que «Calcular» se niega",
                                      "columns": ["Falta"], "rows": [[m] for m in lacks], "align": ["left"]}]})
            lacks = [f"Faltan {len(lacks)} decisiones tuyas: sin ellas «Calcular» se niega. Están en la pestaña "
                     f"«Lo que falta ({len(lacks)})»."]
        said = lacks + ([got["spent"]] if got.get("spent") else [])
        self.lacks.setText("<br>".join(said))
        self.lacks.setVisible(bool(said))
        old = self.body
        if not shown and "matrix" not in got:
            self.body = QWidget()
            col = QVBoxLayout(self.body)
            col.setContentsMargins(0, 24, 0, 0)
            col.addWidget(QLabel(NOTHING, objectName="kicker"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
            col.addWidget(text((got.get("empty") or "").replace("\n", "<br>"), T["text"], 18))
            col.addStretch(1)
        else:
            self.body = QTabWidget()
            if "matrix" in got:
                self.body.addTab(scrolled(Matrix(got["matrix"], self.pair)), "Matriz")
            for tab in shown:
                self.body.addTab(scrolled(TabPage([tab], {})), tab["title"])
            titles = [self.body.tabText(i) for i in range(self.body.count())]
            keep = self.want_tab or (old.tabText(old.currentIndex()) if isinstance(old, QTabWidget) else "")
            self.body.setCurrentIndex(next((i for i, t in enumerate(titles) if t.startswith(keep)), 0) if keep else 0)
            if got.get("empty"):
                self.say(got["empty"], colour("watch"))
        lay = self.layout()
        assert lay is not None
        lay.replaceWidget(old, self.body)
        old.hide()
        old.deleteLater()

    def pair(self, i: str, j: str) -> None:
        """A cell of the matrix was clicked: open that pair."""
        PairDialog(self, {"pool": self.board.selection.get("pool", ""), "i": i, "j": j, "firm": self.value("firm"),
                          "freq": self.value("freq") or "monthly"}).show()

"""The generic study page: family tabs, study tabs with their state dots, the result, the drawer, the runs."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QPushButton, QSplitter, QTabBar, QTabWidget,
                               QVBoxLayout)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.result import ResultView
from ui.desktop.blocks.states import colour
from ui.desktop.selection import SELECTION
from ui.desktop.studypage import compare, dots, notes
from ui.desktop.studypage.drawer import Drawer
from ui.desktop.studypage.history import History
from ui.desktop.studypage.net import fetch
from ui.desktop.studypage.runbar import RunBar
from ui.desktop.theme import T


class StudyPage(QFrame):
    """One study of one strategy (`strategy_page`) or of the population, following SELECTION.
    The wiring lives here; what is said comes from `notes`, what is drawn from `ResultView`."""

    def __init__(self, strategy_page: bool) -> None:
        """Build the page and read the catalogue once.

        Args:
            strategy_page: True for one strategy (scope one), False for the population.
        """
        super().__init__()
        self.setObjectName("term")
        self.strategy_page = strategy_page
        self.where = dict(SELECTION.now)
        self.assets: dict[str, str | None] = {}
        self.cells: dict = {}
        self.strategies: list[dict] = []
        got = fetch("catalogue")
        self.catalogue = {e["key"]: e for e in got.get("studies", [])}
        self.key = next(iter(self.catalogue), "")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 8)
        self.crumb = text("", T["text"], 14)
        lay.addWidget(self.crumb)
        if "error" in got:
            lay.addWidget(text(got["error"], colour("fail"), 14, True))
        self.families = QTabBar()
        for f in dict.fromkeys(e["family"] for e in self.catalogue.values()):
            self.families.setTabData(self.families.addTab(notes.FAMILY.get(f, f)), f)
        self.studies = QTabBar()
        self.studies.setIconSize(QSize(dots.SIZE, dots.SIZE))
        self.studies.setExpanding(False)
        lay.addWidget(self.families)
        lay.addWidget(self.studies)
        self.head = text("", T["text"], 13)
        lay.addWidget(self.head)
        self.drawer = Drawer()
        self.bar = RunBar(self.drawer.overrides)
        self.bar.finished.connect(self.after_run)
        lay.addWidget(self.bar)
        row = QHBoxLayout()
        self.note = text("", T["muted"], 14)
        row.addWidget(self.note, 1)
        self.back = QPushButton("volver a una sola corrida")
        self.back.clicked.connect(lambda: self.load())
        row.addWidget(self.back, 0, Qt.AlignTop)
        lay.addLayout(row)
        self.skipped = text("", T["text"], 13)
        lay.addWidget(self.skipped)
        self.view = ResultView()
        self.history = History()
        self.history.picked.connect(lambda day: self.load(day))
        self.history.compare_runs.connect(self.compare_days)
        self.history.versus.connect(self.versus)
        side = QTabWidget()
        side.setDocumentMode(True)
        side.addTab(self.drawer, "configuración")
        side.addTab(self.history, "historial y comparar")
        split = QSplitter()
        split.addWidget(self.view)
        split.addWidget(side)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        split.setSizes([900, 380])
        lay.addWidget(split, 1)
        self.families.currentChanged.connect(self._family)
        self.studies.currentChanged.connect(self._study)
        SELECTION.changed.connect(self.follow)
        self.follow(dict(SELECTION.now))

    def follow(self, now: dict) -> None:
        """Take a new selection: re-read the dots and the study on screen.

        Args:
            now: SELECTION's fields.
        """
        self.where = dict(now)
        if self.where["project"] and not self.where["asset"]:
            self.where["asset"] = self._asset(self.where["project"])
        if not self.strategy_page:
            self.where["strategy"] = self.where["identity"] = ""
        self.crumb.setText(notes.context(self.where, self.strategy_page))
        self._states()
        self.open_study(self.key)

    def _asset(self, project: str) -> str | None:
        """The project's asset, as `/api/projects` reads it off the name, asked once."""
        if project not in self.assets:
            got = fetch("projects").get("projects") or []
            self.assets.update({p["project"]: p["asset"] for p in got})
        return self.assets.get(project)

    def _states(self) -> None:
        """Every study's stored state here, for the dots."""
        w = self.where
        self.cells, self.strategies = {}, []
        if not (w["project"] and w["databank"]):
            return
        if self.strategy_page:
            self.cells, self.strategies = dots.of_strategy(w["project"], w["databank"],
                                                           w["identity"])
        else:
            self.cells = dots.of_population(w["project"], w["databank"], list(self.catalogue))

    def open_study(self, key: str) -> None:
        """Show one study: its family's tab, its own tab, its result.

        Args:
            key: Study key, as the catalogue and the matrix name it.
        """
        self.key = key
        family = self.catalogue[key]["family"]
        index = next(i for i in range(self.families.count())
                     if self.families.tabData(i) == family)
        if index == self.families.currentIndex():
            self._family(index)
        else:
            self.families.setCurrentIndex(index)

    def _family(self, index: int) -> None:
        """Fill the study tabs of one family, each with its dot, and open the right one."""
        family = self.families.tabData(index)
        keys = [k for k, e in self.catalogue.items() if e["family"] == family]
        if self.key not in keys:
            self.key = keys[0]
        self.studies.blockSignals(True)
        while self.studies.count():
            self.studies.removeTab(0)
        for k in keys:
            i = self.studies.addTab(dots.dot(self.cells.get(k)), self.catalogue[k]["title"])
            self.studies.setTabData(i, k)
            self.studies.setTabToolTip(i, dots.says(self.cells.get(k)))
        self.studies.setCurrentIndex(keys.index(self.key))
        self.studies.blockSignals(False)
        self.load()

    def _study(self, index: int) -> None:
        """A study tab was clicked; `index` is its position."""
        self.key = self.studies.tabData(index)
        self.load()

    def load(self, day: str = "") -> None:
        """Show the stored result of the study on screen, and point drawer, bar and history at it.

        Args:
            day: A run's day, "" for the newest.
        """
        entry, w = self.catalogue[self.key], self.where
        self.head.setText(notes.headline(entry))
        self.drawer.load(self.key, entry["title"])
        self.bar.aim(entry, w, self.strategy_page)
        self.back.hide()
        self.skipped.hide()
        if not (w["project"] and w["databank"]):
            return self._empty("Elige un proyecto y un databank.")
        if self.strategy_page and not w["strategy"]:
            return self._empty("Elige una estrategia en el panel de databanks de Proyecto.")
        query = compare.query(w, self.key)
        got = fetch("result", **query, day=day)
        self.history.fill(fetch("history", **query),
                          [s for s in self.strategies if s["identity"] != w["identity"]]
                          if self.strategy_page else None)
        if "error" in got:
            return self._empty(got["error"], colour("fail"))
        self.meta = got["meta"]
        self.view.show_result(got["result"], self.meta)
        self.drawer.set_shown(self.meta["config_hash"])
        self.history.mark(self.meta["day"])
        self.skipped.setText(notes.skipped(self.meta["skipped"]))
        self.skipped.setVisible(bool(self.meta["skipped"]))
        if got["result"] is None:
            self.note.setText(notes.absent(entry, self.strategy_page))
        else:
            self.note.setText(notes.shown(self.meta["day"], bool(day), self.strategy_page))

    def _empty(self, sentence: str, ink: str = T["muted"]) -> None:
        """No result to show, and why."""
        self.meta = {"path": None}
        self.note.setText(f'<span style="color:{ink}">{sentence}</span>')
        self.history.fill({}, None)
        self.view.show_result(None, None)
        self.drawer.set_shown(None)

    def compare_days(self, left: str, right: str) -> None:
        """Two runs of the study on screen, side by side.

        Args:
            left, right: Their days.
        """
        self._compare(*compare.runs(self.where, self.key, left, right))

    def versus(self, strategy: str, identity: str) -> None:
        """This strategy beside another of the databank, same study.

        Args:
            strategy, identity: The other strategy.
        """
        self._compare(*compare.strategies(self.where, self.key, strategy, identity))

    def _compare(self, results: list[dict | None], titles: tuple[str, str]) -> None:
        """Draw two results compared, or say which side has none."""
        missing = [t for r, t in zip(results, titles) if r is None]
        if missing:
            self.note.setText(f'<span style="color:{colour("fail")}">No se puede comparar: '
                              f"{', '.join(missing)} no tiene resultado de este estudio "
                              "aquí.</span>")
            return
        self.view.compare(results[0], results[1], titles)
        self.note.setText(f"Comparando {titles[0]} (izquierda) con {titles[1]} (derecha).")
        self.back.show()

    def after_run(self) -> None:
        """A run of this page ended: re-read the dots and the newest result."""
        self._states()
        self.open_study(self.key)

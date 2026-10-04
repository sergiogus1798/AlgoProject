"""The «Estrategia» dropdown of the study page: another strategy of the databank, same study."""

from PySide6.QtCore import QStringListModel, Qt, Signal
from PySide6.QtWidgets import QCompleter, QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from ui.desktop import background
from ui.desktop.selection import SELECTION

TIP = ("Cambia de estrategia sin volver a Databanks: la página se repinta con el mismo estudio. "
       "Escribe para filtrar por cualquier parte del nombre. Lista las estrategias del mismo "
       "proyecto y databank.")


class StrategyPicker(QWidget):
    """Label, editable combo with type-to-filter, and ◀ ▶. Names only, read once per databank."""

    picked = Signal(str, str)         # strategy, identity

    def __init__(self, visible: bool = True) -> None:
        """Build it empty; a choice goes to SELECTION, like Databanks' and Ctrl+K's.

        Args:
            visible: False on the population page, which has no single strategy.
        """
        super().__init__()
        self.setVisible(visible)
        self.picked.connect(lambda n, i: SELECTION.choose(strategy=n, identity=i))
        self.rows: list[dict] = []
        self.bank: tuple | None = None
        self.matrices: dict[str, dict] = {}
        self.named: dict[str, set] = {}      # databank -> {(study, strategy name)}
        self.current = ""
        self.study = ""
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Estrategia")
        self.box = QComboBox()
        self.box.setEditable(True)
        self.box.setInsertPolicy(QComboBox.NoInsert)
        self.box.setMinimumWidth(220)
        self.box.setModel(QStringListModel(self))
        done = QCompleter(self.box.model(), self)
        done.setFilterMode(Qt.MatchContains)
        done.setCaseSensitivity(Qt.CaseInsensitive)
        self.box.setCompleter(done)
        self.prev, self.next = QPushButton("◀"), QPushButton("▶")
        self.prev.setToolTip("Estrategia anterior de la lista.")
        self.next.setToolTip("Estrategia siguiente de la lista.")
        for w in (label, self.box, self.prev, self.next):
            w.setToolTip(w.toolTip() or TIP)
            lay.addWidget(w)
        done.activated[str].connect(self.choose)
        self.box.activated.connect(lambda i: self.choose(self.box.itemText(i)))
        self.prev.clicked.connect(lambda: self.step(-1))
        self.next.clicked.connect(lambda: self.step(1))

    def aim(self, project: str, databank: str, strategy: str, study: str) -> None:
        """Show `strategy` as the current one, listing the strategies with a result of `study`
        in ANY databank of the project (a study's results live in the databank it ran on: WFM,
        MCR_All…), or all of the page's databank when `study` is "". The matrices are read off
        the GUI thread once per project and databank.

        Args:
            project, databank: Where the page is.
            strategy: The strategy on screen.
            study: The study on screen; "" (the Ficha) lists every strategy.
        """
        if not (project and databank):
            return
        self.study, self.current = study, strategy
        if self.bank != (project, databank):
            self.bank, self.matrices, self.named = (project, databank), {}, {}
            background.get("projects", lambda got: self.read(got, project, databank),
                           key="studypicker:projects", owner=self)
        self.refill()

    def read(self, got: dict, project: str, databank: str) -> None:
        """Ask for the matrix of every databank of the project."""
        banks = next((p["databanks"] for p in got.get("projects") or []
                      if p["project"] == project), {databank: 1})
        for d in banks:
            background.get("matrix", lambda m, d=d: self.take(project, databank, d, m),
                           key=f"studypicker:{d}", owner=self, project=project, databank=d)

    def take(self, project: str, databank: str, bank: str, got: dict) -> None:
        """One databank's matrix landed (ignored when the page has moved on)."""
        if self.bank == (project, databank):
            cells = got.get("cells") or {}
            name = {r["identity"]: r["strategy"] for r in got.get("strategies") or []}
            self.matrices[bank] = got
            self.named[bank] = {(k, x) for i, c in cells.items() if i in name for k in c
                                for x in (name[i], i)}      # by name or by identity: a databank
            # may drop the «Strategy » prefix (MCR_All) or re-sign the XML (WFM)
            self.refill()

    def refill(self) -> None:
        """List by name the strategies with a result of the study anywhere in the project; the
        identity is the page databank's own, so the choice lands on a strategy it holds."""
        here = self.matrices.get(self.bank[1]) or {}
        # ponytail: the matrix does not know the batch studies (cloud, WFC, CSCV, Market
        # Surfaces): for them every strategy of the page's databank is listed. Filter by
        # `databank/table`'s states if a 10,000-row page ever opens one of those.
        known = any(k == self.study for n in self.named.values() for k, _ in n)
        self.rows = [r for r in here.get("strategies") or []
                     if not self.study or not known or any(
                         (self.study, x) in n for n in self.named.values()
                         for x in (r["strategy"], r["identity"]))]
        self.box.model().setStringList([r["strategy"] for r in self.rows])
        self.show_current(self.current)

    def show_current(self, strategy: str) -> None:
        """Select `strategy` without announcing it."""
        names = self.box.model().stringList()
        self.box.setCurrentIndex(names.index(strategy) if strategy in names else -1)
        if strategy not in names:
            self.box.setEditText(strategy or "")

    def choose(self, name: str) -> None:
        """A name was picked: announce it when it is another strategy of the list."""
        row = next((r for r in self.rows if r["strategy"] == name), None)
        if row:
            self.picked.emit(row["strategy"], row["identity"])

    def step(self, by: int) -> None:
        """Move to the neighbour in the list (wraps)."""
        if self.rows:
            self.box.setCurrentIndex((self.box.currentIndex() + by) % len(self.rows))
            self.choose(self.box.currentText())

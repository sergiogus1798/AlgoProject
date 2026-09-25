"""The strategies zone: the databanks as SQX groups them, one's strategies, one strategy's results."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QSplitter, QVBoxLayout)

from ui.desktop import client
from ui.desktop.resultspanel import ResultsPanel, kicker
from ui.desktop.strategytable import StrategyTable
from ui.desktop.theme import C


class Studies(QFrame):
    """Three columns: databanks, the strategies of one, everything known about one."""

    def __init__(self) -> None:
        """Build the columns and wire one selection into the next."""
        super().__init__(objectName="term")
        self.data: dict = {"databanks": [], "modules": [], "assets": []}
        self.current: dict | None = None
        self.strategy: str | None = None
        self.seen: set[str] = set()   # job ids already shown as finished
        # Jobs are the daemon's; the view asks how they stand every two seconds while any
        # of its own is running, and redraws the strategy when one ends.
        self.poll = QTimer(self)
        self.poll.setInterval(2000)
        self.poll.timeout.connect(self.check_jobs)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        head = QHBoxLayout()
        head.addWidget(QLabel("Estrategias", objectName="h1"))
        self.counts = QLabel("", objectName="dim")
        head.addWidget(self.counts)
        head.addStretch()
        lay.addLayout(head)

        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.left())
        split.addWidget(self.middle())
        self.results = ResultsPanel()
        self.results.run.connect(self.start_run)
        split.addWidget(self.results)
        split.setSizes([260, 640, 460])
        lay.addWidget(split, 1)

    def left(self) -> QFrame:
        """The databank column, one heading per project.

        Returns:
            The framed column.
        """
        f = QFrame()
        lay = QVBoxLayout(f)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(4)
        lay.addWidget(kicker("proyecto"))
        self.project = QComboBox()
        self.project.setToolTip("Un proyecto de SQX del que hay algún databank exportado. "
                                "La lista de abajo es solo la suya.")
        self.project.currentTextChanged.connect(self.fill_banks)
        lay.addWidget(self.project)
        lay.addWidget(kicker("activo"))
        self.asset = QComboBox()
        self.asset.setToolTip("El activo que opera el proyecto, leído de su nombre. Si el "
                              "nombre no lo dice, elígelo: los módulos lo necesitan para el "
                              "feed y los costes.")
        self.asset.currentTextChanged.connect(lambda *_: self.open_strategy(self.strategy)
                                              if self.strategy else None)
        lay.addWidget(self.asset)
        lay.addWidget(kicker("databanks exportados"))
        self.banks = QListWidget()
        self.banks.currentItemChanged.connect(self.open_bank)
        lay.addWidget(self.banks, 1)
        return f

    def middle(self) -> QFrame:
        """The strategy column: the search box over the table.

        Returns:
            The framed column.
        """
        f = QFrame()
        lay = QVBoxLayout(f)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(4)
        row = QHBoxLayout()
        self.title = kicker("estrategias")
        row.addWidget(self.title)
        row.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("filtrar por nombre")
        self.search.setFixedWidth(220)
        row.addWidget(self.search)
        lay.addLayout(row)
        self.table = StrategyTable()
        self.table.picked.connect(self.open_strategy)
        self.search.textChanged.connect(self.table.filter)
        lay.addWidget(self.table, 1)
        return f

    def reload(self) -> None:
        """Ask the daemon for the databanks again and redraw the left column."""
        self.data = client.get("databanks")
        keep = self.project.currentText()
        projects = sorted({d["project"] for d in self.data["databanks"]})
        self.project.blockSignals(True)
        self.project.clear()
        self.project.addItems(projects)
        self.project.setCurrentText(keep if keep in projects else projects[0])
        self.project.blockSignals(False)
        self.asset.blockSignals(True)
        self.asset.clear()
        self.asset.addItems(self.data["assets"])
        self.asset.blockSignals(False)
        self.counts.setText(f"{len(self.data['databanks'])} databanks en {len(projects)}"
                            f" proyectos · {len(self.data['modules'])} módulos leídos")
        self.counts.setStyleSheet(f"color:{C['faint']};")
        self.fill_banks(self.project.currentText())

    def fill_banks(self, project: str) -> None:
        """Show the chosen project's databanks and its asset.

        Args:
            project: The one picked in the combo.
        """
        mine = [d for d in self.data["databanks"] if d["project"] == project]
        guess = mine[0]["asset"] or ""
        self.asset.blockSignals(True)
        self.asset.setCurrentText(guess)
        self.asset.blockSignals(False)
        self.banks.blockSignals(True)
        self.banks.clear()
        for d in mine:
            tag = " · cosecha" if d["source"] == "harvest" else ""
            item = QListWidgetItem(f"  {d['databank']}{tag}  {d['rows']}")
            item.setData(Qt.UserRole, d)
            item.setToolTip(f"{d['rows']} estrategias · exportado {d['date'] or 'sin fecha'}"
                            + ("" if d["signed"] else "\nSIN manifest: nadie firmó este export"))
            if not d["signed"]:
                item.setForeground(Qt.GlobalColor.darkYellow)
            self.banks.addItem(item)
        self.banks.blockSignals(False)
        self.banks.setCurrentRow(0)
        self.open_bank()

    def open_bank(self) -> None:
        """Load the selected databank's strategies into the table."""
        item = self.banks.currentItem()
        if not item or not item.data(Qt.UserRole):
            return
        self.current = item.data(Qt.UserRole)
        d = self.current
        got = client.get("databank", project=d["project"], databank=d["databank"],
                         source=d["source"])
        self.title.setText(f"{d['project']} / {d['databank']}".upper())
        self.table.fill(got["columns"], got["rows"])
        self.strategy = None
        self.results.show_empty("Elige una estrategia en la tabla.")

    def open_strategy(self, name: str) -> None:
        """Draw everything the data root knows about one strategy.

        Args:
            name: The strategy's name as the table shows it.
        """
        d = self.current
        self.strategy = name
        if not self.asset.currentText():
            self.results.show_empty("Este proyecto no dice qué activo opera: elígelo arriba.")
            return
        got = client.get("results", project=d["project"], databank=d["databank"], strategy=name,
                         asset=self.asset.currentText())
        self.results.show(name, got, self.running())

    def running(self) -> list[dict]:
        """The daemon's jobs, unfinished ones and those not yet shown as ended.

        Returns:
            Job records for the strategy on screen.
        """
        return [j for j in client.get("jobs")["jobs"]
                if j["strategy"] == self.strategy and j["project"] == self.current["project"]
                and (j["rc"] is None or j["id"] not in self.seen)]

    def start_run(self, module: str) -> None:
        """Press of a run button: start the module on the strategy on screen.

        Args:
            module: The module's key.
        """
        d = self.current
        client.post("run", {"module": module, "project": d["project"], "databank": d["databank"],
                            "strategy": self.strategy, "asset": self.asset.currentText()})
        self.poll.start()
        self.open_strategy(self.strategy)

    def check_jobs(self) -> None:
        """Redraw the strategy when one of its jobs ends; stop asking when none runs."""
        jobs = self.running()
        ended = [j["id"] for j in jobs if j["rc"] is not None]
        if ended:
            self.open_strategy(self.strategy)
            self.seen.update(ended)
        if not any(j["rc"] is None for j in jobs):
            self.poll.stop()

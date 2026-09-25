"""The IS/OOS gate zone: the cosechas, one gate's funnel and scorecard, one strategy in full."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSplitter, QVBoxLayout)

from ui.desktop import client
from ui.desktop.funnel import Funnel
from ui.desktop.gatedetail import GateDetail
from ui.desktop.resultspanel import kicker, rule
from ui.desktop.scorecard import Scorecard
from ui.desktop.theme import C, chip


class Gate(QFrame):
    """Step 8 of the workflow on screen: what the gate did to a population, and why."""

    def __init__(self) -> None:
        """Build the header, the three columns and the job poll."""
        super().__init__(objectName="term")
        self.data: dict = {"harvests": [], "screens": []}
        self.report: dict | None = None
        self.seen: set[str] = set()
        self.poll = QTimer(self)
        self.poll.setInterval(2000)
        self.poll.timeout.connect(self.check_jobs)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        # The columns are built before the action row: the survivors switch drives the
        # scorecard, which must exist to be connected.
        split = QSplitter(Qt.Horizontal)
        split.addWidget(self.left())
        split.addWidget(self.middle())
        self.detail = GateDetail()
        split.addWidget(self.detail)
        split.setSizes([460, 520, 420])
        lay.addLayout(self.header())
        lay.addLayout(self.actions())
        lay.addWidget(rule())
        lay.addWidget(split, 1)

    def header(self) -> QHBoxLayout:
        """The title, the cosecha picker and the counts line.

        Returns:
            The row.
        """
        row = QHBoxLayout()
        row.addWidget(QLabel("Puerta IS/OOS", objectName="h1"))
        row.addSpacing(12)
        row.addWidget(kicker("cosecha"))
        self.harvest = QComboBox()
        self.harvest.setMinimumWidth(360)
        self.harvest.setToolTip("Una cosecha une el databank de build y el de retest por "
                                "identidad. La puerta juzga una cosecha, nunca un databank.")
        self.harvest.currentIndexChanged.connect(self.open_harvest)
        row.addWidget(self.harvest)
        self.counts = QLabel("", objectName="dim")
        row.addWidget(self.counts, 1)
        return row

    def actions(self) -> QHBoxLayout:
        """The run button, the overrides box and the survivors switch.

        Returns:
            The row.
        """
        row = QHBoxLayout()
        row.addWidget(kicker("activo"))
        self.asset = QComboBox()
        self.asset.setToolTip("El mono se cobra los costes del propio retest; el activo solo "
                              "dice qué feed leen las barras.")
        row.addWidget(self.asset)
        row.addWidget(kicker("umbrales"))
        self.overrides = QLineEdit()
        self.overrides.setPlaceholderText("criba.umbral=valor, separados por espacios · "
                                          "vacío = los de studies/screening/gate/config.yaml")
        self.overrides.setToolTip("Los umbrales se congelan antes de mirar (ledger/thresholds"
                                  ".yaml). Un override queda escrito en el manifest del informe.")
        row.addWidget(self.overrides, 1)
        self.run = QPushButton("correr la puerta")
        self.run.clicked.connect(self.start_run)
        row.addWidget(self.run)
        self.state = QLabel("", objectName="mono")
        row.addWidget(self.state)
        self.survivors = QCheckBox("solo supervivientes")
        self.survivors.toggled.connect(self.scorecard.only)
        row.addWidget(self.survivors)
        return row

    def left(self) -> QFrame:
        """The funnel and the screens under it.

        Returns:
            The framed column.
        """
        f = QFrame()
        lay = QVBoxLayout(f)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(4)
        lay.addWidget(kicker("embudo · entran → pasan"))
        self.funnel = Funnel()
        lay.addWidget(self.funnel)
        lay.addWidget(rule())
        lay.addWidget(kicker("las cribas, en orden · pasa el ratón para el porqué"))
        self.screens = QLabel("", objectName="dim")
        self.screens.setWordWrap(True)
        lay.addWidget(self.screens)
        lay.addStretch()
        return f

    def middle(self) -> QFrame:
        """The scorecard.

        Returns:
            The framed column.
        """
        f = QFrame()
        lay = QVBoxLayout(f)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(4)
        lay.addWidget(kicker("scorecard · una fila por estrategia, una columna por criba"))
        self.scorecard = Scorecard()
        self.scorecard.picked.connect(self.open_strategy)
        lay.addWidget(self.scorecard, 1)
        return f

    def reload(self) -> None:
        """Ask the daemon for the cosechas again."""
        self.data = client.get("gate/harvests")
        assets = client.get("databanks")["assets"]
        self.asset.blockSignals(True)
        self.asset.clear()
        self.asset.addItems(assets)
        self.asset.blockSignals(False)
        keep = self.harvest.currentIndex()
        self.harvest.blockSignals(True)
        self.harvest.clear()
        for h in self.data["harvests"]:
            judged = (f"puerta del {h['report_day']}: {h['gate']['entered']} → "
                      f"{h['gate']['survives']}") if h["gate"] else "sin puerta todavía"
            self.harvest.addItem(f"{h['project']} / {h['databank']} · {h['day']} · {judged}")
        self.harvest.setCurrentIndex(max(keep, 0))
        self.harvest.blockSignals(False)
        self.open_harvest()

    def current(self) -> dict | None:
        """The cosecha picked in the combo.

        Returns:
            Its record, or None with nothing to pick.
        """
        i = self.harvest.currentIndex()
        return self.data["harvests"][i] if i >= 0 else None

    def open_harvest(self) -> None:
        """Draw the picked cosecha's gate, or say it has not been run."""
        h = self.current()
        if not h:
            return
        if h["asset"]:
            self.asset.setCurrentText(h["asset"])
        c = h["counts"]
        self.counts.setText(f"build {c['build']} · retest {c['oos']} ({h['oos_databank']}) · "
                            f"emparejadas {c['matched']} · sin retest {c['missing_oos']} · "
                            f"{c['trades']:,} operaciones")
        self.counts.setStyleSheet(f"color:{C['faint']};")
        self.detail.show_empty("Elige una estrategia en el scorecard.")
        if not h["gate"]:
            self.report = None
            self.funnel.fill([], [])
            self.scorecard.setRowCount(0)
            self.screens.setText("Esta cosecha no ha pasado por la puerta. Pulsa «correr la "
                                 "puerta»: sobre cientos de estrategias tarda segundos, sin SQX.")
            return
        self.report = client.get("gate/report", project=h["project"], databank=h["databank"],
                                 day=h["report_day"])
        self.funnel.fill(self.report["funnel"], self.report["screens"])
        self.scorecard.fill(self.report["rows"], self.report["screens"])
        self.scorecard.only(self.survivors.isChecked())
        src = self.report["source"]
        self.screens.setText(
            f"ventana OOS {src['split']} → {src['end']} · informe del {self.report['date']}"
            + (f" · overrides {src['overrides']}" if src["overrides"] else "") + "\n"
            + "\n".join(f"{s['name']} ({s['kind']}): "
                        + (", ".join(f"{k}={v}" for k, v in s["thresholds"].items()) or "—")
                        for s in self.report["screens"]))

    def open_strategy(self, identity: str) -> None:
        """Draw one strategy of the open report.

        Args:
            identity: The scorecard row's identity.
        """
        h = self.current()
        row = next(r for r in self.report["rows"] if r["identity"] == identity)
        got = client.get("gate/strategy", project=h["project"], databank=h["databank"],
                         day=h["day"], identity=identity)
        self.detail.show(row, self.report["screens"], got)

    def start_run(self) -> None:
        """Run the gate over the picked cosecha, with the overrides typed."""
        h = self.current()
        client.post("gate/run", {"project": h["project"], "databank": h["databank"],
                                 "asset": self.asset.currentText(),
                                 "overrides": self.overrides.text().split()})
        self.state.setText(chip("en curso", C["weak"]))
        self.poll.start()

    def check_jobs(self) -> None:
        """When the gate job ends, reload; say how it ended."""
        jobs = [j for j in client.get("jobs")["jobs"] if j["label"] == "gate"
                and j["id"] not in self.seen]
        done = [j for j in jobs if j["rc"] is not None]
        if not done:
            return
        self.poll.stop()
        job = done[-1]
        self.seen.update(j["id"] for j in done)
        ok = job["rc"] == 0
        self.state.setText(chip("terminó" if ok else f"falló, código {job['rc']}",
                                C["promising"] if ok else C["dead"]))
        self.state.setToolTip("\n".join(job["tail"]))
        self.reload()

"""MT5 BRIDGE › Verificar: one strategy in SQX at each prop firm's conditions against its MT5 backtest."""
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFormLayout, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QSplitter, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.result import ResultView
from ui.desktop.blocks.states import colour
from ui.desktop.jobbutton import JobButton
from ui.desktop.mt5bridge.render import COLUMNS, FirmLight, fill_runs, filtered, header
from ui.desktop.selection import SELECTION
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.studypage.net import send as daemon_send
from ui.desktop.theme import T

INTRO = ("El paso 26: la estrategia se retestea en SQX con las condiciones de cada empresa — su "
         "spread de ahora, su comisión y su swap — y su EA, exportado por SQX, se backtestea en "
         "MT5 en la cuenta de esa empresa. Se comparan las dos listas de operaciones con los "
         "criterios de aceptación que fijaste. La ventana y el modelo del tester se eligen cada "
         "vez: no tienen valor por defecto, porque los datos de algunas empresas son malos.")
PICK = "— elige —"
SELECTED = "La elegida en Proyecto"


class VerifyZone(QFrame):
    """The form on the left, every past check on the right, the chosen check's result below."""

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch,
                 send: Callable[[str, dict], dict] = daemon_send) -> None:
        """Build the frame; the daemon is asked nothing until the zone is first shown.

        Args:
            fetch: GET a daemon route, never raising; injectable for a test.
            send: POST a daemon route, never raising.
        """
        super().__init__()
        self.setObjectName("term")
        self.fetch, self.send, self.loaded = fetch, send, False
        self.runs, self.archive, self.folder, self.result = [], [], [], None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)
        lay.addWidget(QLabel("MT5 BRIDGE", objectName="kicker"))
        lay.addWidget(QLabel("Verificar en SQX y en MT5", objectName="h1"))
        lay.addWidget(text(INTRO, T["muted"], 13))
        lay.addWidget(QFrame(objectName="rule"))

        form = QFormLayout()
        self.source = QComboBox()
        self.source.currentIndexChanged.connect(lambda *_: self._chosen())
        self.chosen = text("", T["muted"], 12)
        self.start = QLineEdit(placeholderText="AAAA-MM-DD o MT5")
        self.start.setToolTip("MT5 = lo más antiguo que tengan a la vez los servidores de las "
                              "empresas marcadas y SQX: se lee al abrir cada cuenta, dentro de "
                              "la verificación. Si ningún servidor lo dice, 4 años antes de Hasta.")
        self.end = QLineEdit(placeholderText="AAAA-MM-DD")
        self.model = QComboBox()
        self.firms = QWidget()
        self.firm_row = QHBoxLayout(self.firms)
        self.firm_row.setContentsMargins(0, 0, 0, 0)
        self.boxes: dict[str, FirmLight] = {}
        form.addRow("Estrategia", self.source)
        form.addRow("", self.chosen)
        form.addRow("Desde", self.start)
        form.addRow("Hasta", self.end)
        form.addRow("Modelo del tester", self.model)
        form.addRow("Empresas", self.firms)
        self.refused = text("", colour("fail"), 12)
        self.button = JobButton("Verificar en SQX y en MT5", "mt5bridge/verify", self.body,
                                self.confirm, lambda _job: self.reload())
        left = QWidget()
        side = QVBoxLayout(left)
        side.setContentsMargins(0, 0, 12, 0)
        side.addLayout(form)
        side.addWidget(self.refused)
        side.addWidget(self.button)
        side.addStretch(1)
        left.setMinimumWidth(380)
        left.setMaximumWidth(520)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        header(self.table)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._picked)
        top = QSplitter(Qt.Horizontal)
        top.addWidget(left)
        top.addWidget(self.table)
        top.setStretchFactor(1, 1)

        self.said = text("", T["muted"], 13)
        self.view = ResultView()
        below = QWidget()
        blay = QVBoxLayout(below)
        blay.setContentsMargins(0, 8, 0, 0)
        blay.addWidget(self.said)
        blay.addWidget(self.view, 1)
        split = QSplitter(Qt.Vertical)
        split.addWidget(top)
        split.addWidget(below)
        split.setStretchFactor(1, 1)
        lay.addWidget(split, 1)
        SELECTION.changed.connect(lambda _now: self._chosen())

    def showEvent(self, event: object) -> None:
        """Read the options and the past checks the first time the zone is shown."""
        super().showEvent(event)
        if not self.loaded:
            self.loaded = True
            self.reload()

    def reload(self) -> None:
        """The form's options and the list of checks, again."""
        got = self.fetch("mt5bridge/options")
        if "error" in got:
            self.refused.setText(got["error"])
            return
        keep = self.source.currentText()
        self.archive = got["archive"]
        self.folder = got.get("folder") or []
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem(SELECTED)
        for row in self.archive:
            self.source.addItem(f"Archivo · {row['strategy'] or row['identity'][:12]} · "
                                f"{row['project']} · {row['version']}")
        for row in self.folder:
            self.source.addItem(f"Banquillo · {row['name']}")
        at = self.source.findText(keep)
        self.source.setCurrentIndex(max(at, 0))
        self.source.blockSignals(False)
        if not self.model.count():
            self.model.addItems([PICK, *got["models"]])
        for firm in got["firms"]:
            if firm["firm"] not in self.boxes:
                box = FirmLight(firm["firm"], firm.get("label") or firm["firm"])
                box.setToolTip(f"su cuenta guardada en el terminal, en {firm['server']}")
                box.stateChanged.connect(lambda *_: self._render())
                self.boxes[firm["firm"]] = box
                self.firm_row.addWidget(box)
        self._chosen()
        self.runs = self.fetch("mt5bridge/runs").get("runs", [])
        self._fill()

    def _where(self) -> dict | None:
        """The `Where` the daemon needs for this pick, or None with nothing chosen."""
        i = self.source.currentIndex()
        if i <= 0:
            now = SELECTION.now
            if not now["identity"]:
                return None
            return {"source": "databank", "identity": now["identity"],
                    "project": now["project"] or "", "databank": now["databank"] or ""}
        if i - 1 < len(self.archive):
            row = self.archive[i - 1]
            return {"source": "archive", "identity": row["identity"], "version": row["version"]}
        row = self.folder[i - 1 - len(self.archive)]
        return {"source": "folder", "identity": row["path"]}

    def _chosen(self) -> None:
        """Say which strategy the form would verify, and fill Desde/Hasta with its defaults."""
        i = self.source.currentIndex()
        if i <= 0:
            now = SELECTION.now
            self.chosen.setText(f"{now['strategy']} · {now['databank']} de {now['project']}"
                                if now["identity"] else
                                "ninguna: elígela en el panel de Databanks, o una del archivo")
        elif i - 1 < len(self.archive):
            row = self.archive[i - 1]
            self.chosen.setText(f"archivada el {row['archived_at']} desde {row['databank']}")
        else:
            row = self.folder[i - 1 - len(self.archive)]
            self.chosen.setText(f"BanquilloEstrategias · {row['path']}")
        where = self._where()
        if where is None:
            return
        got = self.send("mt5bridge/dates", where)
        if got.get("hasta"):
            self.start.setText(got.get("desde", ""))
            self.end.setText(got["hasta"])

    def body(self) -> dict:
        """What the form asks for, as the daemon's `Verify`."""
        where = self._where() or {"source": "databank", "identity": ""}
        model = self.model.currentText()
        return {**where, "start": self.start.text().strip(), "end": self.end.text().strip(),
                "model": "" if model == PICK else model,
                "firms": [f for f, box in self.boxes.items() if box.isChecked()]}

    def confirm(self) -> str | None:
        """The daemon's preflight: its text to confirm, or None with the reasons said."""
        got = self.send("mt5bridge/preflight", self.body())
        reasons = got.get("reasons") or ([got["error"]] if "error" in got else [])
        self.refused.setText("\n".join(f"· {r}" for r in reasons))
        return got.get("text") if got.get("ok") else None

    def _fill(self) -> None:
        """One row per check, newest first."""
        fill_runs(self.table, self.runs)
        if self.runs:
            self.table.selectRow(0)
        else:
            self.said.setText("Todavía no se ha verificado ninguna estrategia.")
            self.view.show_result(None, None)

    def _picked(self) -> None:
        """Load the chosen check's result, its firms' lights turned on, and show it."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        run = self.runs[rows[0].row()]
        got = self.fetch("mt5bridge/result", run=run["run"])
        if "error" in got:
            self.said.setText(got["error"])
            self.result = None
            return self.view.show_result(None, None)
        meta = got["meta"]
        self.said.setText(f"{meta['strategy']} · {meta['from']} → {meta['to']} · "
                          f"modelo «{meta['model']}»"
                          + (f" · falló: {meta['error']}" if meta.get("error") else ""))
        self.result = got["result"]
        for firm, box in self.boxes.items():
            box.blockSignals(True)
            box.setChecked(firm in (run.get("firms") or {}))
            box.blockSignals(False)
        self._render()

    def _render(self) -> None:
        """Draw the loaded result with only the active firms' curves, criteria and columns."""
        active = {f for f, box in self.boxes.items() if box.isChecked()}
        self.view.show_result(filtered(self.result, active) if self.result else None, None)

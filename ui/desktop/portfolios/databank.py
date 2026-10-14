"""The databank at the bottom of PORTFOLIOS: «Estrategias» to tick and «Carteras» to choose — one selection for every module."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
)

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.portfolios import detail
from ui.desktop.theme import T
from ui.text.numbers import num

STRATEGIES = (
    ("✓", "Marca las estrategias que quieres declarar como pool."),
    ("Estrategia", "Su nombre en el databank del que se archivó."),
    ("Activo", "El símbolo."),
    ("Timeframe", "El del proyecto de origen."),
    ("Paso", "El paso del WORKFLOW en que estaba al archivar su versión más nueva."),
    ("Versiones", "Cuántas veces se archivó."),
    ("Última versión", "Cuándo se archivó la más nueva."),
    ("Pools", "Los pools declarados que la llevan."),
    ("MT5", "Las empresas en cuya cuenta de MT5 la validó el paso 26; «—» si ninguna."),
    ("Identidad", "Los ocho primeros caracteres."),
)
PORTFOLIOS = (
    (
        "Tipo",
        "Pool: un conjunto congelado de estrategias. Real / Fondeo: una cartera que salió de buscar "
        "en ese pool.",
    ),
    ("Nombre", "El pool, o la carpeta de la run."),
    ("Pool", "De qué pool sale."),
    ("Plan", "El plan de la empresa de fondeo, si es una cartera de fondeo."),
    ("K", "Cuántas estrategias lleva."),
    ("Puntuación", "Camino real: puntuación por rangos en build, de 0 a 1."),
    ("P(pasar)", "Fondeo: P(pasar) de la etapa A, en build."),
    ("Ajustada", "«AJUSTADO» si se corrió con umbrales relajados: no es un resultado."),
    (
        "Veredicto",
        "Lo que dijo el veredicto, o hasta dónde llegó la run. Entero, al pasar el ratón.",
    ),
)
FROZEN = (
    "Vas a declarar el pool «{name}» con {n} estrategias.\n\nUn pool declarado queda CONGELADO: no se le pueden "
    "añadir ni quitar estrategias después, y su oos2 solo se lee una vez. ¿Declararlo?"
)
KINDS = {"pool": "Pool", "real": "Real", "funded": "Fondeo"}


def table(columns: tuple) -> QTableWidget:
    """A read-only, row-selecting table with a tooltip per header."""
    out = QTableWidget(0, len(columns))
    out.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    out.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    out.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    out.verticalHeader().hide()
    for i, (head, tip) in enumerate(columns):
        item = QTableWidgetItem(head)
        item.setToolTip(tip)
        out.setHorizontalHeaderItem(i, item)
    out.horizontalHeader().setStretchLastSection(True)
    return out


EMPTY = "El archivo está vacío: archiva una estrategia desde su ficha, en Estrategia; aquí se marcan para declarar un pool."


class Databank(QFrame):
    """`chosen(dict)` carries what the modules read: `pool`, `run`, `strategy` ("" when unset).
    `declared()` fires after a pool was written, so the zone lists it."""

    chosen = Signal(dict)
    declared = Signal()

    def __init__(self) -> None:
        """Build the toolbar and the two tables, empty."""
        super().__init__()
        self.strategies, self.rows = [], []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Databank", objectName="kicker"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
        self.said = text("", T["muted"], 13)
        bar.addWidget(self.said, 1)
        for label, tip, slot in (
            (
                "Marcar todas",
                "Marca todas las estrategias de la lista.",
                lambda: self.tick(True),
            ),
            ("Ninguna", "Quita todas las marcas.", lambda: self.tick(False)),
            (
                "Declarar pool con las marcadas…",
                "Congela las estrategias marcadas como un pool con nombre. "
                "De ese pool salen después las parejas, las búsquedas y las carteras.",
                self.declare,
            ),
        ):
            button = QPushButton(label)
            button.setToolTip(tip)
            button.clicked.connect(slot)
            bar.addWidget(button)
        self.fold = QPushButton("▾ Plegar")
        self.fold.setToolTip(
            "Pliega o despliega el databank para dar toda la altura al módulo."
        )
        self.fold.clicked.connect(self.toggle)
        bar.addWidget(self.fold)
        lay.addLayout(bar)
        self.tabs = QTabWidget()
        self.left, self.right = table(STRATEGIES), table(PORTFOLIOS)
        self.tabs.addTab(self.left, "Estrategias")
        self.tabs.addTab(self.right, "Carteras")
        self.left.itemSelectionChanged.connect(self.picked)
        self.right.itemSelectionChanged.connect(self.picked)
        self.tabs.currentChanged.connect(lambda _: self.picked())
        lay.addWidget(self.tabs, 1)

    def toggle(self) -> None:
        """Fold or unfold the tables; the toolbar stays."""
        self.tabs.setVisible(not self.tabs.isVisible())
        self.fold.setText("▾ Plegar" if self.tabs.isVisible() else "▴ Desplegar")
        self.setMaximumHeight(16777215 if self.tabs.isVisible() else 48)

    def fill(self, strategies: list[dict], state: dict, run: str = "") -> None:
        """Both tables from the archive's list and `portfolios/state`; `run` (else the newest) is chosen."""
        kept = {
            r["identity"] for r in self.ticked()
        }  # a job ending reloads the list: the marks are the owner's
        self.strategies = strategies
        holds = {}
        for pool in state["pools"]:
            for identity in pool["members"]:
                holds.setdefault(identity, []).append(pool["name"])
        self.left.setRowCount(len(strategies))
        for i, r in enumerate(strategies):
            cells = (
                "",
                r["strategy"] or "—",
                r["symbol"],
                r["timeframe"] or "—",
                r["step"],
                num(len(r["versions"])),
                detail.when(r["archived_at"]),
                ", ".join(holds.get(r["identity"], [])) or "—",
                ", ".join(r.get("mt5", [])) or "—",
                r["identity"][:8],
            )
            for j, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setToolTip(
                    f"Identidad: {r['identity']}" if j else STRATEGIES[0][1]
                )
                if j == 0:
                    item.setFlags(
                        Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if r["identity"] in kept
                        else Qt.CheckState.Unchecked
                    )
                self.left.setItem(i, j, item)
        self.left.resizeColumnsToContents()
        pools = [
            {
                "kind": "pool",
                "id": p["name"],
                "pool": p["name"],
                "plan": "",
                "k": len(p["members"]),
                "score": None,
                "label": "—",
                "relaxed": {},
            }
            for p in state["pools"]
        ]
        self.rows = state["runs"] + pools
        self.right.setRowCount(len(self.rows))
        for i, r in enumerate(self.rows):
            funded, score = r["kind"] == "funded", r["score"]
            cells = (
                KINDS[r["kind"]],
                r["id"],
                r["pool"],
                r["plan"] or "—",
                num(r["k"]),
                "—" if score is None or funded else f"{score:.3f}",
                f"{score:.1%}" if funded and score is not None else "—",
                "AJUSTADO" if r["relaxed"] else "—",
                r["label"].split(" (")[0],
            )
            for j, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setToolTip(r["label"] if j == 8 else PORTFOLIOS[j][1])
                if j == 7 and r["relaxed"]:
                    item.setForeground(QColor(colour("watch")))
                self.right.setItem(i, j, item)
        self.right.resizeColumnsToContents()
        self.right.setColumnWidth(
            len(PORTFOLIOS) - 1, 120
        )  # the last one stretches: no sideways scroll
        self.tabs.setTabText(0, f"Estrategias ({num(len(strategies))})")
        self.tabs.setTabText(1, f"Carteras ({num(len(self.rows))})")
        if not strategies:
            self.said.setText(EMPTY)
        elif (
            self.said.text() == EMPTY
        ):  # anything else said («Pool declarado.») outlives the reload it causes
            self.said.setText("")
        if self.rows:
            self.tabs.setCurrentIndex(1)
            self.right.selectRow(
                next((i for i, r in enumerate(self.rows) if r["id"] == run), 0)
            )

    def tick(self, on: bool) -> None:
        """Tick or untick every strategy."""
        for i in range(self.left.rowCount()):
            box = self.left.item(i, 0)
            assert box is not None
            box.setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)

    def ticked(self) -> list[dict]:
        """The ticked strategies, each with its newest version."""
        return [
            {"identity": r["identity"], "version": r["versions"][-1]["version"]}
            for i, r in enumerate(self.strategies)
            if (box := self.left.item(i, 0)) is not None
            and box.checkState() == Qt.CheckState.Checked
        ]

    def picked(self) -> None:
        """A row of the tab on screen was chosen: tell the zone what the modules now read."""
        table_, rows = (
            (self.left, self.strategies)
            if self.tabs.currentIndex() == 0
            else (self.right, self.rows)
        )
        got = table_.selectionModel().selectedRows()
        if not got:
            return
        row = rows[got[0].row()]
        if table_ is self.left:
            return self.chosen.emit({"strategy": row["identity"]})
        self.chosen.emit(
            {
                "pool": row["pool"],
                "run": "" if row["kind"] == "pool" else row["id"],
                "strategy": "",
            }
        )

    def declare(self) -> None:
        """Name the ticked strategies as a pool, after a confirmation that says it is frozen."""
        members = self.ticked()
        if len(members) < 2:
            return self.say(
                "Marca al menos dos estrategias (pestaña «Estrategias», primera columna).",
                "watch",
            )
        name, ok = QInputDialog.getText(
            self,
            "Declarar pool",
            "Nombre del pool (Trade_…, Test_… o Research_…, sin espacios):",
        )
        if not ok or not name:
            return
        if (
            QMessageBox.question(  # pyright: ignore[reportCallIssue]  # PySide6 stub wants button0/button1 for the 3-arg form
                self, "Confirmar", FROZEN.format(name=name, n=len(members))
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        background.post(
            "portfolios/pool",
            {"name": name, "members": members},
            self.written,
            owner=self,
        )

    def written(self, got: dict) -> None:
        """The daemon declared the pool, or says why not."""
        if not got.get("ok"):
            return self.say(
                "No se declara: "
                + "; ".join(got.get("reasons") or [got.get("error", "")]),
                "fail",
            )
        self.say("Pool declarado.", "pass")
        self.declared.emit()

    def say(self, words: str, state: str) -> None:
        """One line beside the title, in a state's colour."""
        self.said.setText(f'<span style="color:{colour(state)}">{words}</span>')

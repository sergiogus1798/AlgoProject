"""PORTFOLIOS: a rail of modules, each with its strip and result tabs, over one databank that feeds them all."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QSplitter, QStackedWidget,
                               QVBoxLayout, QWidget)

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.blocks.states import colour
from ui.desktop.portfolios import strips
from ui.desktop.portfolios.databank import Databank
from ui.desktop.portfolios.modulepage import ModulePage
from ui.desktop.portfolios.zone import PortfoliosZone as ArchivePage
from ui.desktop.theme import T

TEST = "RAÍZ DE PRUEBA — {root}: nada de lo que se vea o se calcule aquí es un resultado."
TIPS = {"Archivo": "Las versiones archivadas de la estrategia elegida y «Importar esta versión»."}


class PortfoliosBoard(QFrame):
    """The zone. Left, the rail; right, the module on screen; below, the databank, whose
    selection (`selection`: pool, run, strategy) every module reads. The archive viewer
    (`zone.PortfoliosZone`) is the rail's «Archivo», and `import_requested`, `rows`, `pick`
    and `chosen` are still its own."""

    import_requested = Signal(str, str)

    def __init__(self) -> None:
        """Build the skeleton; the daemon is asked nothing until the zone is first shown."""
        super().__init__()
        self.setObjectName("term")
        self.selection, self.state, self.loaded, self.want_run = {}, {}, False, ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 12)
        lay.setSpacing(6)
        head = QHBoxLayout()
        head.addWidget(QLabel("Portfolios", objectName="kicker"))
        self.where = text("", T["muted"], 13)
        head.addWidget(self.where, 1)
        lay.addLayout(head)
        self.test = text("", T["bg"], 15, True)         # filled: a test root must never pass for the real one
        self.test.setStyleSheet(f"background:{colour('watch')}; color:{T['bg']}; font-size:15px; font-weight:700; "
                                "padding:4px 8px;")
        self.sets = QLineEdit()
        self.sets.setPlaceholderText("Ajustes de prueba que se pasan a «Calcular»: --set sección.clave=valor …")
        self.sets.setToolTip("Solo existe en la raíz de prueba: valores de prueba para los umbrales y las decisiones "
                             "que faltan. En la raíz real no se admite ninguno.")
        for widget in (self.test, self.sets):
            widget.hide()
            lay.addWidget(widget)
        self.rail, self.stack = QListWidget(), QStackedWidget()
        self.rail.setFixedWidth(180)
        self.rail.setStyleSheet(f"font-size:15px; color:{T['text']};")
        self.archive = ArchivePage()
        self.archive.loaded = True          # this zone reloads it, with its own state
        self.archive.import_requested.connect(self.import_requested)
        self.pages = {name: ModulePage(name, self) for name in strips.MODULES}
        for name, page in (self.pages | {strips.ARCHIVE: self.archive}).items():
            self.rail.addItem(name)
            self.rail.item(self.rail.count() - 1).setToolTip(TIPS.get(name) or strips.MODULES[name]["intro"])
            self.stack.addWidget(page)
        self.rail.currentRowChanged.connect(self.show_module)
        top = QWidget()
        row = QHBoxLayout(top)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.rail)
        row.addWidget(self.stack, 1)
        self.bank = Databank()
        self.bank.chosen.connect(self.choose)
        self.bank.declared.connect(self.reload)
        split = QSplitter(Qt.Vertical)
        split.addWidget(top)
        split.addWidget(self.bank)
        split.setSizes([760, 240])
        split.setCollapsible(0, False)
        lay.addWidget(split, 1)
        self.rail.setCurrentRow(0)

    rows = property(lambda self: self.archive.rows)

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Read the archive and the portfolio folder the first time the zone is shown."""
        super().showEvent(event)
        if not self.loaded:
            self.reload()

    def reload(self) -> None:
        """Read the archive and what exists under the portfolio folder again."""
        self.loaded = True
        self.archive.reload()
        background.get("portfolios/state", self.filled, "portfolios:state", self)

    def filled(self, got: dict) -> None:
        """`portfolios/state` answered: the test-root banner, the databank, the module on screen."""
        if "error" in got:
            return self.where.setText(f'<span style="color:{colour("fail")}">{got["error"]}</span>')
        self.state = got
        self.test.setText(TEST.format(root=got["test_root"]))
        self.test.setVisible(bool(got["test_root"]))
        self.sets.setVisible(bool(got["test_root"]))
        # A pool's own row is listed under its name: without it a reload moved a chosen pool to the newest run.
        self.bank.fill(self.archive.rows, got, self.want_run or self.selection.get("run") or self.selection.get("pool", ""))
        self.choose({})

    def run(self) -> dict:
        """The row of the run chosen in the databank, {} when a pool or nothing is."""
        return next((r for r in self.state.get("runs", []) if r["id"] == self.selection.get("run")), {})

    def overrides(self) -> str:
        """The test root's `--set` line; always "" on the real root, where the field does not exist."""
        return self.sets.text().strip() if self.state.get("test_root") else ""

    def computed(self) -> None:
        """A «Calcular» ended: list what exists again; the selection is kept when it still exists."""
        background.get("portfolios/state", self.filled, "portfolios:state", self)

    def choose(self, picked: dict) -> None:
        """The databank's selection changed: say it, and repaint the module on screen."""
        self.selection.update(picked)
        s = self.selection
        if s.get("strategy") and self.archive.rows:
            self.archive.pick(s["strategy"])
        name = next((r["strategy"] for r in self.archive.rows if r["identity"] == s.get("strategy")), "")
        said = [f"pool «{s['pool']}»" if s.get("pool") else "", f"cartera {s['run']}" if s.get("run") else "",
                f"estrategia {name} · {s['strategy'][:8]}" if s.get("strategy") else ""]
        self.where.setText("Selección del databank: " + (" · ".join(x for x in said if x) or "nada todavía"))
        self.show_module(self.rail.currentRow())

    def show_module(self, row: int) -> None:
        """Put a rail module on screen and let it ask for what the selection now is."""
        self.stack.setCurrentIndex(row)
        page = self.stack.currentWidget()
        if isinstance(page, ModulePage) and self.loaded:
            page.refresh()

    def open(self, module: str, tab: str = "", run: str = "") -> None:
        """Open a rail module, one of its result tabs, on one run — for the palette and the launcher."""
        self.want_run = run
        names = [self.rail.item(i).text() for i in range(self.rail.count())]
        if module in self.pages:
            self.pages[module].want_tab = tab
        self.rail.setCurrentRow(names.index(module) if module in names else 0)

    def pick(self, identity: str, version: str = "") -> None:
        """Open «Archivo» on one strategy and one of its versions ("" for the newest)."""
        self.open(strips.ARCHIVE)
        self.archive.pick(identity, version)

    def chosen(self) -> tuple[str, str]:
        """The (identity, version) on screen in «Archivo»; ("", "") when none."""
        return self.archive.chosen()

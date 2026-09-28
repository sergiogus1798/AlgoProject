"""Below the imported ficha: the backtest sheet and every study the version froze, each read from the archive."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.result import ResultView
from ui.desktop.blocks.states import colour
from ui.desktop.portfolios.detail import FAMILY
from ui.desktop.studypage.ficha import sides
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.theme import T
from ui.desktop.tradegallery import TradeGallery
from ui.text.glossary import label as words

# The Ficha's sub-tabs that read the frozen cosecha: (entry, route under /api or None for the
# trade gallery, whether the route takes the asset). «Lote» is not among them: the variant batch
# is read live by the mother's name, and the archive does not freeze it.
SHEETS = (("Ficha · IS/OOS", "tearsheet", False), ("Ficha · Salidas", "tearsheet/exits", False),
          ("Ficha · Contra el subyacente", "tearsheet/market", True),
          ("Ficha · Operaciones", None, False))


class ArchivedStudies(QFrame):
    """A list on the left — the Ficha's sheets, then each databank's frozen studies — and the
    chosen one drawn with `ResultView`. Every read carries `source=archive` and the version."""

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch) -> None:
        """Build it empty; `load` fills it.

        Args:
            fetch: GET a daemon route, never raising; injectable for a test.
        """
        super().__init__()
        self.setObjectName("term")
        self.fetch, self.shown = fetch, {}
        self.menu = QListWidget()
        self.menu.setMinimumWidth(240)
        self.menu.currentItemChanged.connect(lambda *_: self._open())
        self.note = text("", T["muted"], 13)
        self.view = ResultView()
        # The gallery asks /api/tearsheet/trades itself: every call it makes carries the version.
        self.gallery = TradeGallery(lambda path, **q: self.fetch(
            path, **q, source="archive", version=self.shown["version"]))
        self.gallery.hide()
        right = QVBoxLayout()
        right.addWidget(self.note)
        right.addWidget(self.view, 1)
        right.addWidget(self.gallery, 1)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.menu, 1)
        lay.addLayout(right, 4)

    def load(self, shown: dict) -> None:
        """List what one archived version holds and open its backtest sheet.

        Args:
            shown: `/api/archive/show` for that version.
        """
        self.shown = shown
        self.menu.blockSignals(True)
        self.menu.clear()
        for name, route, _ in SHEETS:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, ("sheet", name, shown["databank"]))
            item.setToolTip(f"Las operaciones congeladas de {shown['databank']}, IS y OOS por "
                            "separado. No es un estudio.")
            self.menu.addItem(item)
        for databank, studies in shown["held"].items():
            for s in studies:
                item = QListWidgetItem(f"{databank} › {s['title']}")
                item.setData(Qt.UserRole, ("study", s["study"], databank))
                item.setToolTip(f"{FAMILY.get(s['family'], s['family'])}"
                                f"{', paso ' + s['step'] if s['step'] else ''} · corrió el "
                                f"{s['day']} · configuración {s['config_hash'] or '—'}")
                self.menu.addItem(item)
        self.menu.blockSignals(False)
        self.menu.setCurrentRow(0)

    def _open(self) -> None:
        """Draw the entry chosen in the list."""
        item = self.menu.currentItem()
        if item is None:
            return
        kind, key, databank = item.data(Qt.UserRole)
        s = self.shown
        self.view.show()
        self.gallery.hide()
        where = {"project": s["project"], "databank": databank, "identity": s["identity"],
                 "source": "archive", "version": s["version"]}
        if kind == "study":
            got = self.fetch("result", **where, study=key, strategy=s["strategy"])
            whole = ""
            if "error" not in got and got["result"] is None:
                # A study that writes only the databank's result (spread, crossTF): the
                # archive froze that one beside the strategy, as the population page showed it.
                got = self.fetch("result", **where, study=key, strategy="")
                whole = (" · sin resultado propio de esta estrategia: es el del databank "
                         "entero, archivado con ella")
            if "error" in got:
                return self._say(got["error"])
            self.view.show_result(got["result"], got["meta"])
            self._no_report()
            return self.note.setText(f"{item.text()} · corrió el {got['meta']['day'] or '—'} · "
                                     f"leído de la versión {s['version']} del archivo{whole}")
        _, route, asset = next(e for e in SHEETS if e[0] == key)
        self.note.setText(f"{item.text()} · de la versión {s['version']} del archivo")
        if route is None:
            self.view.hide()
            self.gallery.show()
            return self.gallery.load(s["project"], databank, s["identity"], "IS", s["symbol"])
        got = self.fetch(route, **where, **({"asset": s["symbol"]} if asset else {}))
        if "error" in got:
            return self._say(got["error"])
        if [t["name"] for t in got["tabs"]] != ["IS", "OOS"]:
            self.view.show_result(got, None)
            return self._no_report()
        pair, notes = sides(got)
        self.note.setText(f"{self.note.text()}<br>{notes}")
        self.view.compare(*pair, tuple(t["title"] for t in got["tabs"]))
        # As on the live Ficha: the sheet judges nothing, so compare()'s verdict row goes.
        self.view.content.layout().itemAt(0).widget().hide()
        self._no_report()

    def _no_report(self) -> None:
        """Hide «Informe de lo que ves»: it writes its page beside the live report, under
        `reports/`, and an archived version must leave no trace outside its folder."""
        for button in self.view.findChildren(QPushButton):
            if button.text() == words("screen.report"):
                button.hide()

    def _say(self, sentence: str) -> None:
        """No drawing, and why."""
        self.note.setText(f'<span style="color:{colour("fail")}">{sentence}</span>')
        self.view.show_result(None, None)

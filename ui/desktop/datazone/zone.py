"""The «Datos» zone: the catalogue of AlgoData, and per asset its bars, its real spread and its feed quality."""

from collections.abc import Callable

from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QTabWidget, QVBoxLayout,
                               QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.datazone import tree
from ui.desktop.datazone.pages import BarsPage, StudyPage
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.theme import T

TABS = ("Catálogo", "Velas", "Spread real", "Banda del spread", "Calidad del feed")
TAB_HELP = (
    "Cada carpeta de AlgoData: cuánto ocupa, cuántos ficheros, cuándo se escribió por última vez "
    "y cuántos exports firmados (manifest.json) cuelgan de ella.",
    "Las velas del activo a D1, H4 o H1, remuestreadas de su M1 de bars/ — nunca reexportadas.",
    "Paso 4: el spread de los ticks de Darwinex por año, por hora, el modelo que lo reconstruye "
    "hacia atrás y la propuesta de coste para SQX (studies.data.spread.scan).",
    "Paso 4: la banda del spread medio diario contra el precio y los rangos del MC Retest "
    "(studies.data.spread.bands).",
    "Paso 4: los picos, congelados y huecos del feed M1 por año y por mes, y desde qué año es "
    "estable (studies.data.feedQuality.scan).")


class DataZone(QFrame):
    """The zone: an asset picker on top and five tabs, each fetched on first opening."""

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch) -> None:
        """Build the frame; the daemon is asked nothing until the zone is first shown.

        Args:
            fetch: GET a daemon route, never raising; injectable for a test.
        """
        super().__init__()
        self.setObjectName("term")
        self.fetch, self.assets, self.loaded = fetch, [], set()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)
        lay.addWidget(QLabel("BIBLIOTECA · DATOS", objectName="kicker"))
        lay.addWidget(QLabel("Datos", objectName="h1"))
        self.total = text("", T["muted"], 13)
        lay.addWidget(self.total)
        rule = QFrame(objectName="rule")
        lay.addWidget(rule)

        row = QHBoxLayout()
        row.addWidget(QLabel(label("activo"), objectName="dim"))
        self.picker = QComboBox()
        self.picker.setMinimumWidth(160)
        self.picker.currentIndexChanged.connect(self._asset_changed)
        row.addWidget(self.picker)
        self.facts = QLabel("", objectName="dim")
        row.addWidget(self.facts, 1)
        lay.addLayout(row)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.catalogue = QWidget()
        QVBoxLayout(self.catalogue).setContentsMargins(0, 8, 0, 0)
        self.pages = {"Catálogo": self.catalogue, "Velas": BarsPage(fetch),
                      "Spread real": StudyPage(fetch, "data/spread", "spread", "spread"),
                      "Banda del spread": StudyPage(fetch, "data/spread", "spread", "band"),
                      "Calidad del feed": StudyPage(fetch, "data/feedquality", "feedQuality")}
        for i, name in enumerate(TABS):
            self.tabs.addTab(self.pages[name], name)
            self.tabs.setTabToolTip(i, TAB_HELP[i])
        self.tabs.currentChanged.connect(lambda _: self._refresh())
        lay.addWidget(self.tabs, 1)

    def showEvent(self, event: object) -> None:  # noqa: N802 — Qt's name
        """Ask the daemon for the asset list the first time the zone is shown.

        Args:
            event: Qt's show event.
        """
        super().showEvent(event)
        if not self.assets:
            self.reload()

    def reload(self) -> None:
        """Read the assets again and redraw the open tab; every other tab is refetched on opening."""
        got = self.fetch("data/assets")
        if "error" in got:
            self.total.setText(got["error"])
            return
        self.assets, self.loaded = got["assets"], set()
        chosen = self.picker.currentText()
        self.picker.blockSignals(True)
        self.picker.clear()
        self.picker.addItems([a["symbol"] for a in self.assets])
        self.picker.setCurrentIndex(max(0, self.picker.findText(chosen or "XAUUSD")))
        self.picker.blockSignals(False)
        self._asset_changed()

    def asset(self) -> dict | None:
        """The asset row chosen in the picker, None before the list arrives."""
        i = self.picker.currentIndex()
        return self.assets[i] if 0 <= i < len(self.assets) else None

    def open(self, symbol: str, tab: str = "Velas") -> None:
        """Choose an asset and a tab from outside, e.g. a launcher or the asset zone.

        Args:
            symbol: As the picker lists it.
            tab: One of TABS.
        """
        if not self.assets:
            self.reload()
        self.picker.setCurrentIndex(max(0, self.picker.findText(symbol)))
        self.tabs.setCurrentIndex(TABS.index(tab))

    def _asset_changed(self) -> None:
        """A new asset: its one-line summary, and every asset tab to be refetched."""
        a = self.asset()
        if a is None:
            return
        bars = (f"M1 {a['from']} → {a['to']} · {num(a['count'])} velas" if a["bars"]
                else "sin barras en la librería")
        self.facts.setText(f"{bars} · spread: {a['spread'] or '—'} · calidad: "
                           f"{a['feedQuality'] or '—'}")
        self.loaded &= {"Catálogo"}
        self._refresh()

    def _refresh(self) -> None:
        """Fetch the open tab if it has not been fetched for this asset yet."""
        name = TABS[self.tabs.currentIndex()]
        if name in self.loaded:
            return
        self.loaded.add(name)
        if name == "Catálogo":
            self._draw_catalogue()
        else:
            self.pages[name].load(self.asset())

    def _draw_catalogue(self) -> None:
        """The tree of AlgoData, and the total above the tabs."""
        body = self.fetch("data/catalogue")
        lay = self.catalogue.layout()
        while lay.count():
            old = lay.takeAt(0).widget()
            old.hide()
            old.deleteLater()
        if "error" in body:
            lay.addWidget(text(body["error"], T["muted"], 14))
            return
        self.total.setText(f"{body['root']}/ · {tree.size(body['total_bytes'])} en "
                           f"{num(sum(r['files'] for r in body['rows'] if r['depth'] == 1))} "
                           f"ficheros · rancio a partir de {body['stale_days']} días sin escribir")
        lay.addWidget(tree.build(body))

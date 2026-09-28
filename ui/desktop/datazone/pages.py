"""The Datos zone's pages that depend on the asset: its bars, and one step-4 study read back as a ResultView."""

from collections.abc import Callable
from datetime import date, timedelta

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop.blocks import chart
from ui.desktop.blocks.card import text
from ui.desktop.blocks.result import ResultView
from ui.desktop.blocks.states import REAL
from ui.desktop.datazone import candles
from ui.text.glossary import label
from ui.text.numbers import num
from ui.desktop.theme import T

# (text in the combo, days back from the feed's last bar; None keeps the whole history).
RANGES = (("toda la historia", None), ("10 años", 3653), ("3 años", 1096), ("1 año", 366),
          ("3 meses", 92))
DEFAULT_RANGE = 3        # «1 año»: at D1 its ~260 bars are drawn as candles, not columns
KEYS = {True: [("box", candles.UP, "vela que sube"), ("box", candles.DOWN, "vela que baja")],
        False: [("line", T["faint"], "rango máximo–mínimo de las velas de cada columna"),
                ("line", REAL, "cierre de la última vela de la columna")]}


def _swap(lay: QVBoxLayout, old: QWidget | None, new: QWidget) -> QWidget:
    """Put `new` where `old` was, at the end of the layout.

    Args:
        lay: The page's layout.
        old: The previous drawing, None the first time.
        new: The drawing that replaces it.

    Returns:
        `new`. The old one is hidden before `deleteLater`, which only runs with the event loop.
    """
    if old is not None:
        old.hide()
        old.deleteLater()
    lay.addWidget(new)
    return new


class BarsPage(QWidget):
    """One asset's M1 library resampled to D1, H4 or H1, drawn as candles or as its envelope."""

    def __init__(self, fetch: Callable[..., dict]) -> None:
        """Build the two pickers; nothing is fetched until `load`.

        Args:
            fetch: GET a daemon route, never raising (`studypage.net.fetch`).
        """
        super().__init__()
        self.fetch, self.asset, self.body = fetch, None, None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 0)
        row = QHBoxLayout()
        self.tf, self.span = QComboBox(), QComboBox()
        self.tf.addItems(["D1", "H4", "H1"])
        self.span.addItems([t for t, _ in RANGES])
        self.span.setCurrentIndex(DEFAULT_RANGE)
        for name, combo in (("timeframe", self.tf), ("periodo", self.span)):
            row.addWidget(QLabel(label(name), objectName="dim"))
            row.addWidget(combo)
            combo.currentIndexChanged.connect(lambda _: self.load(self.asset))
        row.addStretch(1)
        lay.addLayout(row)
        self.head = text("", T["muted"], 13)
        lay.addWidget(self.head)
        self.lay = QVBoxLayout()         # the drawing's slot, held at the top of the page
        lay.addLayout(self.lay)
        lay.addStretch(1)

    def load(self, asset: dict | None) -> None:
        """Fetch and draw the chosen asset's bars.

        Args:
            asset: A row of `/api/data/assets`, None before one is chosen.
        """
        self.asset = asset
        if not asset:
            return
        if not asset["bars"]:
            self.head.setText(f"{asset['symbol']} no tiene barras en la librería (bars/): "
                              "solo sus ticks de Darwinex para el spread.")
            self.body = _swap(self.lay, self.body, QWidget())
            return
        days = RANGES[self.span.currentIndex()][1]
        since = "" if days is None else str(date.fromisoformat(asset["to"]) - timedelta(days))
        b = self.fetch("data/bars", feed=asset["bars"], tf=self.tf.currentText(), since=since)
        if "error" in b or not b.get("t"):
            self.head.setText(b.get("error", "Ninguna vela en ese periodo."))
            self.body = _swap(self.lay, self.body, QWidget())
            return
        self.head.setText(f"{b['feed']} · {b['tf']} · {num(b['rows'])} velas · {b['t'][0]} → "
                          f"{b['t'][-1]} · remuestreadas del M1 de la librería, idénticas al "
                          "export de SQX")
        box = QWidget()
        inner = QVBoxLayout(box)
        inner.setContentsMargins(0, 0, 0, 0)
        keys = {m: chart.key(items) for m, items in KEYS.items()}
        state = {"mode": None}

        def mode(fits: bool) -> None:
            """Show the key of what was just painted; the width can switch it on a resize."""
            if state["mode"] is not fits:
                state["mode"] = fits
                keys[True].setVisible(fits)
                keys[False].setVisible(not fits)

        inner.addWidget(candles.canvas(b, mode))
        for k in keys.values():
            k.hide()
            inner.addWidget(k)
        self.body = _swap(self.lay, self.body, box)


class StudyPage(QWidget):
    """One step-4 report of the chosen asset, as the study wrote it, drawn by ResultView."""

    def __init__(self, fetch: Callable[..., dict], route: str, kind: str, part: str = "") -> None:
        """Wire the route; nothing is fetched until `load`.

        Args:
            fetch: GET a daemon route, never raising.
            route: "data/spread" or "data/feedquality".
            kind: Which feed of the asset row it reads: "spread" or "feedQuality".
            part: For the spread route, "spread" or "band".
        """
        super().__init__()
        self.fetch, self.route, self.kind, self.part = fetch, route, kind, part
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 0)
        self.head = text("", T["muted"], 13)
        self.view = ResultView()
        lay.addWidget(self.head)
        lay.addWidget(self.view, 1)

    def load(self, asset: dict | None) -> None:
        """Fetch and draw the chosen asset's report.

        Args:
            asset: A row of `/api/data/assets`, None before one is chosen.
        """
        if not asset:
            return
        feed = asset[self.kind]
        if not feed:
            self.head.setText(f"{asset['symbol']} no tiene feed en {self.kind}/: este estudio "
                              "no se ha corrido sobre él.")
            self.view.show_result(None)
            return
        got = self.fetch(self.route, feed=feed, **({"part": self.part} if self.part else {}))
        self.head.setText(got.get("error", f"{feed} · leído de AlgoData/{self.kind}/{feed}/, "
                                           "tal y como lo escribió el estudio"))
        self.view.show_result(got.get("result"))

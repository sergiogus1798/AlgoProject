"""`TradeGallery`: five trades of one sample, by P&L quantile or drawn with a shown seed — never the best alone."""

from collections.abc import Callable

from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.studypage.net import fetch as daemon_fetch
from ui.desktop.theme import T
from ui.desktop.tradegallery.tile import tile

HELP = {"IS": "Operaciones de la muestra de construcción (IS).",
        "OOS": "Operaciones de la muestra fuera de muestra (OOS, oos1). oos2 nunca se lee.",
        "quantile": ("Las operaciones en los cuantiles 0, 25, 50, 75 y 100 % del P&L de la "
                     "muestra: la peor, la mediana y la mejor, siempre juntas."),
        "random": ("Cinco operaciones al azar de la muestra, con una semilla nueva. La semilla "
                   "se muestra: la misma semilla vuelve a sacar las mismas cinco.")}


class TradeGallery(QWidget):
    """The «Operaciones» sub-tab: a sample switch, the pick buttons, the seed, five tiles."""

    def __init__(self, fetch: Callable[..., dict] = daemon_fetch) -> None:
        """Build the empty gallery.

        Args:
            fetch: `fetch(path, **params) -> dict`, the daemon call; a test hands in its own.
        """
        super().__init__()
        self.fetch, self.where, self.pick, self.seed = fetch, None, "quantile", ""
        frame = QFrame()
        frame.setObjectName("term")
        frame.setStyleSheet(f"QFrame#term QPushButton:checked {{ background: {T['text']};"
                            f" color: {T['bg']}; border-color: {T['text']}; }}")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)
        lay = QVBoxLayout(frame)
        bar = QHBoxLayout()
        self.samples = QButtonGroup(self)
        for name in ("IS", "OOS"):
            b = QPushButton(name)
            b.setCheckable(True)
            b.setToolTip(HELP[name])
            b.clicked.connect(lambda _=False, n=name: self._switch(n))
            self.samples.addButton(b)
            bar.addWidget(b)
        bar.addSpacing(18)
        self.quant = QPushButton("cuantiles 0·25·50·75·100 %")
        self.quant.setToolTip(HELP["quantile"])
        self.quant.clicked.connect(lambda: self._repick("quantile"))
        self.other = QPushButton("otra muestra")
        self.other.setToolTip(HELP["random"])
        self.other.clicked.connect(lambda: self._repick("random"))
        for b in (self.quant, self.other):
            b.setCheckable(True)
            bar.addWidget(b)
        self.seed_label = QLabel("")
        self.seed_label.setObjectName("mono")
        self.seed_label.setToolTip("La semilla del sorteo al azar: la misma semilla saca las "
                                   "mismas cinco operaciones.")
        bar.addWidget(self.seed_label)
        bar.addStretch(1)
        lay.addLayout(bar)
        self.head = text("", T["muted"], 13)
        lay.addWidget(self.head)
        self.body = QVBoxLayout()
        holder = QWidget()
        holder.setLayout(self.body)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)
        lay.addWidget(scroll, 1)

    def load(self, project: str, databank: str, identity: str, sample: str = "IS",
             asset: str = "") -> None:
        """Show five quantile trades of one strategy's sample.

        Args:
            project, databank, identity: One strategy inside one databank.
            sample: "IS" or "OOS".
            asset: The owner's override of the asset, empty to read it off the project's name.
        """
        self.where = {"project": project, "databank": databank, "identity": identity,
                      "asset": asset, "sample": sample}
        self.pick, self.seed = "quantile", ""
        self._refresh()

    def _switch(self, sample: str) -> None:
        """Another sample, same kind of pick (a random pick keeps its seed)."""
        if self.where:
            self.where["sample"] = sample
            self._refresh()

    def _repick(self, pick: str) -> None:
        """Back to the quantiles, or five new random trades with a fresh seed."""
        if self.where:
            self.pick, self.seed = pick, ""
            self._refresh()

    def _refresh(self) -> None:
        """Ask the daemon and redraw the tiles."""
        for b in self.samples.buttons():
            b.setChecked(b.text() == self.where["sample"])
        self.quant.setChecked(self.pick == "quantile")
        self.other.setChecked(self.pick == "random")
        got = self.fetch("tearsheet/trades", **self.where, pick=self.pick, seed=self.seed)
        while self.body.count():
            w = self.body.takeAt(0).widget()
            if w:
                w.hide()
                w.deleteLater()
        if "error" in got:
            self.head.setText(got["error"])
            self.seed_label.setText("")
            return
        self.seed = str(got["seed"]) if got["seed"] is not None else ""
        self.seed_label.setText(f"semilla {self.seed}" if self.seed else "")
        how = ("en los cuantiles 0/25/50/75/100 % del P&L" if got["pick"] == "quantile"
               else f"al azar con la semilla {self.seed}")
        shown = min(5, got["n"])
        self.head.setText(
            f"{got['name']} · {got['sample']} · {shown} de {got['n']} operaciones {how} · "
            f"barras {got['feed'] or '—'} {got['tf']} · cosecha {got['harvest_day']}"
            + (f"\n{got['bars_note']}" if got["bars_note"] else ""))
        for t in got["tiles"]:
            self.body.addWidget(tile(t))
        self.body.addStretch(1)

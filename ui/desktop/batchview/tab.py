"""«Lote»: one mother's variant batch in parallel coordinates, coloured by NetProfit build, oos1 or oos2."""

import httpx
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.desktop import client
from ui.desktop.batchview import scale
from ui.desktop.batchview.parallel import Parallel
from ui.desktop.blocks.chart import key
from ui.desktop.blocks.states import REAL

METRICS = ("NetProfit (oos1)", "NetProfit (build)", "NetProfit (oos2)")
TIP = {"NetProfit (oos1)": "Beneficio neto de cada variante en el tramo oos1, el primer tramo "
                           "fuera de muestra del retest del lote.",
       "NetProfit (build)": "Beneficio neto de cada variante en el tramo build, el mismo "
                            "periodo en que se construyó la madre.",
       "NetProfit (oos2)": "Beneficio neto de cada variante en el tramo oos2, el segundo tramo "
                           "fuera de muestra, cuando el lote se retesteó sobre él."}


def has_batch(project: str, strategy: str) -> bool:
    """Whether a mother has a variant batch, for the strategy page to decide on the tab.

    Args:
        project: Project name.
        strategy: The mother's name, spaces or underscores.

    Returns:
        False too when the daemon does not answer: no tab is better than a broken one.
    """
    try:
        return client.get("batch/has", project=project, strategy=strategy)["has_batch"]
    except httpx.HTTPError:
        return False


class BatchTab(QFrame):
    """The tab: the note, the colour selector, the chart and its key; a sentence instead when
    there is nothing to draw."""

    def __init__(self) -> None:
        """Build the empty tab."""
        super().__init__()
        self.setObjectName("term")
        self.batch = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        head = QLabel("LOTE DE VARIANTES")
        head.setObjectName("kicker")
        self.note = QLabel()
        self.note.setObjectName("dim")
        self.note.setWordWrap(True)
        row = QHBoxLayout()
        self.pick = QLabel("colorear por")
        self.pick.setObjectName("mono")
        self.colour_by = QComboBox()
        for m in METRICS:
            self.colour_by.addItem(m)
            self.colour_by.setItemData(self.colour_by.count() - 1, TIP[m], Qt.ToolTipRole)
        self.colour_by.currentTextChanged.connect(self.redraw)
        row.addWidget(self.pick)
        row.addWidget(self.colour_by)
        row.addStretch(1)
        self.chart = Parallel()
        self.keys = QWidget()
        self.keys.setLayout(QVBoxLayout())
        self.keys.layout().setContentsMargins(0, 0, 0, 0)
        for w in (head, self.note):
            lay.addWidget(w)
        lay.addLayout(row)
        lay.addWidget(self.chart)
        lay.addWidget(self.keys)
        lay.addStretch(1)

    def load(self, project: str, strategy: str) -> bool:
        """Fetch and draw one mother's batch.

        Args:
            project: Project name.
            strategy: The mother's name, spaces or underscores.

        Returns:
            `has_batch` as the daemon said it; False when the daemon does not answer.
        """
        try:
            data = client.get("batch", project=project, strategy=strategy)
        except httpx.HTTPError as err:
            data = {"has_batch": False, "error": f"el demonio no responde: {err}"}
        self.show_batch(data)
        return data["has_batch"]

    def show_batch(self, data: dict) -> None:
        """Draw an `/api/batch` answer, or its sentence.

        Args:
            data: The route's JSON.
        """
        self.batch = None if "error" in data else data
        self.note.setText(data.get("error") or data["note"])
        if self.batch is not None:                  # oos2 only when the batch carries it
            chosen = self.colour_by.currentText()
            self.colour_by.blockSignals(True)
            self.colour_by.clear()
            for m in (m for m in METRICS if m in self.batch["outcomes"]):
                self.colour_by.addItem(m)
                self.colour_by.setItemData(self.colour_by.count() - 1, TIP[m], Qt.ToolTipRole)
            self.colour_by.setCurrentText(chosen if chosen in self.batch["outcomes"] else METRICS[0])
            self.colour_by.blockSignals(False)
        for w in (self.pick, self.colour_by, self.chart, self.keys):
            w.setVisible(self.batch is not None)
        if self.batch is not None:
            self.redraw(self.colour_by.currentText())

    def redraw(self, metric: str) -> None:
        """Colour and rank by one outcome, and rewrite the key under the chart.

        Args:
            metric: One of `METRICS`.
        """
        if self.batch is None:
            return
        self.chart.set_batch(self.batch, metric)
        vals = self.batch["outcomes"][metric]
        items = scale.key(vals, scale.edges(vals))
        if self.batch["mother"] is not None:
            items.append(("dash", REAL, f"la madre, {self.batch['variants'][self.batch['mother']]}"))
        lay = self.keys.layout()
        while lay.count():
            gone = lay.takeAt(0).widget()
            gone.hide()          # deleteLater waits for the event loop; until then it paints
            gone.deleteLater()
        title = QLabel(f"color = {metric}, en nueve tramos iguales entre −M y +M "
                       "(rojo pierde, azul gana); pasa el ratón por una línea para ver sus valores")
        title.setObjectName("dim")
        title.setWordWrap(True)
        title.setToolTip(TIP[metric])
        lay.addWidget(title)
        for at in range(0, len(items), 4):   # chart.key joins with no-break spaces: rows of four
            lay.addWidget(key(items[at:at + 4]))

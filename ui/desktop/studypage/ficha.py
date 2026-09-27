"""The «Ficha» tab of the strategy page: IS/OOS side by side, exits, the underlying, the trades, the batch."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QTabWidget, QVBoxLayout, QWidget

from ui.desktop.blocks.card import text
from ui.desktop.blocks.result import ResultView
from ui.desktop.blocks.states import colour
from ui.desktop.studypage.net import fetch
from ui.desktop.theme import T

# (sub-tab, route under /api or None for a widget of its own, whether the route takes the
# asset). A result whose tabs are exactly «IS», «OOS» is drawn with IS beside OOS.
SUBS = (("IS/OOS", "tearsheet", False), ("Salidas", "tearsheet/exits", False),
        ("Contra el subyacente", "tearsheet/market", True), ("Operaciones", None, False),
        ("Lote", None, False))
LOTE = len(SUBS) - 1    # shown only when the strategy is the mother of a variant batch
PENDING = "pendiente: {what} todavía no está en esta versión de la ventana."


def sides(result: dict) -> tuple[list[dict], str]:
    """A result's tabs as one-tab results under one shared name, so `compare` pairs them.

    Args:
        result: A contract result whose tabs are the samples («IS», «OOS»).

    Returns:
        (one result per sample in the result's order, their tab notes as one text) — the
        notes move above the columns, where each is read beside the other.
    """
    title = " · ".join(f"{t['title']} a la {side}" for t, side in
                       zip(result["tabs"], ("izquierda", "derecha")))
    return ([{**result, "tabs": [{**t, "name": "muestra", "title": title, "note": ""}]}
             for t in result["tabs"]], "<br>".join(t["note"] for t in result["tabs"]))


class Sub(QWidget):
    """One sub-tab: a line saying what is shown (or why not), then the drawing."""

    def __init__(self, body: QWidget) -> None:
        """Hold `body` under a line of text."""
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 0)
        self.line = text("", T["muted"], 14)
        self.body = body
        lay.addWidget(self.line, 0, Qt.AlignTop)
        lay.addWidget(body, 1)
        lay.addStretch()            # takes the height when the body is hidden

    def say(self, sentence: str, ink: str = T["muted"]) -> None:
        """Show a sentence in place of the drawing."""
        self.line.setText(f'<span style="color:{ink}">{sentence}</span>')
        self.body.hide()


class Ficha(QFrame):
    """What the harvest says of the strategy SELECTION holds. Not a study: no run bar, no
    drawer, no history; its staleness is the cosecha's day, printed in the note."""

    def __init__(self) -> None:
        """Build the four sub-tabs, empty; each fills on its first opening per strategy."""
        super().__init__()
        self.setObjectName("term")
        self.where: dict = {}
        self.done: set[int] = set()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        self.note = text("", T["text"], 14)
        lay.addWidget(self.note)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.subs = [Sub(ResultView() if route else QLabel()) for _, route, _ in SUBS]
        for sub, (name, _, _) in zip(self.subs, SUBS):
            self.tabs.addTab(sub, name)
        self.tabs.setTabToolTip(LOTE, "Las variantes de esta madre en coordenadas paralelas: "
                                      "sólo los tramos build y oos1, nunca oos2.")
        self.tabs.setTabVisible(LOTE, False)
        self.tabs.currentChanged.connect(self._open)
        lay.addWidget(self.tabs, 1)

    def load(self, where: dict) -> None:
        """Follow a new selection; the open sub-tab refills now, the rest when opened.

        Args:
            where: The strategy page's selection (project, databank, strategy, identity, asset).
        """
        key = [where.get(k) for k in ("project", "databank", "identity", "asset")]
        if key == [self.where.get(k) for k in ("project", "databank", "identity", "asset")]:
            return
        self.where = dict(where)
        self.done = set()
        # The batch belongs to the mother by name, across the project's databanks.
        from ui.desktop.batchview.tab import has_batch
        self.tabs.setTabVisible(LOTE, bool(where.get("project") and where.get("strategy"))
                                and has_batch(where["project"], where["strategy"]))
        self.note.setText(f"{where.get('strategy') or 'Ninguna estrategia elegida'} · "
                          f"{where.get('project') or '—'} › {where.get('databank') or '—'}")
        self._open(self.tabs.currentIndex())

    def _open(self, index: int) -> None:
        """Fill a sub-tab the first time it is opened for this strategy."""
        if index in self.done:
            return
        self.done.add(index)
        w, sub = self.where, self.subs[index]
        if not (w.get("project") and w.get("databank") and w.get("identity")):
            return sub.say("Elige una estrategia en Población o en la matriz.")
        _, route, asset = SUBS[index]
        if index == LOTE:
            return self._batch(sub)
        if route is None:
            return self._gallery(sub)
        got = fetch(route, project=w["project"], databank=w["databank"], identity=w["identity"],
                    **({"asset": w.get("asset") or ""} if asset else {}))
        if "error" in got:
            late = "404" in got["error"]
            return sub.say(PENDING.format(what=f"/api/{route}") if late else got["error"],
                           T["muted"] if late else colour("fail"))
        day = got.get("harvest_day")
        if day and index == 0:
            self.note.setText(f"{got['strategy']} · {w['project']} › {w['databank']} · "
                              f"cosecha del {day}: la ficha lee la más nueva de este databank")
        sub.body.show()
        if [t["name"] for t in got["tabs"]] != ["IS", "OOS"]:
            sub.line.setText("")
            return sub.body.show_result(got, None)
        pair, notes = sides(got)
        sub.line.setText(notes)
        sub.body.compare(*pair, tuple(t["title"] for t in got["tabs"]))
        # compare()'s first row is each side's verdict header; the Ficha judges nothing and
        # its sides are named by the tab title and the notes above, so the row goes.
        sub.body.content.layout().itemAt(0).widget().hide()

    def _gallery(self, sub: Sub) -> None:
        """The trade gallery, imported on first use; «pendiente» while it does not exist."""
        try:
            from ui.desktop.tradegallery import TradeGallery
        except ImportError:
            return sub.say(PENDING.format(what="la galería de operaciones"))
        if not isinstance(sub.body, TradeGallery):
            sub.layout().removeWidget(sub.body)
            sub.body.deleteLater()
            sub.body = TradeGallery()
            sub.layout().insertWidget(1, sub.body, 1)
        sub.line.setText("")
        sub.body.show()
        w = self.where
        sub.body.load(w["project"], w["databank"], w["identity"], "IS")

    def _batch(self, sub: Sub) -> None:
        """The mother's variant batch, built on first use like the gallery."""
        from ui.desktop.batchview.tab import BatchTab
        if not isinstance(sub.body, BatchTab):
            sub.layout().removeWidget(sub.body)
            sub.body.hide()
            sub.body.deleteLater()
            sub.body = BatchTab()
            sub.layout().insertWidget(1, sub.body, 1)
        sub.line.setText("")
        sub.body.show()
        sub.body.load(self.where["project"], self.where["strategy"])

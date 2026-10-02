"""The «Ficha» tab of the strategy page: IS/OOS side by side — P&L, drawdown, years."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from ui.desktop.blocks.card import text
from ui.desktop.blocks.result import ResultView
from ui.desktop.blocks.states import colour
from ui.desktop.studypage.net import fetch
from ui.desktop.theme import C, T

# (sub-tab, route under /api). A result whose tabs are exactly «IS», «OOS» is drawn with IS
# beside OOS. The owner took «Salidas», «Contra el subyacente» and «Operaciones» out on
# 2026-09-28; PORTFOLIOS still lists them for an archived version. «Lote» moved to the WFC
# study's own tab on 2026-09-29 — a strategy can have no batch, so it does not belong here.
SUBS = (("IS/OOS", "tearsheet"),)
TOP = 5                 # «Excluir top X% de trades»: the X it opens with
PICKED = (f"QPushButton:checked {{ background: {C['accent']}; color: {T['bg']}; font-weight: 700; }}"
          "QPushButton { min-width: 34px; }")
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
        """Build the switches and the two sub-tabs, empty; each fills on its first opening per
        strategy."""
        super().__init__()
        self.setObjectName("term")
        self.where: dict = {}
        self.done: set[int] = set()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        self.note = text("", T["text"], 14)
        lay.addWidget(self.note)
        lay.addLayout(self._knobs())
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.subs = [Sub(ResultView()) for _, route in SUBS]
        for sub, (name, _) in zip(self.subs, SUBS):
            self.tabs.addTab(sub, name)
        self.tabs.currentChanged.connect(self._open)
        lay.addWidget(self.tabs, 1)

    def _knobs(self) -> QHBoxLayout:
        """The IS/OOS sheet's two switches: the P&L without its best trades, the drawdown's unit."""
        self.top = QCheckBox("Excluir top")
        self.top.setToolTip("Dibuja también, discontinua, cada curva de P&L acumulado sin su X % "
                            "de operaciones mejores: si el resto no gana, el beneficio cuelga de "
                            "unas pocas.")
        self.share = QSpinBox()
        self.share.setRange(1, 50)
        self.share.setValue(TOP)
        self.share.setSuffix("%")
        self.dd = QButtonGroup(self)
        row = QHBoxLayout()
        row.addWidget(self.top)
        row.addWidget(self.share)
        row.addWidget(QLabel("de trades", objectName="dim"))
        row.addSpacing(28)
        row.addWidget(QLabel("Drawdown en", objectName="dim"))
        for i, unit in enumerate(("%", "$")):
            button = QPushButton(unit)
            button.setCheckable(True)
            button.setChecked(i == 0)
            button.setStyleSheet(PICKED)
            self.dd.addButton(button, i)
            row.addWidget(button)
        row.addStretch(1)
        self.top.toggled.connect(self._redraw)
        self.share.valueChanged.connect(lambda _: self.top.isChecked() and self._redraw())
        self.dd.idClicked.connect(self._redraw)
        return row

    def _redraw(self, *_: object) -> None:
        """A switch moved: the IS/OOS sheet is asked again, now if it is open."""
        self.done.discard(0)
        if self.tabs.currentIndex() == 0:
            self._open(0)

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
            return sub.say("Elige una estrategia en el panel de databanks de Proyecto.")
        _, route = SUBS[index]
        got = fetch(route, project=w["project"], databank=w["databank"], identity=w["identity"],
                    strategy=w.get("strategy") or "", top=self.share.value() if self.top.isChecked() else 0,
                    dd=self.dd.checkedButton().text())
        if "error" in got:
            late = "404" in got["error"]
            return sub.say(PENDING.format(what=f"/api/{route}") if late else got["error"],
                           T["muted"] if late or got.get("absent") else colour("fail"))
        if got.get("harvest_day") and index == 0:      # §3.1: no «cosecha del…» line
            self.note.setText(f"{got['strategy']} · {w['project']} › {w['databank']}"
                              + (f" · {got['note']}" if got.get("note") else ""))
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

"""The databank panel's filters strip: AND rows over real columns, discards, and the ledger (22 §7.1)."""

import threading

import httpx
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.desktop import client
from ui.desktop.workspace.filterrow import FilterRow, guessed, plain
from ui.desktop.workspace.filtersaved import SavedFilters
from ui.text.numbers import num

PREVIEW_MS = 350    # a pause in the typing before the live count asks the daemon (~0.15 s warm)


class FiltersStrip(QFrame):
    """Below the panel's header: the rows (AND), Aplicar, the saved list, «Quitar filtros» and
    «Descartar seleccionadas». It follows the panel's databank on its own, hides what is set
    aside through `panel.set_hidden` (which re-aggregates the visible ids) and reloads the
    funnel. A live count says what edited rows would leave, hiding and logging nothing; both
    reads run off the GUI thread (`arrived`, `counted`). Nothing here touches SQX."""

    arrived = Signal(dict)
    counted = Signal(dict)

    def __init__(self, panel: QWidget, funnel: QWidget | None = None) -> None:
        """Build the strip over a `workspace.panel.Panel` and, optionally, its `Funnel`."""
        super().__init__()
        self.setObjectName("term")
        self.panel, self.funnel, self.at, self.offer = panel, funnel, ("", ""), []
        self.anonymous, self.now, self.asked, self.shown_ids = 0, [], 0, None
        self.arrived.connect(self.land)
        self.counted.connect(self.show_count)
        kicker = QLabel("FILTROS")
        kicker.setObjectName("kicker")
        add, apply_, clear, drop = (QPushButton("+ condición"), QPushButton("▶ Aplicar"),
                                    QPushButton("Quitar filtros"),
                                    QPushButton("Descartar seleccionadas"))
        apply_.setToolTip("Aplica todas las condiciones a la vez (AND) sobre todo el databank y "
                          "sustituye al filtro anterior: si aflojas, vuelven las que ahora pasan. "
                          "Los descartes a mano se quedan. Sin condiciones, quita solo el filtro. "
                          "Se apunta en el Ledger como una búsqueda. No toca SQX.")
        drop.setToolTip("Oculta las filas seleccionadas; siguen ocultas aunque cambies el "
                        "filtro. También se apunta en el Ledger.")
        clear.setToolTip("Quita el filtro y los descartes a mano: vuelve a mostrar todo. Lo ya "
                         "apuntado en el Ledger se queda: se miró.")
        add.clicked.connect(lambda: self.add())
        apply_.clicked.connect(self.apply)
        clear.clicked.connect(self.clear)
        drop.clicked.connect(self.discard)
        self.saved = SavedFilters()
        self.saved.chosen.connect(self.show_rows)
        self.saved.said.connect(self.say)
        self.saved.store.clicked.connect(lambda: self.saved.save(self.rows()))
        self.said, self.guess, self.timer = QLabel(""), QLabel(""), QTimer(self)
        for w in (self.said, self.guess):
            w.setObjectName("dim")
            w.setWordWrap(True)
        self.timer.setSingleShot(True)
        self.timer.setInterval(PREVIEW_MS)
        self.timer.timeout.connect(self.preview)
        head = QHBoxLayout()
        for w in (kicker, add, apply_, clear, drop):
            head.addWidget(w)
        head.addStretch(1)
        head.addWidget(self.saved)
        self.box = QVBoxLayout()
        self.box.setSpacing(2)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(3)
        lay.addLayout(head)
        lay.addLayout(self.box)
        lay.addWidget(self.guess)
        lay.addWidget(self.said)
        panel.table.model().modelReset.connect(lambda: QTimer.singleShot(0, self.follow))

    def bank(self) -> tuple[str, str]:
        """The project and the databank the panel shows, or '' when it shows no live one."""
        spec = self.panel.sub_spec() if self.panel.live else {}
        return self.panel.project, ("" if spec.get("blocked") else spec.get("databank", ""))

    def follow(self) -> None:
        """The panel painted a table (a databank chosen, «Recargar», a «Continuar» done): read
        this databank's metrics and discards again, off the GUI thread, into `land`."""
        at = self.bank()
        self.setEnabled(bool(at[1]))
        if not at[1]:
            return
        moved, self.at = at != self.at, at

        def ask() -> None:
            """One GET: state, funnel rows and metrics off a single `context` in the daemon."""
            try:
                got = client.get("filters/state", project=at[0], databank=at[1])
            except httpx.HTTPError as failed:
                got = {"error": f"El demonio no respondió: {failed}"}
            self.arrived.emit({"at": at, "moved": moved, "got": got})
        threading.Thread(target=ask, daemon=True).start()

    def land(self, msg: dict) -> None:
        """Paint what `follow` read, unless another databank was chosen since. Rows the owner
        is still editing on the same databank are kept; the live count then re-runs."""
        got = msg["got"]
        if msg["at"] != self.at:
            return
        if "steps" not in got:
            self.say(got.get("error", ""))
            return
        editing = not msg["moved"] and plain(self.rows()) != plain(self.now)
        self.offer, self.anonymous = got.get("metrics", []), got.get("anonymous") or 0
        if editing:
            self.now = [] if got.get("stale") else got.get("conditions") or []
            self.hide_ids(got)
            self.timer.start()
        else:
            self.settle(got)
        self.say(got.get("refused") or self.counts(got))

    def counts(self, state: dict) -> str:
        """The databank's discards in one line, and the rows no filter can hide."""
        loose = state.get("anonymous") or self.anonymous
        tail = f" · {num(loose)} sin identidad, no filtrables" if loose else ""
        if state.get("orphans"):
            tail += (f" · {num(state['orphans'])} líneas de descarte sin cabecera en el registro "
                     "(truncado): no esconden nada")
        if state.get("stale"):
            tail += (f" · el filtro «{state['stale']}» es de antes de que los filtros se "
                     "recalcularan y no está en vigor: pulsa ▶ Aplicar para aplicarlo")
        if not state.get("steps"):
            return (f"{self.at[1]}: sin filtros · {num(len(self.offer))} métricas filtrables "
                    f"(OOS2 no){tail}")
        hand = f" ({num(state['manual'])} a mano)" if state.get("manual") else ""
        return (f"{self.at[1]}: {num(state['entered'])} → {num(state['remaining'])} visibles · "
                f"{num(state['hidden'])} descartadas{hand}{tail}")

    def add(self, row: dict | None = None) -> None:
        """One more condition, empty or a saved one."""
        line = FilterRow(self.offer)
        line.gone.connect(lambda w: (self.box.removeWidget(w), w.deleteLater(),
                                     self.timer.start()))
        line.changed.connect(self.timer.start)
        if row:
            line.put(row)
        self.box.addWidget(line)

    def rows(self) -> list[dict]:
        """Every condition on screen with a value typed (an empty row is none)."""
        lines = [self.box.itemAt(i).widget() for i in range(self.box.count())]
        return [w.spec() for w in lines if isinstance(w, FilterRow) and w.filled()]

    def show_rows(self, rows: list[dict]) -> None:
        """Replace the conditions on screen; one empty row when there are none."""
        while self.box.count():
            self.box.takeAt(0).widget().deleteLater()
        for row in rows or [None]:
            self.add(row)

    def settle(self, state: dict) -> None:
        """Show the conditions in force and hide what the daemon says is set aside. A stale
        filter's conditions are shown but not in force: the live count says what they leave."""
        shown = state.get("conditions") or []
        self.now = [] if state.get("stale") else shown
        self.show_rows(shown)
        self.timer.stop()
        self.guess.setText("")
        self.hide_ids(state)
        if state.get("stale"):
            self.timer.start()

    def preview(self) -> None:
        """The live count: what the rows on screen would leave, asked of the daemon off the
        GUI thread, without hiding or logging anything. Silent while they equal the filter in
        force; an answer overtaken by a later edit is dropped (`show_count`)."""
        rows = self.rows()
        self.asked += 1
        if not self.at[1] or plain(rows) == plain(self.now):
            self.guess.setText("")
            return
        seq, body = self.asked, {"project": self.at[0], "databank": self.at[1], "rows": rows}

        def ask() -> None:
            """One POST to `/api/filters/preview`."""
            try:
                got = client.post("filters/preview", body)
            except httpx.HTTPError as failed:
                got = {"error": f"el demonio no respondió: {failed}"}
            self.counted.emit({"seq": seq, "got": got})
        threading.Thread(target=ask, daemon=True).start()

    def show_count(self, msg: dict) -> None:
        """Paint a live count, unless the rows changed since it was asked."""
        if msg["seq"] == self.asked:
            self.guess.setText(guessed(msg["got"]))

    def send(self, path: str, body: dict) -> None:
        """POST to the daemon, then hide what it says is set aside and say how it went."""
        try:
            got = client.post(path, body)
        except httpx.HTTPError as failed:
            self.say(f"El demonio no respondió: {failed}")
            return
        if "error" in got:
            self.say(got["error"])
            return
        self.settle(got)
        done = self.counts(got)
        if got.get("same"):
            done = f"Ese filtro ya está aplicado: no se apunta otra vez  ·  {done}"
        elif "ledger" in got:
            led = got["ledger"]
            done = (f"{num(got['n_in'])} → {num(got['n_out'])}"
                    + (f" ({num(got['blank'])} sin valor, siguen visibles)" if got.get("blank")
                       else "")
                    + f" · apuntado en el Ledger: {led['study']}, paso {num(led['step'])}, "
                    f"{led['segment']}  ·  {done}")
        self.say(done)

    def hide_ids(self, state: dict) -> None:
        """Hand the hidden identities to the panel and, when they changed, reload the funnel."""
        ids = (self.at, set(state.get("hidden_ids", [])))
        self.panel.set_hidden(ids[1])
        if self.funnel is not None and ids != self.shown_ids:
            self.funnel.load(self.at[0])
        self.shown_ids = ids

    def apply(self) -> None:
        """«Aplicar»: the AND of the rows on the whole databank, replacing the filter in force."""
        self.send("filters/apply", {"project": self.at[0], "databank": self.at[1],
                                    "rows": self.rows()})

    def discard(self) -> None:
        """«Descartar seleccionadas»: the selected rows' identities, set aside by hand."""
        table = self.panel.table
        ids = sorted({table.rows[table.item(i.row(), 0).data(Qt.UserRole)]["identity"]
                      for i in table.selectionModel().selectedRows()} - {None})
        if not ids:
            self.say("Selecciona filas con identidad en la tabla para descartarlas")
            return
        self.send("filters/discard", {"project": self.at[0], "databank": self.at[1],
                                      "identities": ids})

    def clear(self) -> None:
        """«Quitar filtros»: the filter and the manual deletions lifted, everything visible."""
        self.send("filters/clear", {"project": self.at[0], "databank": self.at[1]})

    def say(self, text: str) -> None:
        """One line under the rows."""
        self.said.setText(text)

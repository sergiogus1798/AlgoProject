"""The data of the selected databank: loaded the moment it is chosen, and how far it has got."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ui.desktop import client
from ui.desktop.selection import SELECTION
from ui.desktop.theme import C, MONO, T

# One chip per piece, in the order they land: the metrics in a second, the trades and the
# cosecha after their turn on the conductor.
NAMES = {"metrics": "métricas", "trades": "operaciones", "harvest": "cosecha"}
LOOK = {"fresh": ("✓", C["promising"], "al día"),
        "loading": ("⟳", C["accent"], "cargando"),
        "stale": ("!", C["weak"], "vieja: sus .sqx cambiaron después"),
        "missing": ("·", C["weak"], "no cargada"),
        "none": ("—", T["faint"], "no aplica a este databank"),
        "failed": ("✗", C["dead"], "falló; ↻ para reintentar")}
POLL_MS = 3000          # while something loads
WAIT_MS = 30000         # while SQX is writing the project: try again later


class LoadBar(QWidget):
    """Three chips beside the crumbs. Choosing a databank loads it; `loaded(piece)` fires when
    a piece that was loading lands, for the shell to redraw what reads it."""

    loaded = Signal(str)

    def __init__(self) -> None:
        """Build the chips, empty, and follow the global selection."""
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.chips = {k: QLabel() for k in NAMES}
        self.note = QLabel()
        for w in (*self.chips.values(), self.note):
            w.setStyleSheet(f"font-family:{MONO}; font-size:12px;")
            lay.addWidget(w)
        self.again = QPushButton("↻")
        self.again.setToolTip("Volver a cargar lo que falló")
        self.again.setStyleSheet("border:none; padding:0 4px;")
        self.again.clicked.connect(lambda: self.show_state(self.ask("post", retry=True)))
        self.again.hide()
        lay.addWidget(self.again)
        self.writing = False
        self.where: tuple = (None, None)
        self.last: dict = {}
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.poll)
        SELECTION.changed.connect(self.follow)
        self.follow(dict(SELECTION.now))

    def follow(self, now: dict) -> None:
        """A new project or databank: ask the daemon to load whatever it lacks.

        Args:
            now: What `SELECTION.changed` carries.
        """
        where = (now["project"], now["databank"])
        if where == self.where:
            return
        self.where, self.last = where, {}
        self.timer.stop()
        if not all(where):
            return self.show_state(None)
        self.show_state(self.ask("post"))

    def poll(self) -> None:
        """Ask again how the loading goes; after SQX stopped writing, queue what is missing."""
        if all(self.where):
            self.show_state(self.ask("post" if self.writing else "get"))

    def ask(self, verb: str, retry: bool = False) -> dict:
        """POST to load (queues what is missing) or GET the state; a daemon error is shown.

        Args:
            verb: `post` or `get`.
            retry: With `post`, queue the pieces that failed too.

        Returns:
            The daemon's answer, or `{"error": sentence}`.
        """
        project, databank = self.where
        try:
            if verb == "post":
                return client.post("load", {"project": project, "databank": databank,
                                            "retry": retry})
            return client.get("load", project=project, databank=databank)
        except Exception as e:     # the window's boundary: a daemon down must not close it
            return {"error": f"el demonio no respondió: {e}"}

    def show_state(self, got: dict | None) -> None:
        """Paint the chips, fire `loaded` for pieces that just landed, and schedule a poll.

        Args:
            got: What `ask` returned, or None for no databank chosen.
        """
        if got is None or got.get("error"):
            for chip in self.chips.values():
                chip.setText("")
            self.note.setText(got["error"] if got else "")
            self.note.setStyleSheet(f"font-family:{MONO}; font-size:12px; color:{C['dead']};")
            return
        pieces = got["pieces"]
        for key, chip in self.chips.items():
            mark, ink, word = LOOK[pieces[key]["state"]]
            chip.setText(f"{mark} {NAMES[key]}")
            chip.setStyleSheet(f"font-family:{MONO}; font-size:12px; color:{ink};")
            chip.setToolTip(f"{NAMES[key].capitalize()}: {word}.\n{pieces[key]['what']}."
                            + (f"\n{pieces[key]['why']}" if "why" in pieces[key] else ""))
            if self.last.get(key) == "loading" and pieces[key]["state"] == "fresh":
                self.loaded.emit(key)
        self.last = {k: v["state"] for k, v in pieces.items()}
        self.again.setVisible("failed" in self.last.values())
        writing = self.writing = got["writing"]
        self.note.setText(f"{got['strategies']} estrategias · {got['role']}"
                          + (" · SQX está escribiendo este proyecto: se carga al terminar"
                             if writing else ""))
        self.note.setStyleSheet(f"font-family:{MONO}; font-size:12px; color:"
                                f"{C['weak'] if writing else T['faint']};")
        if writing:
            self.timer.start(WAIT_MS)
        elif "loading" in self.last.values():
            self.timer.start(POLL_MS)

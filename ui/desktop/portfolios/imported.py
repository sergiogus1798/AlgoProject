"""The Estrategia page of an archived version: F4's ficha, every read on `source=archive`, nothing run."""

import threading

from ui.desktop.portfolios.studies import ArchivedStudies
from ui.desktop.studypage.net import fetch
from ui.desktop.workspace.ficha import Ficha

FROZEN = ("archivada: aquí no se calcula nada. Para calcular, ábrela desde su proyecto en "
          "Proyectos.")


class ImportedFicha(Ficha):
    """The ficha as a live strategy shows it — the two curves, the statistics, the metadata —
    read from one archived version, with the frozen studies below instead of the study tabs.
    «Archivar» is hidden and every «calcular» answers that nothing is computed here."""

    def __init__(self) -> None:
        """Build the page empty; `open` loads a version."""
        super().__init__()
        self.version = ""
        self.keep.hide()
        self.compute.run = lambda *_: self.say(FROZEN)
        self.frozen = ArchivedStudies()
        self.family.addWidget(self.frozen, 1)
        self.short.hide()

    def open(self, shown: dict) -> None:
        """Load one archived version.

        Args:
            shown: `/api/archive/show` for that version.
        """
        self.version = shown["version"]
        self.opened_from = "PORTFOLIOS"
        self.where = {"project": shown["project"], "strategy": shown["strategy"],
                      "databank": shown["databank"], "identity": shown["identity"],
                      "asset": shown["symbol"]}
        self.compute.where = self.where
        self.title.setText(shown["strategy"])
        self.origin.setText(f"   importada del archivo · versión {shown['version']} · paso "
                            f"{shown['step']}   ·   {shown['project']}   ·   {shown['databank']}")
        self.origin.setToolTip(f"Identidad: {shown['identity']}")
        self.frozen.load(shown)
        self.say("leyendo el archivo…")
        threading.Thread(target=self.ask, args=(dict(self.where),), daemon=True).start()

    def ask(self, where: dict) -> None:
        """Off the GUI thread: the ficha's three reads, on the archived version."""
        q = {k: where[k] for k in ("project", "databank", "identity")} | {
            "source": "archive", "version": self.version}
        self.arrived.emit({"key": (where["project"], where["strategy"]),
                           "curve": fetch("strategy/costcurve", **q),
                           "stats": fetch("strategy/stats", **q),
                           "meta": fetch("strategy/meta", **q)})

    def lower(self, live: bool, family: str, study: str | None = None) -> None:
        """The frozen studies stand where the study tabs would: nothing to switch."""

    def reload(self) -> None:
        """An archived version never changes: nothing to read again."""

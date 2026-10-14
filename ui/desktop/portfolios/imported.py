"""The Estrategia page of an archived version: F4's ficha, every read on `source=archive`, nothing run."""

from typing import Any

from ui.desktop import background
from ui.desktop.blocks.card import text
from ui.desktop.portfolios.series import SeriesBar
from ui.desktop.blocks.states import colour
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
        self.compute.run = lambda *_: self.say(FROZEN)  # pyright: ignore[reportAttributeAccessIssue]  # instance override of the method: an archive runs nothing
        self.frozen = ArchivedStudies()
        self.series, self.names, self.workflow = SeriesBar(), [], ""
        self.series.step.connect(self.go)
        self.banner = text("", colour("watch"), 13)
        self.family.insertWidget(0, self.banner)
        self.family.insertWidget(0, self.series)
        self.banner.hide()
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
        self.title.setText(shown.get("label") or shown["strategy"])
        self.banner.setText(shown.get("banner", ""))
        self.banner.setVisible(bool(shown.get("banner")))
        if "workflow" not in shown:
            self.series.hide()
        self.origin.setText(f"   importada del archivo · versión {shown['version']} · paso "
                            f"{shown['step']}   ·   {shown['project']}   ·   {shown['databank']}")
        self.origin.setToolTip(f"Identidad: {shown['identity']}")
        self.frozen.load(shown)
        self.say("leyendo el archivo…")
        where = dict(self.where)
        background.run(lambda: self.ask(where), self.paint, key=f"ficha:{id(self)}", owner=self)

    def open_series(self, workflow: str, names: list[str], index: int) -> str:
        """Open one strategy of a saved workflow and arm «anterior / siguiente» over `names`.

        Args:
            workflow: The workflow's folder name.
            names: The strategies to walk, in order.
            index: Which one to show first.

        Returns:
            "" when it opened; otherwise the sentence saying why not.
        """
        self.workflow, self.names = workflow, names
        return self.go(index)

    def go(self, index: int) -> str:
        """Show the index-th strategy of the series (`/api/campaign/open`)."""
        shown = fetch("campaign/open", workflow=self.workflow, strategy=self.names[index])
        if "error" in shown:
            return shown["error"]
        self.open(shown)
        self.series.show_at(self.workflow, index, len(self.names))
        return ""

    def ask(self, where: dict) -> dict[str, Any]:
        """Off the GUI thread: the ficha's three reads, on the archived version."""
        q = {k: where[k] for k in ("project", "databank", "identity")} | {
            "source": "archive", "version": self.version}
        return {"key": (where["project"], where["strategy"]),
                "curve": fetch("strategy/costcurve", **q),
                "stats": fetch("strategy/stats", **q),
                "meta": fetch("strategy/meta", **q)}

    def lower(self, live: bool, family: str, study: str | None = None) -> None:
        """The frozen studies stand where the study tabs would: nothing to switch."""

    def reload(self) -> None:
        """An archived version never changes: nothing to read again."""

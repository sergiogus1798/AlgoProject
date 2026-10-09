"""How the window hops between zones: what a palette row, a card or a cell hands on and where it lands."""

from ui.desktop import projectflow as flow
from ui.desktop.selection import SELECTION


class Opens:
    """The `Shell` methods that open one zone from another; they use the shell's zones and status."""

    def go_to(self, item: dict) -> None:
        """Open what one palette row points at: by zone name and SELECTION, never by stack index.

        Args:
            item: A row as `cmdpalette.CmdPalette.gather` built it; `kind` says which.
        """
        kind, fields = item["kind"], {k: item[k] for k in ("project", "asset", "databank")
                                      if k in item}
        if kind == "zone":
            self.open_zone(item["label"])
        elif kind == "study":
            self.open_zone("Estrategia")
            self.estrategia.show_live()
            if self.ficha.page is not None:
                self.ficha.page.open_study(item["study"])
        elif kind == "strategy":
            SELECTION.choose(**fields, strategy=item["label"], identity=item["identity"])
            self.estrategia.show_live()
            self.open_zone("Estrategia")
        elif kind == "project":
            self.open_project(item["project"])
        else:
            SELECTION.choose(**fields)
            self.open_zone("Databanks" if kind == "databank" else "Proyecto")
            if kind == "databank":
                self.workspace.show_databank(item["databank"])

    def open_project(self, name: str) -> None:
        """A card or a palette row chose a project: select it, load it if confirmed, show it."""
        self.status.setText(self.gallery.choose(name))
        self.open_zone("Proyecto")

    def open_strategy(self, identity: str) -> None:
        """Databanks' panel chose a strategy by identity: select it and show its ficha."""
        said = flow.select_strategy(identity, flow.in_panel(self, identity))
        self.status.setText(said)
        if not said:
            self.estrategia.show_live()
            self.open_zone("Estrategia")

    def open_archived(self, identity: str, version: str) -> None:
        """PORTFOLIOS' «Importar»: the Estrategia page of one archived version, nothing run.

        Args:
            identity: The strategy's identity.
            version: The archived version; "" for the newest.
        """
        said = self.estrategia.show_archived(identity, version)
        self.status.setText(said)
        if not said:
            self.open_zone("Estrategia")

    def open_campaign(self, workflow: str, names: list, index: int) -> None:
        """PORTFOLIOS' «Campaña»: the Estrategia page on a saved workflow's strategy, walkable."""
        said = self.estrategia.show_campaign(workflow, names, index)
        self.status.setText(said)
        if not said:
            self.open_zone("Estrategia")

    def open_template(self, name: str) -> None:
        """Jump from a coverage cell to that template's page.

        Args:
            name: Template name.
        """
        self.open_zone("Plantillas")
        self.catalogue.select(name)

    def open_library(self, action: str, cell: dict) -> None:
        """Cobertura handed a family or a cell on to another page of the library.

        Args:
            action: `templates`, `palette`, `new`, `research` (`coverage.ACTIONS`) or `proposal`.
            cell: What `coverage.Matrix.choose` holds: `family`, `symbol`, `timeframe`,
                `template`; `{}` for `proposal`.
        """
        research = self.zones["Investigar"]
        if action == "templates":
            self.open_zone("Plantillas")
            self.catalogue.show_family(cell["family"])
            if cell["template"]:
                self.catalogue.select(cell["template"])
        elif action == "palette":
            self.open_zone("Paletas")
            self.palettes.show_family(cell["family"])
        elif action == "new":
            self.open_zone("Nueva plantilla")
            self.chat.start(cell["family"], " · ".join(
                x for x in (cell["symbol"], cell["timeframe"]) if x))
        elif action == "research":
            self.open_zone("Investigar")
            research.open_cell(cell["symbol"], cell["timeframe"])
        else:
            self.open_zone("Investigar")
            research.open_proposal()

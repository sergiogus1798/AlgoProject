"""Proyectos → Proyecto → Estrategia in the shell: the Estrategia zone (a live ficha, or an
archived version PORTFOLIOS imported), a strategy found by its identity, and the two zones kept
on the global selection."""

import httpx
from PySide6.QtWidgets import QStackedWidget, QWidget

from ui.desktop import client
from ui.desktop.portfolios.imported import ImportedFicha
from ui.desktop.selection import SELECTION
from ui.desktop.studypage.net import fetch
from ui.desktop.workspace import ficha as ficha_module
from ui.desktop.workspace.ficha import Ficha

# What Proyecto and Estrategia show now, so a zone is refilled only when SELECTION moved on.
SHOWN: dict[str, object] = {"Proyecto": None, "Estrategia": None}
# The databank panel tab a ficha opens from when the panel's own tab is not one it knows.
# It is the panel tab of step 8 (`daemon/workflow/steps.py`), not the retired zone.
FIRST_PANEL = "Puerta IS/OOS"


class StrategyZone(QStackedWidget):
    """The Estrategia zone: the live ficha, or one archived version read with `source=archive`.

    Opening a live strategy (the panel's double click, Ctrl+K, a refill on a new selection)
    shows the live ficha; PORTFOLIOS' «Importar» shows the archived one. SELECTION is never
    changed by an import: an archived strategy may belong to no project on any install.
    """

    def __init__(self) -> None:
        """Hold the live ficha; the archived page is built on the first import."""
        super().__init__()
        self.ficha = Ficha()
        self.imported: ImportedFicha | None = None
        self.addWidget(self.ficha)

    def show_live(self) -> None:
        """Put the live ficha on screen."""
        self.setCurrentWidget(self.ficha)

    def show_archived(self, identity: str, version: str) -> str:
        """Open one archived version on the imported page.

        Args:
            identity: The strategy's identity, as PORTFOLIOS emits it.
            version: The version folder; "" for the newest.

        Returns:
            "" when it opened; otherwise the sentence saying why not.
        """
        shown = fetch("archive/show", identity=identity, version=version)
        if "error" in shown:
            return shown["error"]
        if self.imported is None:
            self.imported = ImportedFicha()
            self.addWidget(self.imported)
        self.setCurrentWidget(self.imported)
        self.imported.open(shown)
        return ""


def origin(shell: QWidget) -> tuple[str, str]:
    """The databank panel's tab (and its open sub-panel) the ficha was opened from.

    Returns:
        (tab, sub) as `ficha.fill` and `fichaorigin.default_study` read them; sub is "" when
        the tab is not one `ORIGIN_FAMILY` knows, or before the panel has its tab row.
    """
    try:
        panel = shell.workspace.panel
        tab = panel.top.tabText(panel.top.currentIndex())
        sub = panel.sub.tabText(panel.sub.currentIndex())
    except AttributeError:                    # a panel without its tab row yet
        return FIRST_PANEL, ""
    return (tab, sub) if tab in ficha_module.ORIGIN_FAMILY else (FIRST_PANEL, "")


def catch_up(shell: QWidget, zone: str) -> None:
    """Refill Proyecto or Estrategia when SELECTION holds something they do not show yet.

    Args:
        shell: The `Shell`, holding `workspace` and `estrategia`.
        zone: The zone about to open; any other zone is left alone.
    """
    now = SELECTION.now
    if zone == "Proyecto" and now["project"] and SHOWN[zone] != now["project"]:
        shell.workspace.fill(now["project"])
        SHOWN[zone] = now["project"]
    wanted = (now["project"], now["databank"], now["strategy"])
    if zone == "Estrategia" and now["strategy"] and SHOWN[zone] != wanted:
        shell.estrategia.ficha.fill(now["project"], now["strategy"], *origin(shell))
        shell.estrategia.show_live()
        SHOWN[zone] = wanted


def in_panel(shell: QWidget, identity: str) -> tuple[str, str] | None:
    """The databank and name Proyecto's panel shows for one identity, or None."""
    panel = shell.workspace.panel
    row = next((r for r in panel.table.rows if r["identity"] == identity), None)
    bank = (panel.sub_spec() or {}).get("databank") if panel.tabs else None
    return (bank, row["name"]) if row and bank else None


def select_strategy(identity: str, shown: tuple[str, str] | None = None) -> str:
    """Make a strategy of the selected project the global selection, by its identity.

    Args:
        identity: The strategy's SHA-256 identity; its name and databank come from the
            daemon's rosters (`/api/projects/find`) and the hash itself is never shown.
        shown: (databank, name) as the databank panel shows the row. Its databank is the
            daemon's first place to look: one identity may sit in Results and OOS alike. Used
            as the answer when no install
            holds the strategy any more — a row the panel read from the cosecha and the
            reports (📓 2026-09-28: the custodian kept only WFM of the USDJPY project), which
            the ficha still reads by identity.

    Returns:
        "" when it was selected; otherwise the sentence saying why not.
    """
    now = SELECTION.now
    try:
        got = client.get("projects/find", project=now["project"] or "", identity=identity,
                         databank=(shown[0] if shown else now["databank"]) or "")
    except httpx.HTTPError as e:
        return f"El demonio no respondió: {e}"
    if "error" in got and shown:
        got = {"databank": shown[0], "name": shown[1]}
    if "error" in got:
        return got["error"]
    SELECTION.choose(databank=got["databank"], strategy=got["name"], identity=identity)
    return ""

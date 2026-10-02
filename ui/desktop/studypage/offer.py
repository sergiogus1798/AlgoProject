"""Tests with no result anywhere in the project: their tabs greyed or hidden, the reason said, and a jump to where they run."""

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPushButton, QTabBar

from ui.desktop import background
from ui.desktop.theme import T

if TYPE_CHECKING:
    from ui.desktop.studypage.page import StudyPage

# Said in the tab's own text: the theme's sheet sets every tab's colour, so a greyed text
# colour (`setTabTextColor`) never shows (2026-09-30).
OFF = " · sin datos"


def mark(bar: QTabBar, i: int, off: bool) -> None:
    """Add or drop the «sin datos» mark on one tab's text."""
    base = bar.tabText(i).removesuffix(OFF)
    bar.setTabText(i, base + OFF if off else base)


class Offer(QObject):
    """What `/api/study/offer` says of the strategy on screen, painted on the page's tabs.

    A study is off when the strategy has no stored result for it in ANY databank of the
    project (`page.cells`, from `/api/presence`: one entity across the project, owner
    2026-09-30) AND the runner refuses it in this databank. A study with a result elsewhere is
    never off: its result is shown, saying where it came from. An off tab stays clickable,
    marked «sin datos», when its own databank holds a strategy of the same name to run it on
    («→ abrir en …», a jump the owner chooses); with nowhere to run it either, it is hidden."""

    jump = Signal(str, dict)          # study key, `go` of `/api/study/offer`

    def __init__(self, page: "StudyPage") -> None:
        """Hold the page and the jump button, hidden.

        Args:
            page: The strategy's study page; `page.button` goes in its note row.
        """
        super().__init__(page)
        self.page = page
        self.refused: dict[str, dict] = {}
        self.found: set[str] = set()      # studies whose result this page did find elsewhere
        self.button = QPushButton("")
        self.button.setProperty("help", "Abre la estrategia del mismo nombre en el databank de "
                                "este test. Se empareja por nombre: allí su identidad puede ser "
                                "otra, y la ficha lo lee todo de ese databank.")
        self.button.clicked.connect(lambda: self.jump.emit(self.page.key, self.go))
        self.button.hide()
        self.go: dict = {}

    def ask(self) -> None:
        """Ask the daemon, off the GUI thread, for this place; the tabs repaint on arrival."""
        self.refused, self.found = {}, set()
        w = self.page.where
        if not (self.page.strategy_page and w["project"] and w["databank"] and w["strategy"]):
            return self.paint()
        background.get("study/offer", self.arrived, key=f"offer-{id(self)}", owner=self.page,
                       project=w["project"], databank=w["databank"], strategy=w["strategy"],
                       asset=w["asset"] or "")

    def arrived(self, got: dict) -> None:
        """Keep the answer (an error greys nothing) and repaint what is on screen."""
        self.refused = got.get("studies") or {}
        self.paint()
        self.page.prune()
        self.explain()

    def off(self, key: str) -> dict | None:
        """The refusal of a study with nothing stored anywhere, or None when it can be used."""
        return None if key in self.page.cells or key in self.found else self.refused.get(key)

    def hide(self, key: str) -> bool:
        """A tab to drop, not merely grey: no result anywhere in the project, refused here AND
        nowhere to jump to (owner, 2026-09-30 §1). Before the daemon answers `off` is always
        None, so nothing is hidden yet."""
        off = self.off(key)
        return bool(off) and "databank" not in off["go"]

    def paint(self) -> None:
        """Mark the study tabs that are off, and the family tabs whose every study is."""
        page = self.page
        for i in range(page.studies.count()):
            off = self.off(page.studies.tabData(i))
            mark(page.studies, i, bool(off))
            if off:
                page.studies.setTabToolTip(i, "Sin resultado en ningún databank del proyecto: "
                                              f"{off['why']}")
        families = {}
        for key, entry in page.catalogue.items():
            families.setdefault(entry["family"], []).append(key)
        for i in range(page.families.count()):
            keys = families.get(page.families.tabData(i))
            mark(page.families, i, bool(keys) and all(self.off(k) for k in keys))

    def first(self, keys: list[str]) -> str:
        """The study a family opens on: the first usable here, else the first."""
        return next((k for k in keys if not self.off(k)), keys[0])

    def explain(self) -> bool:
        """On an off study: say why, hide the run buttons and offer the jump.

        Returns:
            True when the study on screen is off here.
        """
        page, off = self.page, self.off(self.page.key)
        self.button.hide()
        page.note.setToolTip("")
        if page.studies.isHidden():           # the Ficha is on screen: no study to explain
            return False
        if off and page.view.stored is not None:
            # A result `/api/presence` had not seen yet (a run that just ended) is not «sin datos»
            self.found.add(page.key)
            self.paint()
            off = None
        page.bar.setVisible(not off)
        if not off:
            return False
        self.go = off["go"]
        where = (f"Su databank es {self.go['databank']} (pestaña {self.go['tab']} de "
                 "Databanks), que tiene una estrategia con este nombre."
                 if "databank" in self.go else self.go.get("absent", ""))
        # A line, not the runner's paragraph (owner, 2026-09-30): the reasons are on hover.
        page.note.setText(f'<span style="color:{T["muted"]}">Sin datos de este test en ningún '
                          "databank del proyecto.</span>")
        page.note.setToolTip(f"{off['why']}\n\n{where}".strip())
        if page.view.stored is None:          # «no ha corrido aquí» would promise a run
            why = off["why"].removeprefix(f"{page.key}: ").rstrip(".")   # the runner names the key
            page.view.empty(f"No se corre desde aquí: {why}.")
        if "databank" in self.go:
            self.button.setText(f"→ abrir en {self.go['tab']}")
            self.button.show()
        return True

"""The study page of one strategy, with its Ficha as the first tab — what the Estrategia zone embeds."""

from ui.desktop.studypage.ficha import Ficha
from ui.desktop.studypage.page import StudyPage

FICHA = "ficha"     # the family tab's data for the Ficha, which is no family of studies


class StrategyPage(StudyPage):
    """The study page of the strategy SELECTION holds, with the «Ficha» as its fixed first tab.
    On the Ficha the study widgets hide; any study tab or `open_study` brings them back."""

    def __init__(self) -> None:
        """Build it for scope one and open it on the Ficha."""
        self.ficha: Ficha | None = None      # the base's __init__ already follows SELECTION
        self.hold = False
        super().__init__(strategy_page=True)
        self.ficha = Ficha()
        lay = self.layout()
        lay.insertWidget(lay.indexOf(self.families) + 1, self.ficha, 1)
        self.families.blockSignals(True)
        self.families.insertTab(0, "Ficha")
        self.families.setTabData(0, FICHA)
        self.families.setTabToolTip(0, "Lo que dice la cosecha de esta estrategia, IS y OOS "
                                       "por separado. No es un estudio: no se corre desde aquí.")
        self.families.setCurrentIndex(0)
        self.families.blockSignals(False)
        self._family(0)

    def on_ficha(self) -> bool:
        """Whether the Ficha is the tab on screen."""
        return self.ficha is not None and self.families.tabData(
            self.families.currentIndex()) == FICHA

    def _mode(self, ficha: bool) -> None:
        """Show the Ficha or the study widgets, never both."""
        self.ficha.setVisible(ficha)
        for w in (self.studies, self.head, self.bar, self.note, self.view.parentWidget()):
            w.setVisible(not ficha)
        if ficha:
            for w in (self.back, self.skipped):
                w.hide()

    def _family(self, index: int) -> None:
        """A family tab was chosen; the Ficha's is handled here, the rest by the base.

        Args:
            index: The tab's position.
        """
        if self.ficha is None:
            return super()._family(index)
        on = self.families.tabData(index) == FICHA
        self._mode(on)
        if on:
            return self.ficha.load(self.where)
        super()._family(index)

    def follow(self, now: dict) -> None:
        """Take a new selection; on the Ficha, refill it and leave the study tabs be.

        Args:
            now: SELECTION's fields.
        """
        if not self.on_ficha():
            return super().follow(now)
        self.hold = True
        super().follow(now)
        self.hold = False
        self.ficha.load(self.where)

    def open_family(self, name: str) -> None:
        """Show one family tab by the name it shows (Estrategia opens on its origin's family).

        Args:
            name: «Ficha», «Cribado», «Transferencia»…; a name with no tab leaves the bar be.
        """
        for i in range(self.families.count()):
            if self.families.tabText(i) == name:
                self.families.setCurrentIndex(i)
                return

    def open_study(self, key: str) -> None:
        """Show one study, leaving the Ficha — except while a selection is being followed, or
        when the daemon did not answer the catalogue (its error is on the page already).

        Args:
            key: Study key.
        """
        if self.hold or key not in self.catalogue:
            self.key = key
            return
        super().open_study(key)

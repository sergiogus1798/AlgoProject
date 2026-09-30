"""«Lote» beside the drawer: the mother's variant batch, only while the WFC study is open."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.desktop.studypage.page import StudyPage


def show(page: "StudyPage") -> None:
    """Add, show or hide the batch tab for the study and strategy `page` has on screen.

    Args:
        page: A `StudyPage`; `page.lote` holds the tab once built, None until then. Left off
            the Ficha (owner, 2026-09-29): a strategy can have no batch.
    """
    from ui.desktop.batchview.tab import BatchTab, has_batch
    w = page.where
    show_it = bool(page.strategy_page and page.key == "wfc" and w.get("project")
                   and w.get("strategy") and has_batch(w["project"], w["strategy"]))
    if show_it and page.lote is None:
        page.lote = BatchTab()
        page.side.addTab(page.lote, "Lote")
    if page.lote is None:
        return
    page.side.setTabVisible(page.side.indexOf(page.lote), show_it)
    page.toggles.sync()
    if show_it:
        page.lote.load(w["project"], w["strategy"])

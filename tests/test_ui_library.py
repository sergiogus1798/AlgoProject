"""The library offscreen over the daemon in-process: one names table, Cobertura's links, the lazy zones."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from sqx import tasklog  # noqa: E402
from ui.daemon.app import APP  # noqa: E402
from ui.daemon.coverage import ARCHETYPES  # noqa: E402
from ui.desktop import client, names  # noqa: E402
from ui.desktop.nav import GROUPS, LIBRARY, ZONES  # noqa: E402
from ui.desktop.shell import Shell  # noqa: E402

QAPP = QApplication.instance() or QApplication([])
HTTP = TestClient(APP)
client.get = lambda path, **params: HTTP.get(f"/api/{path}", params=params).json()
client.post = lambda path, body: HTTP.post(f"/api/{path}", json=body).json()
tasklog.status = lambda role, project: None  # the one call that could reach an install
SHELL = Shell()


def on_screen() -> str:
    """The zone the stack shows, by name."""
    return next(n for n in ZONES if SHELL.zones[n] is SHELL.stack.currentWidget())


def test_every_spelling_shows_one_name() -> None:
    """Registry, taxonomy, research and Spanish spellings of a family all show the same words."""
    for spellings, shown in (
        (
            ("meanReversion", "mean_reversion", "reversion", "Reversión a la media"),
            "Mean reversion",
        ),
        (("trendFollowing", "trend", "tendencia", "Tendencia"), "Trend following"),
        (("breakout", "ruptura", "Ruptura"), "Breakout"),
    ):
        assert {names.family(s) for s in spellings} == {shown}
    assert [names.spelt(a, names.REGISTRY) for a in ARCHETYPES] == list(ARCHETYPES)
    assert names.family("free") == "Free" and names.family("") == "Sin familia"
    assert names.palette("Reversión a la media — base") == "Mean reversion — base"
    assert (
        names.palette("Pullback — tendencia + reversión")
        == "Pullback — trend following + mean reversion"
    )


def test_sidebar_holds_the_front_page_only() -> None:
    """The five pages are zones; one has a sidebar button; MT5 Bridge sits before Portfolios."""
    assert set(LIBRARY) <= set(ZONES) and ZONES[0] == "Cobertura"
    assert [n for n in LIBRARY if n in SHELL.nav] == ["Cobertura"]
    assert [g for g, _ in GROUPS][-2:] == ["MT5 Bridge", "Portfolios"]


def test_zones_load_when_first_opened() -> None:
    """Nothing but the front page is read before the window shows; «Recargar» marks them again."""
    assert (
        SHELL.coverage.data
        and "Activos" in SHELL.stale
        and not SHELL.palettes.data["palettes"]
    )
    SHELL.open_zone("Paletas")
    assert "Paletas" not in SHELL.stale and SHELL.palettes.data["palettes"]
    SHELL.refresh()
    assert (
        "Plantillas" in SHELL.stale and "Paletas" not in SHELL.stale
    )  # the open one was re-read


def test_a_family_leads_to_its_templates() -> None:
    """Clicking a family's name opens Plantillas with only that family's templates."""
    SHELL.open_zone("Cobertura")
    # Whichever family the library holds today: `breakout` went empty on 2026-10-05.
    family = client.get("templates")["templates"][0]["archetype"]
    SHELL.coverage.on_row(SHELL.coverage.data["rows"].index(family))
    assert (
        on_screen() == "Plantillas" and SHELL.catalogue.family.currentData() == family
    )
    listed = [
        SHELL.catalogue.list.item(i).data(Qt.UserRole)
        for i in range(SHELL.catalogue.list.count())
    ]
    by_name = {t["name"]: t for t in SHELL.catalogue.data["templates"]}
    assert listed and all(by_name[n]["archetype"] == family for n in listed)
    assert SHELL.nav["Cobertura"].isChecked() and SHELL.library.isVisibleTo(SHELL)
    assert SHELL.library.currentIndex() == LIBRARY.index("Plantillas")


def test_a_cell_leads_to_palette_chat_and_research() -> None:
    """The four buttons of a chosen cell open the other pages on that cell's family."""
    cover = SHELL.coverage
    SHELL.open_zone("Cobertura")
    cover.on_click(
        cover.data["rows"].index("trendFollowing"), cover.data["columns"].index("H4")
    )
    assert cover.cell["family"] == "trendFollowing" and cover.cell["timeframe"] == "H4"
    cover.act("palette")
    assert (
        on_screen() == "Paletas"
        and SHELL.palettes.entry()["palette"]["family"] == "trend"
    )
    cover.act("new")
    assert on_screen() == "Nueva plantilla" and SHELL.chat.answers == {
        "archetype": "trendFollowing"
    }
    cover.act("research")
    research = SHELL.zones["Investigar"]
    assert on_screen() == "Investigar" and research.tabs.currentWidget() is research.map
    cover.go.emit("proposal", {})
    assert research.tabs.currentWidget() is research.proposal


def test_the_strip_and_a_plain_zone() -> None:
    """A tab of the strip opens its page; a zone outside the library hides the strip."""
    SHELL.open_zone("Cobertura")
    SHELL.library.setCurrentIndex(LIBRARY.index("Investigar"))
    assert on_screen() == "Investigar"
    SHELL.open_zone("Datos")
    assert SHELL.library.isHidden() and SHELL.nav["Datos"].isChecked()
    assert not SHELL.nav["Cobertura"].isChecked()

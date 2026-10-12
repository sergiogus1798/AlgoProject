"""PORTFOLIOS › Campaña over the daemon in-process, on a saved workflow of AlgoData/campaign: the list,
the funnel, a finalist opened on Estrategia from the archive (the mother's, labelled), its extra results
(steps 17-24) and «anterior / siguiente» walking the series. Nothing is computed."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.daemon.app import APP  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.portfolios.campaign import CampaignPage  # noqa: E402
from ui.desktop.projectflow import StrategyZone  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

HTTP = TestClient(APP)


def get(path: str, **params: str) -> dict:
    """client.get over the in-process app."""
    return HTTP.get(f"/api/{path}", params=params).json()


def wait(app: QApplication, seconds: float = 3.0) -> None:
    """Let the background reads land."""
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)


def main() -> None:
    """Run the checks; skip when the machine has no saved workflow."""
    client.get = get
    listed = get("campaign/list")["workflows"]
    if not listed:
        return print("ok (sin workflows guardados: nada que abrir)")
    # The newest saved workflow is whatever the loop ran last — interrupted, failed or with no
    # survivor (2026-10-06) — so the one opened is the newest that has finalists to open.
    name = next((w["name"] for w in listed if w["finalists"]), None)
    if not name:
        return print("ok (ningún workflow guardado tiene finalistas: nada que abrir)")
    shown = get("campaign/show", workflow=name)
    assert shown["strategies"] and shown["steps"], "workflow sin estrategias o sin pasos"
    first = shown["strategies"][0]
    opened = get("campaign/open", workflow=name, strategy=first["name"])
    assert opened["label"] == first["name"] and (not opened["banner"] or "madre" in opened["banner"]), opened.get("error")
    assert {e["step"] for e in opened["extras"]} >= {"19", "20"}, "faltan los pasos 19-20 de la madre"
    got = get("campaign/extra", workflow=name, key=opened["extras"][0]["key"])
    assert got["result"]["tabs"], "el extra no es un resultado dibujable"
    assert "error" in get("campaign/extra", workflow=name, key="../../../etc/passwd")
    assert "error" in get("campaign/show", workflow="nope")

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(QSS)
    page = CampaignPage(get)
    page.reload()
    assert page.table.rowCount() == len(listed)
    page.find.setText("zzz")
    assert page.table.rowCount() == 0
    page.find.setText(shown["symbol"].lower())
    assert page.table.rowCount() >= 1
    page.table.selectRow([r["name"] for r in page.shown].index(name))
    asked = []
    page.campaign_requested.connect(lambda *a: asked.append(a))
    page.strats.selectRow(1)
    page._open()
    assert asked[0][2] == 1 and len(asked[0][1]) == len(shown["strategies"])

    stack = StrategyZone()
    assert stack.show_campaign(name, asked[0][1], 1) == ""
    ficha = stack.imported
    wait(app)
    assert ficha.title.text() == asked[0][1][1] and ficha.series.index == 1
    labels = [ficha.frozen.menu.item(i).text() for i in range(ficha.frozen.menu.count())]
    assert any("paso 19" in t for t in labels), labels
    ficha.series.next.click()
    assert ficha.series.index == 2 and ficha.title.text() == asked[0][1][2]
    ficha.series.prev.click()
    assert ficha.series.index == 1
    ficha.resize(2200, 1300)
    ficha.show()
    wait(app)
    shot = os.environ.get("CAMPAIGN_SHOT")
    if shot:
        ficha.grab().save(shot)
    print("ok")


main()

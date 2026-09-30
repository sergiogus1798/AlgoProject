#!/usr/bin/env python3
"""The tear sheet's market routes in-process on a real harvest, and the trade gallery drawn offscreen."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pyarrow.parquet as pq  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.paths import DATA, ROOT  # noqa: E402
from core.study.blocks import validate  # noqa: E402
from ui.daemon.tearmarket.api import ROUTER  # noqa: E402
from ui.desktop.blocks.result import ResultView  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402
from ui.desktop.tradegallery import TradeGallery  # noqa: E402

# The USDJPY Donchian project's newest cosecha — the one the route reads. It was pinned to 09-27,
# and the cosecha of 2026-09-29 (Results cut to 21) no longer held those identities.
PROJECT, DATABANK = "Test_USDJPY_donchianUpperCrossUp_M30", "Results"
HARVEST = max(d for d in (DATA / "harvest" / PROJECT / DATABANK).iterdir()
              if (d / "metrics.parquet").exists())
XAU = "XAU_ISOOS_ejemplo"            # a project whose name holds no asset symbol
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"


def serve() -> TestClient:
    """A local app with only this router: no daemon, no port.

    Returns:
        The test client.
    """
    app = FastAPI()
    app.include_router(ROUTER)
    return TestClient(app)


def identities(n: int, harvest: Path = HARVEST) -> list[str]:
    """The first identities of a harvest's metrics.

    Args:
        n: How many.
        harvest: The harvest folder.

    Returns:
        Identities in file order.
    """
    return pq.read_table(harvest / "metrics.parquet", columns=["identity"]).column(0).to_pylist()[:n]


def test_market(http: TestClient) -> None:
    """Cells + flat + no-market = months, per sample, on five strategies; both-down in watch."""
    for ident in identities(5):
        r = http.get("/api/tearsheet/market",
                     params={"project": PROJECT, "databank": DATABANK, "identity": ident}).json()
        assert "error" not in r, r
        validate(r)
        assert [t["name"] for t in r["tabs"]] == ["IS", "OOS"]
        for sample, n in r["summary"]["counts"].items():
            cells = n["both_up"] + n["up_down"] + n["down_up"] + n["both_down"]
            assert cells + n["flat"] + n["no_market"] == n["months"] > 0, (sample, n)
        bars = r["tabs"][0]["blocks"][1]["items"]
        assert [i["state"] for i in bars][:4] == ["info", "info", "info", "watch"], bars


def test_refusals(http: TestClient) -> None:
    """Unknown asset, no asset in the name, a foreign sample, no harvest, an identity elsewhere."""
    ident = identities(1)[0]
    base = {"project": PROJECT, "databank": DATABANK, "identity": ident}
    cases = [("/api/tearsheet/market", {**base, "asset": "NOPE"}, "No conozco el activo"),
             ("/api/tearsheet/trades", {**base, "sample": "oos2"}, "solo IS u OOS"),
             ("/api/tearsheet/market", {**base, "databank": "Nada"}, "no tiene cosecha"),
             ("/api/tearsheet/trades", {**base, "identity": "0" * 64}, "no está en la cosecha"),
             ("/api/tearsheet/trades", {**base, "project": "../x"}, "Nombre no válido")]
    xau = DATA / "harvest" / XAU / DATABANK
    if xau.is_dir():
        cases.append(("/api/tearsheet/market", {**base, "project": XAU, "identity": identities(
            1, max(xau.iterdir()))[0]}, "No sé qué activo"))
    else:
        print(f"    (sin la cosecha {XAU}/{DATABANK}: no se comprueba el proyecto cuyo nombre "
              "no dice su activo; hace falta una cosecha de un proyecto así)")
    for path, params, words in cases:
        r = http.get(path, params=params)
        assert r.status_code == 200 and words in r.json().get("error", ""), (params, r.json())
    r = http.get("/api/tearsheet/trades", params={**base, "asset": "NOPE"}).json()
    assert r["bars_note"] and all("missing" in t["bars"] for t in r["tiles"]), r["bars_note"]


def test_trades(http: TestClient) -> None:
    """Quantile picks deterministic and ordered by P&L; a seed redraws the same five; no oos2 bar."""
    base = {"project": PROJECT, "databank": DATABANK, "identity": identities(1)[0]}
    for sample in ("IS", "OOS"):
        a = http.get("/api/tearsheet/trades", params={**base, "sample": sample}).json()
        b = http.get("/api/tearsheet/trades", params={**base, "sample": sample}).json()
        assert [t["row"] for t in a["tiles"]] == [t["row"] for t in b["tiles"]]
        pnl = [t["pnl"] for t in a["tiles"]]
        assert len(pnl) == 5 and pnl == sorted(pnl), pnl
        assert a["seed"] is None
        for t in a["tiles"]:
            w = t["bars"]
            assert w["t"][w["entry"]] <= t["open_time"] and w["t"][w["exit"]] <= t["close_time"]
            assert w["held"] == w["exit"] - w["entry"] and w["t"][-1] < "2023-01-01", w["t"][-1]
    r1 = http.get("/api/tearsheet/trades", params={**base, "pick": "random"}).json()
    r2 = http.get("/api/tearsheet/trades",
                  params={**base, "pick": "random", "seed": str(r1["seed"])}).json()
    assert r1["seed"] == r2["seed"] and [t["row"] for t in r1["tiles"]] == [t["row"] for t in r2["tiles"]]


def test_draw(app: QApplication, http: TestClient) -> None:
    """The gallery and the market result drawn offscreen, grabbed for a person to look at."""
    def fetch(path: str, **params: str) -> dict:
        """The gallery's daemon call, answered in-process."""
        return http.get(f"/api/{path}", params=params).json()

    SHOTS.mkdir(parents=True, exist_ok=True)
    ident = identities(1)[0]
    g = TradeGallery(fetch)
    g.resize(1500, 1900)
    g.load(PROJECT, DATABANK, ident, "OOS")
    app.processEvents()
    assert g.body.count() == 6 and "5 de" in g.head.text(), g.head.text()
    g.grab().save(str(SHOTS / "H2-gallery-quantiles.png"))
    g.other.click()
    app.processEvents()
    assert g.seed and g.seed in g.seed_label.text()
    g.grab().save(str(SHOTS / "H2-gallery-random.png"))
    g.load(PROJECT, DATABANK, ident, "IS", asset="NOPE")
    app.processEvents()
    g.grab().save(str(SHOTS / "H2-gallery-nobars.png"))
    view = ResultView()
    view.resize(1300, 900)
    view.show_result(fetch("tearsheet/market", project=PROJECT, databank=DATABANK, identity=ident), None)
    app.processEvents()
    view.grab().save(str(SHOTS / "H2-market.png"))


if __name__ == "__main__":
    APP = QApplication.instance() or QApplication([])
    APP.setStyleSheet(QSS)
    HTTP = serve()
    for test, args in ((test_market, (HTTP,)), (test_refusals, (HTTP,)), (test_trades, (HTTP,)),
                       (test_draw, (APP, HTTP))):
        started = time.time()
        test(*args)
        print(f"ok  {test.__name__}  {time.time() - started:.1f} s")

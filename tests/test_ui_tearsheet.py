"""The Ficha: its two routes on the real cosecha and on synthetic ones, and its drawing offscreen."""

import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from core.paths import DATA, ROOT  # noqa: E402
from ui.daemon import jobsapi  # noqa: E402
from ui.daemon.results import api as results  # noqa: E402
from ui.daemon.runner import api as runner  # noqa: E402
from ui.daemon.tearsheet import api as tearsheet, harvest  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.selection import SELECTION  # noqa: E402
from ui.desktop.studypage.views import StrategyPage  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

# The USDJPY Donchian project's newest cosecha, the one the routes read (2026-09-29: Results cut
# to 21; the 5.16.75 pinned before went with the other 178). Strategy 13.14.82 is among the 21
# and has a spread report, so its P&L carries the real curve.
PROJECT, DATABANK, STRATEGY = ("Test_USDJPY_donchianUpperCrossUp_M30", "Results",
                               "Strategy 13.14.82")
IDENTITY = "47da0743d600c27cedda1f78cc30de3ebd4935f6624d8ffbf4e9cc0e0e6140dd"
FOLDER = max(d for d in (DATA / "harvest" / PROJECT / DATABANK).iterdir()
             if (d / "metrics.parquet").exists())
DAY = FOLDER.name
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"


def serve() -> TestClient:
    """The Ficha's router plus what the strategy page reads, in-process; never port 8765."""
    app = FastAPI()
    for r in (tearsheet.ROUTER, results.ROUTER, runner.ROUTER, jobsapi.ROUTER):
        app.include_router(r)
    http = TestClient(app)

    def get(path: str, **params: str) -> dict:
        """client.get over the in-process app."""
        got = http.get(f"/api/{path}", params=params)
        got.raise_for_status()
        return got.json()

    client.get = get
    return http


def ask(http: TestClient, route: str, **where: str) -> dict:
    """One Ficha route for the test strategy, unless told otherwise."""
    params = {"project": PROJECT, "databank": DATABANK, "identity": IDENTITY, **where}
    return http.get(f"/api/{route}", params=params).json()


def own(sample: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The strategy's rows of one sample, read here and not through the daemon."""
    where = [("identity", "==", IDENTITY)]
    e = pd.read_parquet(FOLDER / "equity.parquet", filters=where)
    t = pd.read_parquet(FOLDER / "trades.parquet", filters=where)
    return (e[e["sample"] == sample].sort_values("day"),
            t[t["sample"].astype(str) == sample])


def block(result: dict, sample: str, title: str) -> dict:
    """One block of one sample's tab, by title."""
    tab = next(t for t in result["tabs"] if t["name"] == sample)
    return next(b for b in tab["blocks"] if b["title"] == title)


def test_sheet(http: TestClient) -> None:
    """IS and OOS apart, years summing to the curve, the real and the top-less curves, < 1 s warm."""
    ask(http, "tearsheet")
    started = time.time()
    got = ask(http, "tearsheet")
    warm = time.time() - started
    assert warm < 1.0, warm
    assert [t["name"] for t in got["tabs"]] == ["IS", "OOS"] and got["harvest_day"] == DAY
    cut = ask(http, "tearsheet", top="5", dd="$")
    for s in ("IS", "OOS"):
        equity, _ = own(s)
        assert [b["title"] for b in next(t for t in got["tabs"] if t["name"] == s)["blocks"]] == [
            "P&L acumulado", "Drawdown", "P&L por año"], s
        years = block(got, s, "P&L por año")
        assert abs(sum(i["value"] for i in years["items"]) - float(equity["equity"].iloc[-1])) < 0.05
        curve = block(got, s, "P&L acumulado")
        assert curve["x"][0] == f"{equity['day'].iloc[0]:%Y-%m-%d}", s   # nothing of the other
        assert [x["ink"] for x in curve["series"]] == [f"sqx.{s}", f"real.{s}"], s
        assert round(curve["series"][0]["values"][-1], 2) == round(float(equity["equity"].iloc[-1]), 2)
        assert len(block(cut, s, "P&L acumulado")["series"]) == 4, s
        assert block(got, s, "Drawdown")["unit"] == "%" and block(cut, s, "Drawdown")["unit"] == "$"
    assert "error" in ask(http, "tearsheet", dd="€")
    print(f"    tearsheet warm {warm:.2f} s")


def test_exits(http: TestClient) -> None:
    """Exit rows add up to the sample's trades and P&L, types spelled as exported."""
    got = ask(http, "tearsheet/exits")
    for s in ("IS", "OOS"):
        _, trades = own(s)
        rows = block(got, s, "Resultado por tipo de salida")
        assert sum(r[1] for r in rows["rows"]) == len(trades), s
        assert round(sum(r[2] for r in rows["rows"]), 2) == round(trades["Profit/Loss"].sum(), 2)
        assert {r[0] for r in rows["rows"]} == set(trades["Close type"].astype(str)), s


def synthetic(root: Path, samples: tuple[str, ...], exits: tuple[str, ...]) -> None:
    """A one-strategy cosecha under `root`, with the samples and exit types asked for."""
    folder = root / "harvest" / "Test_P" / "Bank" / "2026-01-01"
    folder.mkdir(parents=True, exist_ok=True)
    days = pd.date_range("2020-01-01", periods=60, freq="D")
    pd.DataFrame({"strategy": ["S"]}, index=pd.Index(["x"], name="identity")).to_parquet(
        folder / "metrics.parquet")
    pd.concat([pd.DataFrame({"day": days, "identity": "x", "equity": range(60), "sample": s})
               for s in samples]).to_parquet(folder / "equity.parquet")
    n = 6
    pd.concat([pd.DataFrame({
        "Open time": days[:n], "Close time": days[1:n + 1], "Profit/Loss": [10.0, -5.0] * 3,
        "Balance": 100000.0, "Close type": [exits[k % len(exits)] for k in range(n)],
        "MAE ($)": -1.0, "MFE ($)": 1.0, "Size": 1.0, "identity": "x", "sample": s})
        for s in samples]
    ).to_parquet(folder / "trades.parquet")


def test_refusals(http: TestClient) -> None:
    """A sample outside IS/OOS is refused; no cosecha names its command; one exit type is said."""
    real = harvest.DATA
    with tempfile.TemporaryDirectory(prefix="ui-tearsheet-") as tmp:
        harvest.DATA = Path(tmp)
        where = {"project": "Test_P", "databank": "Bank", "identity": "x"}
        assert "studies.screening.gate.harvest" in ask(http, "tearsheet", **where)["error"]
        synthetic(Path(tmp), ("IS", "OOS2"), ("Stop loss",))
        for route in ("tearsheet", "tearsheet/exits"):
            assert "OOS2" in ask(http, route, **where).get("error", ""), route
        synthetic(Path(tmp), ("IS", "OOS"), ("Stop loss",))
        got = ask(http, "tearsheet/exits", **where)
        assert "un solo tipo: «Stop loss»" in block(got, "IS", "Resultado por tipo de salida")["note"]
    harvest.DATA = real
    assert "no está en la cosecha" in ask(http, "tearsheet", identity="nada")["error"]


def shot(widget: object, name: str) -> None:
    """Save a grab for a person to look at."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    widget.grab().save(str(SHOTS / f"H1-{name}.png"))


def test_draw(app: QApplication) -> None:
    """The strategy page opens on the Ficha, draws IS beside OOS, then again with its switches."""
    SELECTION.choose(project=PROJECT, databank=DATABANK, strategy=STRATEGY, identity=IDENTITY,
                     asset=None)
    page = StrategyPage()
    page.resize(1600, 1400)
    assert page.on_ficha() and page.ficha.isVisibleTo(page) and not page.bar.isVisibleTo(page)
    view = page.ficha.subs[0].body
    assert len(view.results) == 2, page.ficha.subs[0].line.text()
    assert DAY in page.ficha.note.text(), page.ficha.note.text()
    app.processEvents()
    shot(page, "ficha")
    view.scroll.verticalScrollBar().setValue(1400)
    shot(page, "ficha-scrolled")
    view.scroll.verticalScrollBar().setValue(3200)
    shot(page, "ficha-bottom")
    assert [page.ficha.tabs.tabText(k) for k in range(page.ficha.tabs.count())] == ["IS/OOS"]
    page.ficha.top.setChecked(True)                  # the P&L asked again without its best 5 %
    page.ficha.dd.button(1).click()                  # and the drawdown in $
    app.processEvents()
    pnl = [b for b in view.results[0]["tabs"][0]["blocks"] if b["title"] == "P&L acumulado"][0]
    assert len(pnl["series"]) == 4, [x["label"] for x in pnl["series"]]
    shot(page, "ficha-top")
    page.open_study("gate")                  # a study leaves the Ficha and brings the run bar
    assert not page.on_ficha() and page.bar.isVisibleTo(page) and page.view.results
    assert not page.ficha.isVisibleTo(page)
    page.families.setCurrentIndex(0)
    assert page.on_ficha() and not page.bar.isVisibleTo(page)
    page.deleteLater()


if __name__ == "__main__":
    APP = QApplication.instance() or QApplication([])
    APP.setStyleSheet(QSS)
    HTTP = serve()
    for test, args in ((test_sheet, (HTTP,)), (test_exits, (HTTP,)), (test_refusals, (HTTP,)),
                       (test_draw, (APP,))):
        started = time.time()
        test(*args)
        print(f"ok  {test.__name__}  {time.time() - started:.1f} s")

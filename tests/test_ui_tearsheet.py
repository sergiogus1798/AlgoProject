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
from ui.daemon import studyapi  # noqa: E402
from ui.daemon.batch import api as batch  # noqa: E402
from ui.daemon.results import api as results  # noqa: E402
from ui.daemon.runner import api as runner  # noqa: E402
from ui.daemon.tearsheet import api as tearsheet, harvest  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.selection import SELECTION  # noqa: E402
from ui.desktop.studypage.views import StrategyPage  # noqa: E402
from ui.desktop.theme import QSS  # noqa: E402

PROJECT, DATABANK, STRATEGY = "USDJPY_workflow_profiling_v1", "Results", "Strategy 1.23.51"
IDENTITY = "0b91ad2b2354a2fdab752e3f500968b1de2b1981cc6d961b4fd680038a2bcce7"
FOLDER = DATA / "harvest" / PROJECT / DATABANK / "2026-09-26"
# Deepest IS episode of Strategy 1.23.51, read off the parquet by hand (2026-09-26): last day
# at the peak, lowest close, first close back at the peak, and the two spans in days.
EPISODE = [-9584.84, "2011-04-07", "2011-11-30", "2012-04-02", 361, 124]
SHOTS = ROOT / "scratch" / "ui-plan" / "shots"


def serve() -> TestClient:
    """The Ficha's router plus what the strategy page reads, in-process; never port 8765."""
    app = FastAPI()
    for r in (tearsheet.ROUTER, results.ROUTER, runner.ROUTER, studyapi.ROUTER, batch.ROUTER):
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
    """IS and OOS apart, months summing to the curve to the cent, episodes as by hand, < 1 s warm."""
    ask(http, "tearsheet")
    started = time.time()
    got = ask(http, "tearsheet")
    warm = time.time() - started
    assert warm < 1.0, warm
    assert [t["name"] for t in got["tabs"]] == ["IS", "OOS"] and got["harvest_day"] == "2026-09-26"
    for s in ("IS", "OOS"):
        equity, _ = own(s)
        grid = block(got, s, "P&L por mes")
        cells = sum(v for row in grid["values"] for v in row if v is not None)
        assert round(cells, 2) == round(float(equity["equity"].iloc[-1]), 2), (s, cells)
        curve = block(got, s, "P&L acumulado")
        assert curve["x"][0] == f"{equity['day'].iloc[0]:%Y-%m-%d}", s   # nothing of the other
        assert len(curve["x"]) == len(equity), s
    deepest = block(got, "IS", "Los 5 episodios de drawdown más profundos")["rows"][0]
    assert [round(deepest[0], 2)] + deepest[1:] == EPISODE, deepest
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
        "MAE ($)": -1.0, "MFE ($)": 1.0, "identity": "x", "sample": s}) for s in samples]
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
    """The strategy page opens on the Ficha, draws IS beside OOS, then its other sub-tabs."""
    SELECTION.choose(project=PROJECT, databank=DATABANK, strategy=STRATEGY, identity=IDENTITY,
                     asset=None)
    page = StrategyPage()
    page.resize(1600, 1400)
    assert page.on_ficha() and page.ficha.isVisibleTo(page) and not page.bar.isVisibleTo(page)
    view = page.ficha.subs[0].body
    assert len(view.results) == 2, page.ficha.subs[0].line.text()
    assert "2026-09-26" in page.ficha.note.text(), page.ficha.note.text()
    app.processEvents()
    shot(page, "ficha")
    view.scroll.verticalScrollBar().setValue(1400)
    shot(page, "ficha-scrolled")
    view.scroll.verticalScrollBar().setValue(3200)
    shot(page, "ficha-bottom")
    for k, name in ((1, "salidas"), (2, "subyacente"), (3, "operaciones")):
        page.ficha.tabs.setCurrentIndex(k)
        app.processEvents()
        assert k in page.ficha.done
        shot(page, name)
    page.open_study("gate")                  # a study leaves the Ficha and brings the run bar
    assert not page.on_ficha() and page.bar.isVisibleTo(page) and page.view.results
    assert not page.ficha.isVisibleTo(page)
    page.families.setCurrentIndex(0)
    assert page.on_ficha() and not page.bar.isVisibleTo(page)
    page.deleteLater()


def test_lote(http: TestClient) -> None:
    """«Lote» shows for a mother with a batch folder (drawn, or the sentence of a batch not yet
    harvested) and stays hidden for a strategy without one."""
    from ui.desktop.studypage.ficha import LOTE, Ficha
    names = {s["strategy"]: s["identity"] for s in ask(http, "matrix", project=PROJECT,
                                                         databank=DATABANK)["strategies"]}
    ficha = Ficha()
    for name, shown in (("Strategy 1.28.59", True), ("Strategy 1.23.51", True),
                        ("Strategy 21.8.70", False)):
        ficha.load({"project": PROJECT, "databank": DATABANK, "strategy": name,
                    "identity": names[name], "asset": "USDJPY"})
        assert ficha.tabs.isTabVisible(LOTE) == shown, name
    ficha.load({"project": PROJECT, "databank": DATABANK, "strategy": "Strategy 1.28.59",
                "identity": names["Strategy 1.28.59"], "asset": "USDJPY"})
    ficha.tabs.setCurrentIndex(LOTE)
    ficha.resize(1400, 900)
    shot(ficha, "lead-ficha-lote")


if __name__ == "__main__":
    APP = QApplication.instance() or QApplication([])
    APP.setStyleSheet(QSS)
    HTTP = serve()
    for test, args in ((test_sheet, (HTTP,)), (test_exits, (HTTP,)), (test_refusals, (HTTP,)),
                       (test_draw, (APP,)), (test_lote, (HTTP,))):
        started = time.time()
        test(*args)
        print(f"ok  {test.__name__}  {time.time() - started:.1f} s")

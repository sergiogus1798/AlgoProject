"""The databank table's metric chooser: hide, add, «–» and why, kept per databank as a diff, restore."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.daemon.databank import columns as store  # noqa: E402
from ui.daemon.databank import segments  # noqa: E402
from ui.daemon.filters import discards  # noqa: E402
from ui.desktop import client  # noqa: E402
from ui.desktop.workspace import columns  # noqa: E402
from ui.desktop.workspace.columnsmenu import ColumnsMenu  # noqa: E402
from ui.desktop.workspace.columnsview import WIDE  # noqa: E402
from ui.desktop.theme import C  # noqa: E402
from ui.desktop.workspace.panel import Panel  # noqa: E402

P = "Test_UiColumns"
DASH = "–"
TABS = {"tabs": [{"tab": "Puerta", "subs": [
    {"sub": "Build", "databank": "Results", "studies": ["*"], "split": None, "blocked": None},
    {"sub": "Cribas", "databank": "Results", "studies": ["gate"], "split": None,
     "blocked": None}]},
    {"tab": "SPP", "subs": [
        {"sub": "IS", "databank": "SPP IS", "studies": ["spp"], "split": None,
         "blocked": None}]}]}
COLS = [{"key": "name", "kind": "name"},
        {"key": "Net profit (IS)", "kind": "metric", "metric": "Net profit", "sample": "IS"},
        {"key": "Sharpe Ratio (IS)", "kind": "metric", "metric": "Sharpe Ratio", "sample": "IS"},
        {"key": "Net profit (OOS)", "kind": "metric", "metric": "Net profit", "sample": "OOS"},
        {"key": "Stability (IS)", "kind": "metric", "metric": "Stability", "sample": "IS"},
        {"key": "gate.verdict", "kind": "study", "study": "gate", "sub": "", "field": "verdict",
         "title": "Puerta"},
        {"key": "spp.verdict", "kind": "study", "study": "spp", "sub": "", "field": "verdict",
         "title": "SPP"}]


def payload(n: int, judged: int) -> dict:
    """A databank of n rows; the first `judged` carry the gate's verdict and the spp's."""
    return {"columns": COLS, "rows": [
        {"identity": f"id{i}", "name": f"S{i}",
         "values": [f"S{i}", 100.0 * i, i / 10, -5.0 * i, 0.9,
                    "pasa" if i < judged else None, "pasa" if i < judged else None],
         "states": {"gate.verdict": "pass"} if i < judged else {}} for i in range(n)]}


TABLES = {"Results": payload(6, 3), "SPP IS": payload(4, 4)}
SEGS = {"Results": {"union": list(segments.UNION), "why": None, "oos": "OOS1", "no_oos": ["id5"],
                    "rows": {f"id{i}": {"Net profit": 1000.0 + i} for i in range(5)}},
        "SPP IS": {"union": list(segments.UNION), "rows": {}, "no_oos": [], "oos": None,
                   "why": segments.NO_HARVEST}}
BROKEN: set[str] = set()        # databanks whose segments request fails


def fake(root: Path) -> None:
    """Point the store at a scratch folder and the client at in-process answers."""
    discards.folder = lambda p, d: root / p / d.replace(" ", "_")

    def get(path: str, **q: str) -> dict:
        """The four GETs the panel makes; a databank in BROKEN fails its segments."""
        if path == "databank/segments" and q["databank"] in BROKEN:
            raise httpx.ConnectError("sin demonio")
        return {"databank/panels": lambda: TABS,
                "databank/table": lambda: TABLES[q.get("databank", "")],
                "databank/columns": lambda: {"views": store.views(q["project"], q["databank"])},
                "databank/segments": lambda: SEGS[q.get("databank", "")]}[path]()

    def post(path: str, body: dict) -> dict:
        """The columns write, and the aggregate (answered with an error: no cosecha here)."""
        if path == "databank/columns":
            return {"views": store.save(body["project"], body["databank"], body["table"],
                                        body["view"])}
        return {"error": "sin cosecha en la prueba"}
    client.get, client.post = get, post


def settle(app: QApplication, done: object = None, seconds: float = 5) -> None:
    """Pump events until `done()` holds (the threads' answers landed) or time runs out."""
    end = time.monotonic() + seconds
    while time.monotonic() < end and not (done and done()):
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


def heads(panel: Panel) -> list[str]:
    """The headers on screen, in visual order."""
    t, h = panel.table, panel.table.horizontalHeader()
    return [t.horizontalHeaderItem(c).text() for c in sorted(range(t.columnCount()),
                                                              key=h.visualIndex)]


def cells(panel: Panel, header: str) -> list:
    """The items of one column, top to bottom as shown."""
    t = panel.table
    c = [t.horizontalHeaderItem(i).text() for i in range(t.columnCount())].index(header)
    return [t.item(r, c) for r in range(t.rowCount())]


def disk(root: Path, bank: str = "Results") -> dict:
    """The databank's columns.json as written."""
    return json.loads((root / P / bank / "columns.json").read_text(encoding="utf-8"))


def choose(app: QApplication, root: Path, panel: Panel) -> list[str]:
    """Hide Sharpe IS, add four metrics through the chooser, keep; return the default."""
    default = heads(panel)
    cols = panel.columns
    offered, ids, _ = cols.offer(TABLES["Results"], panel.sub_spec(), True)
    settle(app, lambda: "Results" in cols.segs)
    offered, ids, _ = cols.offer(TABLES["Results"], panel.sub_spec(), True)
    assert "Sharpe Ratio|IS" in ids and "Net profit|OOS" in ids, ids
    chosen = [k for k in ids if k != "Sharpe Ratio|IS"] + [
        "Stability|IS", "Net profit|OOS2", "Net profit|IS+OOS1", "Sharpe Ratio|IS+OOS1"]
    menu = ColumnsMenu(offered, ids, "Results", cols.segs["Results"])
    tops = [menu.tree.topLevelItem(g) for g in range(menu.tree.topLevelItemCount())]
    assert any(t.text(0).startswith("OOS1 (en la tabla") for t in tops)
    for top in tops:
        for i in range(top.childCount()):
            item = top.child(i)
            item.setCheckState(0, Qt.Checked if item.data(0, Qt.UserRole) in chosen
                               else Qt.Unchecked)
    menu.narrow("sharpe")
    seen = [t.child(i).text(0) for t in tops for i in range(t.childCount())
            if not t.child(i).isHidden()]
    assert seen and all("Sharpe" in x for x in seen), seen
    menu.accept()
    assert menu.answer == chosen, menu.answer         # added at the end, in the list's order
    assert cols.keep(menu.answer) == ""
    saved = disk(root)[WIDE]
    assert saved["hidden"] == ["Sharpe Ratio|IS"] and saved["added"] == chosen[-4:], saved
    return default


def main() -> None:
    """Hide, add, «–», red losers, sort, drag, per databank, broken file, restore, filters."""
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fake(root)
        panel = Panel()
        panel.fill(P)
        settle(app, lambda: "Results" in panel.columns.views)
        default = choose(app, root, panel)
        panel.open_sub(0)
        settle(app)
        now = heads(panel)
        assert "Sharpe IS" not in now and now[-6:] == [
            "Estabilidad IS", "Beneficio neto OOS2", "Beneficio neto IS+OOS1",
            "Sharpe IS+OOS1", "Puerta", "SPP"], now       # metrics first, the study's after
        inks = [c.foreground().color().name() for c in cells(panel, "Beneficio neto OOS")]
        assert inks[0] != C["dead"] and set(inks[1:]) == {C["dead"]}, inks   # 0 is not red
        for key, v, red in (("Profit factor|OOS", .97, 1), ("Profit factor|IS", 1.2, 0),
                            ("Max DD %|IS", -9, 0), ("Drawdown|IS+OOS1", -3, 0), ("ZScore|OOS",
                            -.4, 0), ("Ret/DD Ratio|OOS2", -.1, 1), ("spread.PF [OOS]", .9, 1)):
            assert columns.unprofitable(key, v) == red, key
        assert [c.text() for c in cells(panel, "Beneficio neto OOS2")] == [DASH] * 6
        assert [c.text() for c in cells(panel, "Sharpe IS+OOS1")] == [DASH] * 6
        joined = cells(panel, "Beneficio neto IS+OOS1")
        assert [c.text() for c in joined][:2] == ["1 000", "1 001"]
        assert joined[5].text() == DASH and joined[5].toolTip() == columns.NO_OOS
        # «–» last whichever way the column is sorted.
        c = [panel.table.horizontalHeaderItem(i).text()
             for i in range(panel.table.columnCount())].index("Beneficio neto IS+OOS1")
        for order in (Qt.DescendingOrder, Qt.AscendingOrder):
            panel.table.sortByColumn(c, order)        # what a header click does
            texts = [x.text() for x in cells(panel, "Beneficio neto IS+OOS1")]
            top = "1 004" if order == Qt.DescendingOrder else "1 000"
            assert texts[-1] == DASH and texts[0] == top, (order, texts)
        # A header dragged: kept in the new order; the name is put back in front.
        h = panel.table.horizontalHeader()
        h.moveSection(heads(panel).index("Sharpe IS+OOS1"), 1)
        h.moveSection(0, 3)
        assert heads(panel)[:2] == ["Estrategia", "Sharpe IS+OOS1"], heads(panel)
        assert disk(root)[WIDE]["order"][0] == "Sharpe Ratio|IS+OOS1"
        # An id nobody offers now survives a save; a new default column shows up by itself.
        store.save(P, "Results", WIDE, disk(root)[WIDE]
                   | {"added": disk(root)[WIDE]["added"] + ["Ghost|IS"]})
        panel.columns.views.pop("Results")
        TABLES["Results"]["columns"].append({"key": "wfc.verdict", "kind": "study",
                                             "study": "wfc", "sub": "", "field": "verdict",
                                             "title": "WFC"})
        for r in TABLES["Results"]["rows"]:
            r["values"].append("pasa")
        panel.open_sub(0)
        settle(app, lambda: "Results" in panel.columns.views)
        assert heads(panel)[-1] == "WFC" and heads(panel)[1] == "Sharpe IS+OOS1", heads(panel)
        assert panel.columns.keep([k for k in panel.table.ids]) == ""
        assert "Ghost|IS" in disk(root)[WIDE]["added"], disk(root)
        # Per databank: SPP keeps its default; Cribas, on Results too, shows Build's metrics.
        panel.select("SPP", "IS")
        settle(app, lambda: "SPP IS" in panel.columns.views)
        assert "Beneficio neto IS+OOS1" not in heads(panel) and panel.table.rowCount() == 4
        panel.select("Puerta", "Cribas")
        assert (heads(panel)[1], heads(panel)[-1]) == ("Sharpe IS+OOS1", "Veredicto")
        # One metric left, in every Results table; Cribas' hidden verdict keeps its 3 rows.
        panel.columns.keep(["Net profit|IS"])
        panel.open_sub(1)
        assert heads(panel) == ["Estrategia", "Beneficio neto IS"] and panel.table.rowCount() == 3
        panel.set_hidden({"id1"})
        assert [panel.table.isRowHidden(r) for r in range(3)].count(True) == 1
        panel.select("Puerta", "Build")
        assert heads(panel) == ["Estrategia", "Beneficio neto IS", "Puerta", "SPP", "WFC"]
        # A fresh panel (the next session) reads the same choices back from the store.
        again = Panel()
        again.fill(P)
        settle(app, lambda: "Results" in again.columns.views)
        settle(app, lambda: "Results" in again.columns.segs)
        assert heads(again)[:2] == ["Estrategia", "Beneficio neto IS"], heads(again)
        again.columns.keep(None)                          # «Restaurar vista por defecto»
        again.open_sub(0)
        assert heads(again) == default + ["WFC"], heads(again)
        assert set(disk(root)) == {"Puerta › Cribas"}, disk(root)
        # A corrupt file reads as nothing chosen and the next save heals it.
        (root / P / "SPP_IS").mkdir(parents=True, exist_ok=True)
        (root / P / "SPP_IS" / "columns.json").write_text("[1, 2]", encoding="utf-8")
        assert store.views(P, "SPP IS") == {}
        store.save(P, "SPP IS", "SPP › IS", None)
        assert disk(root, "SPP_IS") == {}
        # A failed read says why, and is asked again rather than kept.
        BROKEN.add("SPP IS")
        again.select("SPP", "IS")
        cols = again.columns
        cols.offer(TABLES["SPP IS"], again.sub_spec(), True)
        settle(app, lambda: ("segments", "SPP IS") in cols.failed)
        offered, _, _ = cols.offer(TABLES["SPP IS"], again.sub_spec(), True)
        assert offered["Net profit|IS+OOS1"]["why"].startswith("no se pudo calcular"), offered
        assert "SPP IS" not in cols.segs
        BROKEN.clear()
        cols.forget("SPP IS")
        cols.offer(TABLES["SPP IS"], again.sub_spec(), True)
        settle(app, lambda: "SPP IS" in cols.segs)
        offered, _, _ = cols.offer(TABLES["SPP IS"], again.sub_spec(), True)
        assert offered["Net profit|IS+OOS1"]["why"] == segments.NO_HARVEST
    app.processEvents()
    print("ok: métricas por databank, «–» y sus motivos, rojo si pierde, orden, nuevas por "
          "defecto, ids guardados, fichero roto, lectura fallida, restaurar y filtros")


if __name__ == "__main__":
    main()

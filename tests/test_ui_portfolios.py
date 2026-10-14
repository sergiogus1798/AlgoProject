#!/usr/bin/env python3
"""Known-answer test of the PORTFOLIOS zone's daemon: known folders → the JSON the window paints, and the launchers' plumbing."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from ui_portfolios_planted import A, B, C, FUNDED, RUN, plant  # noqa: E402

from portfolio.common.construct.incubation import record
from ui.daemon import jobs
from ui.daemon.portfolios import (
    api,
    commands,
    construct,
    correlation,
    funded,
    parts,
    shelf,
    weights,
)

FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def words(m: dict) -> None:
    """What the walk of 2026-10-05 found: a button named as it is not, English thousands, unreadable cells."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication, QTableWidget
    from ui.desktop.portfolios import strips
    from ui.desktop.portfolios.matrix import Matrix
    from ui.desktop.theme import T

    check(
        "Constructor: the unjudged line names the launcher as the strip spells it",
        f"«{strips.MODULES['Constructor']['launchers'][1][0]}»" in construct.UNJUDGED,
    )
    check(
        "no figure of the zone is printed with English thousands (12,345)",
        not any(
            ":,}" in f.read_text(encoding="utf-8")
            for f in Path(api.__file__).parent.glob("*.py")
        ),
    )
    app = QApplication.instance() or QApplication([])
    blind = Matrix(
        m | {"threshold": None, "states": [[None] * 3] * 3}, lambda i, j: None
    )
    cell = blind.findChild(QTableWidget).item(0, 1)
    check(
        "Correlación: without a threshold read the cells are still readable (light on dark)",
        cell.foreground().color().name() == T["text"]
        and cell.background().color().name() == T["line"],
    )
    from ui.desktop.portfolios.databank import Databank

    bank, rows = (
        Databank(),
        [
            {
                "identity": i,
                "strategy": "S",
                "symbol": "X",
                "timeframe": "H1",
                "step": "24",
                "versions": [{"version": "v"}],
                "archived_at": "2026-01-01T00:00:00",
            }
            for i in (A, B)
        ],
    )
    bank.fill(rows, {"pools": [], "runs": []})
    bank.tick(True)
    bank.say("Pool declarado.", "pass")
    bank.fill(
        rows, {"pools": [{"name": "Test_p", "members": [A, B]}], "runs": []}
    )  # the reload a declare or a job causes
    check(
        "databank: a reload keeps what was just said and the owner's marks",
        "Pool declarado." in bank.said.text() and len(bank.ticked()) == 2,
    )
    from ui.desktop.portfolios.board import PortfoliosBoard

    board, run = (
        PortfoliosBoard(),
        {
            "kind": "real",
            "id": RUN,
            "pool": "Test_p",
            "plan": "",
            "k": 2,
            "score": 0.9,
            "label": "sin juzgar",
            "relaxed": {},
        },
    )
    board.selection = {"pool": "Test_p", "run": ""}
    board.filled(
        {
            "test_root": "",
            "pools": [{"name": "Test_p", "members": [A, B]}],
            "runs": [run],
        }
    )
    check(
        "databank: a reload keeps a chosen POOL row chosen, it does not move to the newest run",
        board.bank.right.currentRow() == 1 and board.selection.get("run") == "",
    )
    page = board.pages["Banco"]
    page.feed({"banks": ["20261005_100000_viejo", "20261004_100000_antes"]})
    page.inputs["bank"].setCurrentIndex(1)
    board.computed = lambda: None
    page.ended({"rc": 1})
    kept = page.value("bank")
    page.ended({"rc": 0})
    page.feed(
        {
            "banks": [
                "20261005_120000_nuevo",
                "20261005_100000_viejo",
                "20261004_100000_antes",
            ]
        }
    )
    check(
        "bank: after «Calcular la caja» the table shown is the one just computed, not the one chosen before",
        kept == "20261004_100000_antes"
        and page.value("bank") == "20261005_120000_nuevo",
    )
    from ui.desktop.portfolios.calc import CalcButton

    def row(page: object, w: object) -> int:
        """The row of the page's layout a strip widget sits in."""
        lay = page.layout()
        return next(
            i
            for i in range(lay.count())
            if lay.itemAt(i).layout() and lay.itemAt(i).layout().indexOf(w) >= 0
        )

    bank = board.pages["Banco"]
    check(
        "strip: with five selectors the typed ones go to a second row — the combos were squeezed, the launcher cut",
        row(bank, bank.inputs["horizon"]) - row(bank, bank.inputs["plan"]) == 1
        and row(bank, bank.findChild(CalcButton)) == row(bank, bank.inputs["plan"]),
    )
    from PySide6.QtWidgets import QFrame, QVBoxLayout
    from ui.desktop.blocks import table
    from ui.desktop.theme import QSS

    app.setStyleSheet(QSS)
    frame = QFrame(objectName="term")
    box = table.widget(
        parts.table("t", ["Método", "Sharpe"], [["paridad de riesgo (1/σ)", 0.04]] * 20)
    )
    QVBoxLayout(frame).addWidget(box)
    frame.show()
    app.processEvents()
    grid = box.findChild(QTableWidget)
    wide = sum(grid.columnWidth(j) for j in range(2))
    check(
        "tables: columns are measured in the frame's own font — a long cell is not cut",
        grid.columnWidth(0) >= grid.sizeHintForColumn(0),
    )
    check(
        "tables: a compact table that scrolls keeps its last column clear of the scrollbar",
        grid.maximumWidth() >= wide + grid.verticalScrollBar().sizeHint().width(),
    )
    del blind, bank, board, frame, app


def main() -> int:
    """Plant the folders, point the readers at them, read, then walk the launchers with `jobs.start` stubbed."""
    queued, real_spent, real_root = [], construct.spent, shelf.test_root
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plant(root)
        shelf.ROOT, record.ROOT = root, root / "incubation"
        shelf.names = lambda: {A: {"strategy": "Alfa"}}
        construct.spent = lambda pool, members=None: ""
        correlation.pool_mod.read = lambda pool, firm: {"hash": "hash"}
        jobs.start = lambda label, argv, about, **_: (
            queued.append((label, argv, about)) or {"id": "job-1"}
        )
        jobs.listing = lambda: []

        rows = shelf.runs()
        check(
            "runs: newest first, the funded one read as stage A only",
            [r["id"] for r in rows] == [FUNDED, RUN]
            and rows[0]["kind"] == "funded"
            and rows[0]["label"] == "solo etapa A"
            and rows[0]["score"] == 0.25,
        )
        check(
            "runs: the real one unjudged, K = 2, relaxed kept",
            rows[1]["kind"] == "real"
            and rows[1]["k"] == 2
            and rows[1]["label"] == "sin juzgar"
            and rows[1]["relaxed"] == {"pearson": 0.9},
        )

        old = funded.read("Test_p", run=FUNDED)
        check(
            "Fondeo: a run written before the risk cap was counted still opens (it was a KeyError on screen)",
            old["tabs"][0]["title"] == "Etapa A"
            and "tope de riesgo" not in json.dumps(old["tabs"][0], ensure_ascii=False),
        )
        got = construct.read("Test_p", "")
        check(
            "Constructor: three tabs, the relaxed line, unjudged",
            [t["title"] for t in got["tabs"]]
            == ["Resultado", "Combinaciones", "Nulo y veredicto"]
            and got["relaxed"].startswith(
                "AJUSTADO: umbrales relajados (pearson = 0.9)"
            )
            and not got["judged"],
        )
        head = got["tabs"][0]["blocks"][0]["text"]
        check(
            "Constructor: the head names the members by strategy and short identity",
            "K = 2 [Alfa · aaaaaaaa, bbbbbbbb]" in head and "deja fuera 1 de 3" in head,
        )
        check(
            "Constructor: a pool without runs is an empty state with its one action",
            construct.read("Test_otro", "")["tabs"] == []
            and "pulsa «Buscar cartera»" in construct.read("Test_otro", "")["empty"],
        )

        m = correlation.read("Test_p", "", "monthly", "pearson")["matrix"]
        check(
            "Correlación: the matrix is symmetric with a blank diagonal",
            m["values"]
            == [[None, 0.10, 0.20], [0.10, None, -0.45], [0.20, -0.45, None]],
        )
        check(
            "Correlación: discrete steps against the threshold in force, |ρ| two-sided",
            m["threshold"] == 0.30
            and m["two_sided"]
            and m["states"][0] == [None, "pass", "watch"]
            and m["states"][1][2] == "fail",
        )
        graph = correlation.read("Test_p", "", "monthly", "pearson")["tabs"][0]
        table = next(b for b in graph["blocks"] if b["kind"] == "table")
        check(
            "Correlación: the admissible graph says which pair falls and why",
            [r[2] for r in table["rows"]] == ["sí", "sí", "no"]
            and table["rows"][2][3] != "—",
        )

        check(
            "Pesos: nothing run → what is missing and the action",
            weights.read("Test_p", RUN)["tabs"] == []
            and "Calcular" in weights.read("Test_p", RUN)["empty"],
        )
        check(
            "Incubación: nothing registered → the plain statement, no tabs",
            weights.incubation() == {"tabs": [], "empty": weights.IDLE, "relaxed": ""},
        )

        shelf.test_root = lambda: ""
        refused = commands.plan(
            "universe", {"pool": "Test_p", "sets": "--set pairs.pearson=0.9"}
        )
        check(
            "launcher: a --set is refused on the real root",
            not refused["ok"] and "raíz de prueba" in refused["reasons"][0],
        )
        plain = api.preflight("universe", pool="Test_p")
        shelf.test_root = lambda: "raíz"
        odd = api.preflight(
            "universe",
            pool="Test_p",
            sets="--set noexiste.clave=1 --set pairs.nada=2 --set pairs.pearson=0.9",
        )
        check(
            "launcher: a --set naming no knob is refused in words, not as a KeyError",
            not odd["ok"]
            and [r.split("»")[0] for r in odd["reasons"]]
            == [
                "ajuste desconocido: «noexiste.clave=1",
                "ajuste desconocido: «pairs.nada=2",
            ],
        )
        shelf.test_root = real_root
        check(
            "launcher: universe needs no confirmation and runs the real module",
            plain["ok"]
            and not plain["confirm"]
            and plain["argv"]
            == ["-m", "portfolio.common.construct.universe", "--pool", "Test_p"],
        )
        lacking = api.preflight("stage_b", run=FUNDED)
        check(
            "launcher: stage B refuses without the owner's knobs, none defaulted",
            not lacking["ok"]
            and any("funded.open_risk_cap" in r for r in lacking["reasons"])
            and any("stageb.t1_gap" in r for r in lacking["reasons"]),
        )
        check(
            "launcher: the bank refuses without horizon, edge and the owner's inputs",
            {"horizonte", "edge", "owner.eurusd"}
            <= {
                w
                for r in api.preflight("bank", run=FUNDED)["reasons"]
                for w in ("horizonte", "edge", "owner.eurusd")
                if w in r
            },
        )
        wrong = api.preflight("verdict", run=FUNDED)
        check(
            "launcher: the verdict wants a run of the real path",
            not wrong["ok"] and "camino real" in wrong["reasons"][0],
        )

        pre = api.preflight("verdict", run=RUN)
        check(
            "verdict: confirmation required, naming the pool and the single use",
            pre["ok"]
            and pre["confirm"]
            and "«Test_p»" in pre["text"]
            and "UN SOLO USO" in pre["text"]
            and RUN in pre["text"],
        )
        blind = api.run_action(
            api.Run(action="verdict", params={"run": RUN}, nonce="inventado")
        )
        check(
            "verdict: without its preflight's nonce nothing is queued",
            not blind["ok"] and not queued,
        )
        done = api.run_action(
            api.Run(action="verdict", params={"run": RUN}, nonce=pre["nonce"])
        )
        check(
            "verdict: with it, ONE job of report.py on that run (command stubbed)",
            done["ok"]
            and len(queued) == 1
            and queued[0][0] == "portfolio"
            and queued[0][1][:4]
            == ["-m", "portfolio.common.construct.report", "--pool", "Test_p"]
            and queued[0][1][4:6] == ["--run", str(root / "runs" / RUN)]
            and "--seed" in queued[0][1],
        )
        again = api.run_action(
            api.Run(action="verdict", params={"run": RUN}, nonce=pre["nonce"])
        )
        check(
            "verdict: the nonce is spent — a second press queues nothing",
            not again["ok"] and len(queued) == 1,
        )
        spent, construct.spent = construct.spent, real_spent
        construct.pool_mod.read = lambda pool, firm: {"hash": "hash"}
        construct.oos2_mod.spent = lambda pool: {
            "ts": "2026-01-03T00:00:00",
            "thresholds": {"members": f"{A}+{C}"},
        }
        check(
            "verdict: a pool whose oos2 another portfolio read says this verdict cannot open it",
            "solo medirá oos1" in api.preflight("verdict", run=RUN)["text"],
        )
        construct.oos2_mod.spent = lambda pool: {
            "ts": "2026-01-03T00:00:00",
            "thresholds": {
                "members": "+".join(sorted(shelf.run(root / "runs" / RUN)["members"]))
            },
        }
        text = api.preflight("verdict", run=RUN)["text"]
        check(
            "verdict: the portfolio that read it is told its stored reading comes back, not «solo oos1»",
            "esta misma cartera" in text and "solo medirá oos1" not in text,
        )
        construct.spent = spent
        (root / "runs" / RUN / "verdict.json").write_text(
            json.dumps(
                {  # a relaxed bar: percentile 50, refused oos2
                    "label": "SIN VEREDICTO: oos1 pasado, oos2 sin leer",
                    "pass": None,
                    "sentence": "…",
                    "oos1": {
                        "state": "pass",
                        "span": ["2020-01-02", "2021-12-31"],
                        "value": 0.8,
                        "quantile": 50.0,
                        "bar": 0.5,
                        "null_median": 0.5,
                        "percentile": 0.9,
                        "n": 10000,
                        "n_space": 37,
                        "k": 2,
                        "share_chosen": 0.03,
                    },
                    "oos2": {"state": "refused", "reason": "gastada"},
                }
            )
        )
        judged = construct.verdict(root / "runs" / RUN)["blocks"]
        bar = next(b for b in judged if b["kind"] == "table")["rows"][1]
        check(
            "verdict: the bar's explanation names the percentile in force, not a fixed 95",
            bar[0] == "percentil 50 del azar"
            and bar[2].startswith("Percentil 50 del azar")
            and "solo superan 50 de cada 100" in bar[2],
        )
        check(
            "verdict: «SIN VEREDICTO» is not announced as «VEREDICTO: SIN VEREDICTO»",
            judged[0]["text"].startswith("SIN VEREDICTO")
            and parts.headline("NO PASA (oos1)") == "VEREDICTO: NO PASA (oos1)",
        )
        words(m)
    print(f"\n{len(FAILURES)} fallos" if FAILURES else "\nTodo OK")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""The campaign's loop on a fake workflow command: a STOP mid-run leaves the cell interrupted and SQX's
stop called, a restart resumes it with `run` and repeats nothing, three failed tries make a cell
failed and two failed cells running end the loop, and a cell whose palette expert asks a question is
set aside while the next one runs; only a done cell's project is retired. No SQX, no install; the data root is a temp folder."""

import os
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
os.environ["ALGO_DATA_ROOT"] = str(TMP)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.campaign import keep, ledger, run  # noqa: E402

FLOW = TMP / "fakeflow.sh"
FLOW.write_text(f"""#!/bin/bash
echo "$1 $2" >> {TMP}/calls
[ -e {TMP}/fail ] && exit 1
mkdir -p {TMP}/projects/$2 {TMP}/autopilot/$2/r1
touch {TMP}/projects/$2/project.cfx
[ -e {TMP}/slow ] && sleep 30
printf '| paso | tipo | s | qué hizo |\\n|---|---|---|---|\\n| 6+7 | sqx | 120 | CONSTRUCCION: 0 → 1000 · OOS: 0 → 1000 |\\n| 8 | judge | 60 | 5 hechos; OOS: 1000 → 10 por sorteo |\\n' > {TMP}/autopilot/$2/r1/resumen.md
echo '[]' > {TMP}/autopilot/$2/r1/finalistas.json
""")
FLOW.chmod(0o755)
run.WORKFLOW = [str(FLOW)]
run.WORKER = ["touch", str(TMP / "worker_stopped")]
run.AUTOPILOT = "fakeflow.sh [a-z]+ {} "
run.POLL = run.BOOT = 0.2
run.project_dir = lambda name, install: TMP / "projects" / name
run.template_dir = lambda name: TMP / name
RETIRED: list[str] = []
run.retire = types.SimpleNamespace(
    retire=lambda name, *a, **k: RETIRED.append(name) or f"retired {name}"
)
run.shutil.disk_usage = lambda path: types.SimpleNamespace(free=1e12)  # /tmp is small


def cell(n: str) -> dict:
    """A queued cell named by one letter."""
    return {
        "template": f"t{n}",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "direction": "long",
        "family": "tendencia",
        "palette": "-",
        "project": f"Trade_{n}",
    }


def states() -> dict[str, str]:
    """Project -> state, from the ledger."""
    return {r["project"]: r["state"] for r in ledger.cells().values()}


def main() -> None:
    """The three scenarios, in order, on one ledger."""
    for n in "AB":
        ledger.mark(cell(n), "pending", **cell(n))
    (TMP / "slow").touch()
    loop = threading.Thread(target=run.loop)
    loop.start()
    time.sleep(1.5)
    run._stop_file().touch()
    loop.join(timeout=20)
    assert not loop.is_alive(), "STOP did not end the loop"
    assert states() == {"Trade_A": "interrupted", "Trade_B": "pending"}, states()
    assert (TMP / "worker_stopped").exists(), "the worker's stop was not called"
    assert len(list((TMP / "campaign" / "runs").glob("tA_*/workflow.json"))) == 1

    (TMP / "slow").unlink()
    run._stop_file().unlink()
    run.loop()
    assert states() == {"Trade_A": "done", "Trade_B": "done"}, states()
    assert (TMP / "calls").read_text().split("\n")[:3] == [
        "template Trade_A",
        "run Trade_A",
        "template Trade_B",
    ]
    assert ledger.following() is None
    done = ledger.cells()[ledger.key(cell("B"))]
    assert done["steps_minutes"] == 3.0 and done["counts"][-1] == "OOS 1000→10", done

    (TMP / "fail").touch()
    for n in "CDE":
        ledger.mark(cell(n), "pending", **cell(n))
    run.loop()
    assert [states()[f"Trade_{n}"] for n in "CDE"] == ["failed", "failed", "pending"], (
        states()
    )
    assert (TMP / "calls").read_text().count("Trade_C") == 3

    (TMP / "fail").unlink()
    run._stop_file().unlink(missing_ok=True)
    asked = {**cell("F"), "palette": "experto"}
    ledger.mark(asked, "pending", **asked)
    run.palette.choose = lambda c: (
        (None, "PREGUNTA: ¿cuál?") if c["project"] == "Trade_F" else ("p", "")
    )
    run.loop()
    assert states()["Trade_F"] == "question" and states()["Trade_E"] == "done", states()

    from pipeline.campaign import shelf

    sqx = TMP / "s.sqx"
    sqx.write_text("x")
    final = {
        "strategy": "Strategy 1 S0",
        "mother": "Strategy 1",
        "identity": "i",
        "sqx": str(sqx),
        "stop": {"x": 2.0},
        "archive": str(TMP),
        "mother_archive": None,
    }
    shelf.place({**cell("G"), "test": True}, [final], TMP)
    filed = TMP / "campaign/supervivientes/_pruebas/XAUUSD/H1/long/tendencia/tG"
    assert len(list(filed.glob("*_Strategy_1_S0/estrategia.sqx"))) == 1
    assert "Strategy 1 S0" in (TMP / "campaign/supervivientes/indice.csv").read_text()

    rows = keep.steps(TMP / "autopilot" / "Trade_B" / "r1" / "resumen.md")
    assert [c["out"] for r in rows for c in r["counts"]] == [1000, 1000, 10]

    from pipeline.campaign import plan

    seg = {"rows": 0, "screenings": 0}
    plan.cellbook.ask = lambda *a: {  # a cell with only Test_ rows spent oos1 and oos2
        "cell": {"oos1": {**seg, "screenings": 4}, "oos2": {**seg, "rows": 30}}
    }
    row = {**cell("H"), "template": "tH"}
    assert plan._spent(row) == "oos1 4 cribas, oos2 30 filas"
    assert RETIRED == ["Trade_A", "Trade_B", "Trade_E"], (
        RETIRED
    )  # only a done cell is retired
    print("ok")


if __name__ == "__main__":
    main()

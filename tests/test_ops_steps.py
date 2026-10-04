"""«En marcha» in the workflow's order, and the WFC counted by mother."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import stage  # noqa: E402
from ui.daemon.ops import steps  # noqa: E402
from ui.desktop.durations import ratio  # noqa: E402

LEGS = stage.titles("wfc")


def task(title: str) -> dict:
    """A task row as `progress.state` builds it, reduced to what the ordering reads."""
    return {"title": title, "status": "done"}


def py(n: str) -> dict:
    """A Python step row as `python_rows` builds it."""
    return {"kind": "python", "step": float(n), "n": n, "title": n, "status": "pending", "why": ""}


def test_file_order_is_not_the_workflows() -> None:
    """The Nikkei's file: WFM before CrossTF before the WFC legs; Python steps between."""
    file_order = ["CONSTRUCCION", "OOS", "MCR 1 Bar", "SPP IS", "SPP OOS", "WFM", "CrossTF",
                  *LEGS, "CrossTF H1"]
    rows = steps.order([task(t) for t in file_order], [py("12"), py("17"), py("20")], [], 10)
    names = [r["title"] for r in rows]
    assert names == ["CONSTRUCCION", "OOS", "CrossTF", "CrossTF H1", "12", "MCR 1 Bar", "SPP IS",
                     "SPP OOS", *LEGS, "17", "WFM", "20"]


def test_only_the_running_leg_names_its_mother() -> None:
    """A finished leg carries no mother: steps 23 and 24 start the same legs."""
    runs = [task(LEGS[0])] * 2
    live = {"title": LEGS[0], "status": "running"}
    got = steps.order([task(LEGS[1]), live], [], runs, 10)
    assert [r.get("mother") for r in got] == [None, {"n": 2, "of": 10}]


def test_pasos_csv_is_read_after_a_restart() -> None:
    """Known answer: last word per step wins; a lone «empezó» of a dead run is nothing."""
    import tempfile
    from unittest import mock
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "P" / "20261004-1"
        run.mkdir(parents=True)
        (run / "pasos.csv").write_text("8,empezó,10:00:00\n8,hecho,10:01:00\n"
                                       "10,empezó,10:02:00\n12+14,falló,10:03:00\n")
        (run / "estado.txt").write_text("x")
        with mock.patch.object(steps, "autopilot_runs", return_value=Path(tmp)):
            fresh = steps.autopilot_marks("P")
            dead = steps.autopilot_marks("P", now=run.joinpath("estado.txt").stat().st_mtime
                                         + steps.STALE_S + 1)
    assert fresh == {"8": "done", "10": "running", "12": "failed", "14": "failed"}
    assert dead == {"8": "done", "12": "failed", "14": "failed"}


def test_mothers_counts_the_unbroken_wfc_tail() -> None:
    """Three mothers = three starts of each leg after the last non-WFC task."""
    runs = [task("SPP OOS")] + [task(t) for _ in range(3) for t in LEGS]
    assert steps.mothers(runs, LEGS[0], 10) == {"n": 3, "of": 10}
    assert steps.mothers(runs, LEGS[2], 2) == {"n": 3, "of": None}     # total smaller: unknown
    assert steps.mothers([task("WFM")], LEGS[0], 10) is None
    assert ratio({"done": 300, "total": 500, "mother": {"n": 7, "of": 30}}).startswith(
        "madre 7 de 30 · 300")


if __name__ == "__main__":
    test_file_order_is_not_the_workflows()
    test_mothers_counts_the_unbroken_wfc_tail()
    test_pasos_csv_is_read_after_a_restart()
    test_only_the_running_leg_names_its_mother()
    print("ok")

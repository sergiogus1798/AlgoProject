#!/usr/bin/env python3
"""The autopilot's tail, 17 → 26, on hand-built rails and a ledger in a temp folder: the order
of the plan, its clean stops, the blind block under the ledger's door, and a run with nobody
left ending without a failure. No SQX and no study runs: every command is recorded by a stub."""

import contextlib
import json
import os
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import gate, record
from ledger import study as studymod
from pipeline.autopilot import blind, call, plan, run, survivors, tail
from ui.daemon.workflow.steps import STEPS

MT5 = {"start": "2024-01-01", "end": "2026-08-30", "model": "ohlc_m1", "firms": ["ftmo"]}
GIVEN = {"panel": {"21": "OOS", "22": "Results"}, "mt5": MT5, "judged": set()}
WHO = {"symbol": "USDJPY", "timeframe": "H1", "feed": "USDJPY_M1", "family": "fam"}
BLOCK = [("17", "blind"), ("18", "blind"), ("18.5", "blind")]
CLOSING = [("21", "reading"), ("22", "reading"), ("23", "structural"), ("24", "stop"),
           ("25", "edge"), ("25", "finalists")]


@contextlib.contextmanager
def patched(target: object, **attrs: object) -> Iterator[None]:
    """Swap attributes of a module for the length of a block, then put them back."""
    kept = {k: getattr(target, k) for k in attrs}
    for k, v in attrs.items():
        setattr(target, k, v)
    try:
        yield
    finally:
        for k, v in kept.items():
            setattr(target, k, v)


def rail(pending_from: str = "16.5", family: str | None = "fam", **states: str) -> dict:
    """GET /api/workflow's shape: done up to `pending_from`, pending after, `states` on top
    (keys as `s18_5` for step 18.5)."""
    at = [s["n"] for s in STEPS].index(pending_from)
    over = {k[1:].replace("_", "."): v for k, v in states.items()}
    return {"family": family, "steps": [
        {"n": s["n"], "title": s["title"], "kind": s["kind"], "stage": s.get("stage"),
         "state": over.get(s["n"], "done" if i < at else "pending"),
         "tests": [{"key": "wfm", "state": "done" if i < at else "pending"}] * (s["n"] == "19")}
        for i, s in enumerate(STEPS)]}


def kinds(got: dict) -> list[tuple[str, str]]:
    """A plan as (step, kind) pairs."""
    return [(a["n"], a["kind"]) for a in got["do"]]


def test_the_whole_tail_in_order() -> None:
    """16 judged, the variants, the blind block with the WFM and its rows, 20 and its judge,
    21-25, the finalists, step 26 — and every blind look redone, the batches being new."""
    got = plan.plan(rail(), GIVEN)
    assert kinds(got) == [("16", "judge"), ("16.5", "variants"), *BLOCK, ("19", "sqx"),
                          ("19", "wfm"), ("19", "ledger"), ("20", "joint"), ("20", "judge"),
                          *CLOSING, ("26", "mt5verify")]
    assert got["stop"] == {"n": None, "why": "no queda ningún paso"}
    assert all(a["redo"] for a in got["do"] if a["kind"] == "blind")
    assert got["do"][-1]["params"] == MT5 and got["do"][10]["databank"] == "OOS"
    json.dumps(got)     # plan.json is written as it comes


def test_clean_stops() -> None:
    """Nothing is defaulted: 26 without every parameter, 21 without its databank, 17 without
    a family and a step in marcha each end the plan before it, saying what is missing."""
    got = plan.plan(rail(), GIVEN | {"mt5": MT5 | {"model": None, "firms": []}})
    assert kinds(got)[-1] == ("25", "finalists") and got["stop"]["n"] == "26"
    assert "--mt5-model, --mt5-firms" in got["stop"]["why"] and "--mt5-from" not in got["stop"]["why"]

    got = plan.plan(rail(), GIVEN | {"panel": {"22": "Results"}})
    assert kinds(got)[-2:] == [("20", "joint"), ("20", "judge")]
    assert got["stop"]["n"] == "21" and "--panel 21=" in got["stop"]["why"]

    got = plan.plan(rail(family=None), GIVEN)
    assert kinds(got) == [("16", "judge"), ("16.5", "variants")]
    assert got["stop"] == {"n": "17", "why": tail.NO_FAMILY}

    got = plan.plan(rail("23", s23="running"), GIVEN)
    assert got["do"] == [] and got["stop"] == {"n": "23", "why": "está en marcha"}

    # without parameters and with 26 already verified, the rail simply runs out
    got = plan.plan(rail("26", s26="done"), tail.NOTHING)
    assert kinds(got) == [("25", "finalists")] and got["stop"]["n"] is None


def test_a_rerun_takes_up_where_it_stopped() -> None:
    """17 and 18 done, 19 not: the looks are planned without `redo` (a mother with her
    result is skipped when run), the WFM runs, and everything after it runs again."""
    got = plan.plan(rail("19", s16_5="done"), GIVEN)
    assert kinds(got) == [*BLOCK, ("19", "sqx"), ("19", "wfm"), ("19", "ledger"),
                          ("20", "joint"), ("20", "judge"), *CLOSING, ("26", "mt5verify")]
    assert not any(a["redo"] for a in got["do"] if a["kind"] == "blind")

    # the block and 20 done, 21 done: only what is pending, and no judge of a step whose
    # next step already ran
    got = plan.plan(rail("22"), GIVEN | {"mt5": {}})
    assert kinds(got) == CLOSING[1:] and got["stop"]["n"] == "26"

    # a step the owner gives rules to is judged right after it runs
    got = plan.plan(rail("24"), GIVEN | {"judged": {"8", "24"}})
    assert kinds(got)[:3] == [("24", "stop"), ("24", "judge"), ("25", "edge")]


def ledger(folder: Path, steps: list[int]) -> None:
    """A study's ledger in `folder` holding one row of each of `steps`."""
    for step in steps:
        record.append("S", record.search("S", {
            "step": step, "launched_by": "test", "symbol": "USDJPY", "timeframe": "H1",
            "segment": "oos2", "n_in": 1, "n_out": 1, "criterion": "x", "note": "lote M"}))


def test_the_door_refuses_to_read_without_the_three_rows() -> None:
    """Under ALGO_AUTONOMOUS, step 20 and the registration refuse while 19 has no row, and
    no command starts; a human is not refused. With the WFM read, its rows are written once."""
    ran, asked = [], []
    with tempfile.TemporaryDirectory() as tmp, \
            patched(studymod, path=lambda s: Path(tmp) / f"{s}.jsonl"), \
            patched(survivors, about=lambda p: WHO), \
            patched(call, run=ran.append, window=lambda *a: [["-m", a[0]]]), \
            patched(blind, study=lambda p: ("S", {"study": "S", "symbol": "USDJPY",
                                                  "timeframe": "H1", "config_hash": None}),
                    bank=lambda p: "WFM", variants_dir=lambda p, m: Path(tmp) / m,
                    report_dir=lambda p, d, day: Path(tmp) / "reports" / d / day):
        ledger(Path(tmp), [17, 18])
        mothers = pd.DataFrame({"strategy": ["M"], "identity": ["i"], "file": [None]})
        os.environ[gate.AUTONOMOUS] = "1"
        try:
            for refused in (lambda: blind.joint("P"), lambda: blind.register("P", mothers)):
                try:
                    refused()
                    raise AssertionError("the door let a blind read through")
                except PermissionError as said:
                    assert "faltan [19]" in str(said)
            assert ran == []

            # every look asks the door for oos2 first; step 20 has no claim on it
            with patched(gate, allow=lambda *a: asked.append(a)):
                said = blind.look("P", "17", "wfc", mothers, redo=False)
            assert asked == [(17.0, "oos2", "USDJPY")] and ran == [["-m", "wfc"]]
            assert said.startswith("wfc: 1 madre(s)")
            (Path(tmp) / "M" / "estudios").mkdir(parents=True)
            (Path(tmp) / "M" / "estudios" / "wfc.json").write_text("{}")
            assert "0 madre(s) leídas" in blind.look("P", "17", "wfc", mothers, redo=False)
            assert "1 madre(s) leídas" in blind.look("P", "17", "wfc", mothers, redo=True)
            (Path(tmp) / "M" / "estudios" / "wfc.json").unlink()

            # the WFM reading lands: its three rows are written, once, and the door opens
            read = Path(tmp) / "reports" / "WFM" / "2026-10-02" / "wfm"
            (read / "estrategias").mkdir(parents=True)
            (read / "verdict.csv").write_text("strategy,verdict\nM,blind\n")
            (read / "estrategias" / "M.json").write_text(
                json.dumps({"computed_at": "2026-10-02T10:00:00+00:00"}))
            assert blind.register("P", mothers) == "filas escritas: paso 19: 3"
            assert blind.register("P", mothers) == "17, 18 y 19 ya tenían sus filas"
            assert list(studymod.read("S")["step"]) == [17, 18, 19, 19, 19]
            del ran[:]
            assert blind.joint("P") == "blindJoint sobre el estudio S"
            assert ran == [["-m", "blindJoint"]]
        finally:
            os.environ.pop(gate.AUTONOMOUS, None)
        # a human is never refused: the same order, the door open
        (Path(tmp) / "S.jsonl").unlink()
        blind.joint("P")


def test_nobody_left_is_a_clean_end() -> None:
    """Zero survivors of 16: the variants never start, resumen.md says why, no fallo.md."""
    started = []
    todo = {"do": [{"n": "16.5", "title": "v", "kind": "variants", "tests": []}],
            "stop": {"n": "26", "why": "x"}}
    with tempfile.TemporaryDirectory() as tmp, \
            patched(run.advance, where=lambda p: {"role": "custodian"}, busy=lambda *a: []), \
            patched(run.workflow, workflow=lambda p: {}), \
            patched(run.plan, plan=lambda data, given: todo), \
            patched(run.variants, run=lambda *a: started.append(a)), \
            patched(survivors, databank_dir=lambda *a: Path(tmp) / "empty"):
        out = Path(tmp)
        run.autopilot("Test_x", out)
        assert started == [] and not (out / "fallo.md").exists()
        assert "«SPP OOS» no tiene ninguna superviviente" in (out / "resumen.md").read_text()
        assert (out / "estado.txt").read_text().split(" ", 1)[1].startswith("FIN")


if __name__ == "__main__":
    test_the_whole_tail_in_order()
    test_clean_stops()
    test_a_rerun_takes_up_where_it_stopped()
    test_the_door_refuses_to_read_without_the_three_rows()
    test_nobody_left_is_a_clean_end()
    print("ok")

#!/usr/bin/env python3
"""The autopilot's step 26 hand-over: a finalist is the mother's own `.sqx` (no stop, no
variant), an empty list is a clean end, and step 26's clean refusal."""

import json
import sys
import tempfile
import types
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import call, finalists, survivors
from tests.test_autopilot_tail import WHO, patched

REAL = "Test_USDJPY_donchianUpperCrossUp_H1"


def mothers(folder: Path, names: list[str]) -> pd.DataFrame:
    """`survivors.mothers`' frame over empty files named after each mother."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / f"{name}.sqx").write_bytes(b"")
    return pd.DataFrame(
        {
            "strategy": names,
            "identity": [f"id-{n}" for n in names],
            "file": [folder / f"{n}.sqx" for n in names],
        }
    )


def test_a_finalist_is_the_mothers_own_file() -> None:
    """One row per mother: her name, her `.sqx` (absolute), no `stop` field; none is a clean end."""
    with (
        tempfile.TemporaryDirectory() as tmp,
        patched(survivors, about=lambda p: WHO),
        patched(
            finalists.identity,
            hashed=lambda files: {Path(f): f"id-{Path(f).stem}" for f in files},
        ),
    ):
        who = mothers(Path(tmp) / "bank", ["Strategy 1", "Strategy 2"])
        said = finalists.write("Pr", who, Path(tmp))
        rows = json.loads((Path(tmp) / finalists.FILE).read_text())
        assert "2 finalista(s)" in said and len(rows) == 2
        assert rows[0] == {
            "strategy": "Strategy 1",
            "identity": "id-Strategy 1",
            "mother": "Strategy 1",
            "sqx": str((Path(tmp) / "bank" / "Strategy 1.sqx").resolve()),
            "symbol": "USDJPY",
            "timeframe": "H1",
        }
        try:
            finalists.write("Pr", who.iloc[:0], Path(tmp))
            raise AssertionError("an empty list went on to step 26")
        except survivors.Done:
            pass
        assert json.loads((Path(tmp) / finalists.FILE).read_text()) == []


def test_step_26_is_its_agents_and_refuses_cleanly() -> None:
    """`mt5.verify.autopilot` is imported only when step 26 runs; a check that is not ok is
    a clean stop carrying its reasons, an ok one hands back the step's own line."""
    calls, params = (
        [],
        {"start": "2024-01-01", "end": "2026-08-30", "model": "m", "firms": ["f"]},
    )
    fake = types.ModuleType("mt5.verify.autopilot")
    fake.check = lambda project, rows, got, own_log=False: {
        "ok": got is params and bool(rows),
        "text": "",
        "reasons": ["sin cuenta guardada", "sin EA"],
    }
    fake.run = lambda project, rows, got, out: (
        calls.append((project, rows, got, out)) or "1 de 1"
    )
    import mt5.verify

    name, absent = "mt5.verify.autopilot", object()
    kept = sys.modules.get(name, absent), getattr(mt5.verify, "autopilot", absent)
    sys.modules[name] = mt5.verify.autopilot = fake
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / finalists.FILE).write_text("[]")
            try:
                finalists.verify("Pr", params, out)
                raise AssertionError("step 26 started with its check not ok")
            except survivors.Done as said:
                assert (
                    str(said) == "el paso 26 no se lanza: sin cuenta guardada; sin EA"
                )
            (out / finalists.FILE).write_text('[{"strategy": "S"}]')
            assert finalists.verify("Pr", params, out) == "1 de 1"
            assert calls == [("Pr", [{"strategy": "S"}], params, out)]
    finally:
        del sys.modules[name], mt5.verify.autopilot
        if kept[0] is not absent:
            sys.modules[name] = kept[0]
        if kept[1] is not absent:
            mt5.verify.autopilot = kept[1]


def test_window_wfc_command_signs_the_family() -> None:
    """Read-only, when the data root holds a batch with trades: the window's command for a blind look."""
    from core.paths import DATA

    if not list(
        (DATA / "strategyPermutations" / REAL).glob("*/variant_trades.parquet")
    ):
        print(
            "skipped the window's wfc command: no batch of this run holds variant_trades.parquet"
        )
        return
    argv = call.window("wfc", REAL, "", "USDJPY", ["Strategy 16.9.76"])[0]
    assert (
        argv[:2] == ["-m", "studies.optimisation.wfc.report"] and argv[-2] == "--family"
    )


if __name__ == "__main__":
    test_a_finalist_is_the_mothers_own_file()
    test_step_26_is_its_agents_and_refuses_cleanly()
    test_window_wfc_command_signs_the_family()
    print("ok")

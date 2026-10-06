#!/usr/bin/env python3
"""The autopilot's steps 23 to 26 with SQX and the studies replaced by stubs that record each
command and drop synthetic files where the real one would: the order of the two SQX batches,
the traded version picked at the ledger's stop percentile and never chosen, a mother without
a step-24 stop named and left out, the finalists' contract, and step 26's clean refusal."""

import json
import os
import sys
import tempfile
import time
import types
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import DATA
from ledger import thresholds
from pipeline.autopilot import call, closing, finalists, survivors, traded
from tests.test_autopilot_tail import WHO, patched

P = thresholds.value(traded.KEY)        # the owner's percentile, read and never written here
LEGS = ["WFC_Build", "WFC_OOS1", "WFC_OOS2"]
REAL = "Test_USDJPY_donchianUpperCrossUp_H1"


def mothers(folder: Path, names: list[str]) -> pd.DataFrame:
    """`survivors.mothers`' frame over empty files named after each mother."""
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / f"{name}.sqx").write_bytes(b"")
    return pd.DataFrame({"strategy": names, "identity": [f"id-{n}" for n in names],
                         "file": [folder / f"{n}.sqx" for n in names]})


def test_the_two_batches_in_order() -> None:
    """23: make → retest → keep → export of build and oos1 only → the reading → clear. 24:
    two passes, the second on the grid the first one's report wrote, each asking the door
    for oos2; the mothers' folder holds exactly this run's mothers."""
    ran, asked = [], []
    with tempfile.TemporaryDirectory() as tmp, \
            patched(closing, DATA=Path(tmp), wire=lambda *a: ran.append("wire"),
                    retest=lambda p, r, w: ran.append(f"retest {w.name}") or "ok"), \
            patched(call, run=lambda argv: ran.append(" ".join(argv[1:]))), \
            patched(closing.gate, allow=lambda *a: asked.append(a[:2])), \
            patched(survivors, about=lambda p: WHO):
        (Path(tmp) / "structural" / "Pr" / "mothers").mkdir(parents=True)
        (Path(tmp) / "structural" / "Pr" / "mothers" / "old.sqx").write_bytes(b"")
        who = mothers(Path(tmp) / "bank", ["Strategy 1", "Strategy 2"])
        closing.structural("Pr", "custodian", who, "R1")
        held = Path(tmp) / "structural" / "Pr" / "mothers"
        assert sorted(f.name for f in held.iterdir()) == ["Strategy 1.sqx", "Strategy 2.sqx"]
        assert [r.split()[0] for r in ran] == [
            "wire", "sqx.structural.make", "retest", "sqx.structural.keep",
            "sqx.export.export_retest", "studies.readings.structure.report",
            "sqx.variants.execute"]
        assert "--batch structure --databank WFC_Build --databank WFC_OOS1" in ran[4]
        assert "WFC_OOS2" not in ran[4] + ran[5] and ran[6].endswith("--clear")
        assert asked == [(23, "build"), (23, "oos1")]

        del ran[:], asked[:]
        closing.stop("Pr", "custodian", who, "R1")
        one = ["sqx.variants.stopgrid", "retest", "sqx.export.export_retest",
               "studies.closing.atrCalculator.report", "sqx.variants.execute"]
        assert [r.split()[0] for r in ran] == ["wire", *one, *one]
        grid = Path(tmp) / "atrCalculator" / "Pr" / "R1" / "pass1" / "estudios" / "atrCalculator"
        assert "--grid" not in ran[1] and ran[6].endswith(f"--grid {grid / 'stopgrid.csv'}")
        assert all(leg in ran[3] for leg in LEGS) and "--family fam" in ran[4]
        assert ran[4].endswith("pass1") and ran[9].endswith("pass2")
        assert asked == [(24, "build"), (24, "oos1"), (24, "oos2")]


def batch(root: Path, names: list[str]) -> Path:
    """A step-24 second pass as `stopgrid` and `execute` leave it: per mother the grid of two
    percentiles, three steps each, and the three legs exported after it ran."""
    folder = root / "atrCalculator" / "Pr" / "R1" / "pass2"
    (folder / "sqx").mkdir(parents=True)
    rows = [{"variant_id": f"S{m:02d}V{k:03d}", "strategy": name, "percentile": pct,
             "step": step, "x": pct / 50 + step / 10}
            for m, name in enumerate(names)
            for k, (pct, step) in enumerate((p, s) for p in (80.0, float(P)) for s in (-1, 0, 1))]
    pd.DataFrame(rows).to_parquet(folder / "manifest.parquet")
    (folder / "ran.json").write_text("{}")
    os.utime(folder / "ran.json", (time.time() - 60,) * 2)
    for leg in LEGS:
        out = root / "raw" / "Pr" / leg / "2026-10-02" / traded.TAG
        out.mkdir(parents=True)
        trades = pd.DataFrame([{**dict.fromkeys(traded.COLUMNS, 1.0), "Symbol": feed,
                                "strategy": r["variant_id"]}
                               for r in rows for feed in ("USDJPY_M1", "EURUSD_M1")])
        trades.to_parquet(out / "trades.parquet")
        pd.DataFrame({"strategy": [r["variant_id"] for r in rows],
                      "identity": "retested"}).to_csv(out / "identity.csv", index=False)
    return folder


def test_the_traded_version_is_the_ledgers_percentile() -> None:
    """Each mother's variant is step 0 of the ledger's percentile; one with no stop is named
    and left out while the rest go on; step 25 reads build as IS and oos1 as OOS, the main
    market only, keyed by the mother; the finalists carry the contract's seven fields."""
    ran = []
    with tempfile.TemporaryDirectory() as tmp, \
            patched(traded, DATA=Path(tmp),
                    harvest_dir=lambda p, d, day: Path(tmp) / "harvest" / p / d / day), \
            patched(call, run=lambda argv: ran.append(argv)), \
            patched(survivors, about=lambda p: WHO), \
            patched(finalists.sqxfile, identity=lambda f: f"grafted-{f.stem}"):
        who = mothers(Path(tmp) / "bank", ["Strategy 1", "Strategy 2", "Strategy 3"])
        assert traded.stops("Pr", who) == ([], list(who["strategy"]))      # no batch at all
        folder = batch(Path(tmp), ["Strategy 1", "Strategy 3"])
        picked, left = traded.stops("Pr", who)
        assert left == ["Strategy 2"]
        assert [(p["variant"], p["x"], p["percentile"]) for p in picked] == [
            ("S00V004", P / 50, P), ("S01V004", P / 50, P)]
        assert picked[0]["sqx"] == str(folder / "sqx" / "S00V004.sqx")

        said = traded.edge("Pr", who)
        assert "2 versión(es)" in said and "fuera: Strategy 2" in said
        assert [a[-1] for a in ran] == ["Strategy 1", "Strategy 3"]
        assert ran[0][:6] == ["-m", "studies.readings.edgeCost.report", "--project", "Pr",
                              "--databank", f"Stop_p{P}"]
        day = next((Path(tmp) / "harvest" / "Pr" / f"Stop_p{P}").iterdir())
        trades = pd.read_parquet(day / "trades.parquet")
        assert sorted(trades["sample"].unique()) == ["IS", "OOS"] and len(trades) == 4
        assert set(trades["identity"]) == {"id-Strategy 1", "id-Strategy 3"}
        metrics = pd.read_parquet(day / "metrics.parquet")
        assert metrics.index.name == "identity" and list(metrics["strategy"]) == [
            "Strategy 1", "Strategy 3"] and set(metrics["TimeFrame [IS]"]) == {"H1"}

        said = finalists.write("Pr", who, Path(tmp))
        rows = json.loads((Path(tmp) / finalists.FILE).read_text())
        assert "2 finalista(s)" in said and "fuera: Strategy 2" in said
        assert rows[0] == {"strategy": "Strategy 1 S00V004", "identity": "grafted-S00V004",
                           "mother": "Strategy 1", "sqx": picked[0]["sqx"], "symbol": "USDJPY",
                           "timeframe": "H1", "stop": {"percentile": P, "x": P / 50}}
        assert Path(rows[0]["sqx"]).is_absolute() and isinstance(rows[0]["stop"]["percentile"], int)

        # an export older than the batch's run, or of another batch, is refused
        os.utime(folder / "ran.json", (time.time() + 60,) * 2)
        try:
            traded.edge("Pr", who)
            raise AssertionError("read an export that is not the batch's")
        except SystemExit as said:
            assert "no es el export de la pasada 2" in str(said)

        # nobody with a stop: an empty list, and a clean end
        try:
            finalists.write("Pr", who.iloc[[1]], Path(tmp))
            raise AssertionError("an empty list went on to step 26")
        except survivors.Done as said:
            assert "fuera: Strategy 2" in str(said)
        assert json.loads((Path(tmp) / finalists.FILE).read_text()) == []


def test_step_26_is_its_agents_and_refuses_cleanly() -> None:
    """`mt5.verify.autopilot` is imported only when step 26 runs; a check that is not ok is
    a clean stop carrying its reasons, an ok one hands back the step's own line."""
    calls, params = [], {"start": "2024-01-01", "end": "2026-08-30", "model": "m", "firms": ["f"]}
    fake = types.ModuleType("mt5.verify.autopilot")
    fake.check = lambda project, rows, got: {"ok": got is params and bool(rows), "text": "",
                                             "reasons": ["sin cuenta guardada", "sin EA"]}
    fake.run = lambda project, rows, got, out: calls.append((project, rows, got, out)) or "1 de 1"
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
                assert str(said) == "el paso 26 no se lanza: sin cuenta guardada; sin EA"
            (out / finalists.FILE).write_text('[{"strategy": "S"}]')
            assert finalists.verify("Pr", params, out) == "1 de 1"
            assert calls == [("Pr", [{"strategy": "S"}], params, out)]
    finally:
        del sys.modules[name], mt5.verify.autopilot
        if kept[0] is not absent:
            sys.modules[name] = kept[0]
        if kept[1] is not absent:
            mt5.verify.autopilot = kept[1]


def test_on_the_recorded_run() -> None:
    """Read-only, on the 2026-09-30 hand run when the data root holds it: the three mothers'
    stops are the X of `x_p<percentile>` in step 24's own verdict.csv, and the window's
    command for a blind look signs the template family."""
    folder = DATA / "atrCalculator" / REAL / "pass2"
    if not (folder / "manifest.parquet").exists():
        return
    said = pd.read_csv(folder / "estudios" / "atrCalculator" / "verdict.csv").set_index("strategy")
    who = pd.DataFrame({"strategy": list(said.index), "identity": list(said["identity"]),
                        "file": None})
    picked, left = traded.stops(REAL, who)
    assert left == [] and len(picked) == len(said)
    for p in picked:
        assert abs(p["x"] - said.at[p["strategy"], f"x_p{P}"]) < 1e-4 and Path(p["sqx"]).exists()
    argv = call.window("wfc", REAL, "", "USDJPY", [said.index[0]])[0]
    assert argv[:2] == ["-m", "studies.optimisation.wfc.report"] and argv[-2] == "--family"


if __name__ == "__main__":
    test_the_two_batches_in_order()
    test_the_traded_version_is_the_ledgers_percentile()
    test_step_26_is_its_agents_and_refuses_cleanly()
    test_on_the_recorded_run()
    print("ok")

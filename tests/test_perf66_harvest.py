"""Encargo 66 store loop: harvesting the days outside the loop, aliases once and the deferred distributions fold into a save."""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.archive import collect, harvest
from core.store import late, save

# ---------------------------------------------------------------- store: days outside the loop, aliases once

def harvest_tree(root: Path, days: int, ids: list[str]) -> Path:
    """A harvest tree of `days` result days holding the given identities."""
    for d in range(days):
        folder = root / "harvest" / "P" / "Results" / f"2026-10-0{d + 1}"
        folder.mkdir(parents=True)
        rng = np.random.default_rng(d)
        rows = [(i, k, float(rng.normal())) for i in ids for k in range(5)]
        frame = pd.DataFrame(rows, columns=["identity", "k", "v"])
        frame.set_index("identity").to_parquet(folder / "metrics.parquet")
        frame.sample(frac=1, random_state=d).to_parquet(folder / "equity.parquet")
        frame.to_parquet(folder / "trades.parquet")
    return root


def test_the_harvest_loop_with_the_days_outside_cuts_the_same_rows_reading_each_file_once(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Days outside the loop cut the same rows, reading each file once."""
    ids = [f"id{i}" for i in range(8)]
    monkeypatch.setattr(save, "DATA", harvest_tree(tmp_path / "data", 3, ids))
    reads = []
    real = pd.read_parquet
    monkeypatch.setattr(collect.pd, "read_parquet", lambda *a, **k: reads.append(1) or real(*a, **k))

    def old_loop(i: str) -> dict:
        """Today's loop: survivor outside, days inside."""
        return save.harvest_cut("P", i, tmp_path / "old" / i)

    harvest._PARTS.clear()
    t0 = time.perf_counter()
    old = {i: old_loop(i) for i in ids}
    t_old, n_old = time.perf_counter() - t0, len(reads)
    reads.clear()
    harvest._PARTS.clear()
    t0 = time.perf_counter()
    new = save.harvest_all("P", ids, tmp_path / "new")
    t_new, n_new = time.perf_counter() - t0, len(reads)
    print(f"\nreads {n_old} -> {n_new}; {t_old:.3f}s -> {t_new:.3f}s")
    assert n_new == 9 < n_old
    for i in ids:
        assert [(d, s, c) for d, s, _, c in old[i]] == [(d, s, c) for d, s, _, c in new[i]]
        for (_, _, fo, _), (_, _, fn, _) in zip(old[i], new[i]):
            for name in ("metrics", "equity", "trades"):
                assert (fo / f"{name}.parquet").read_bytes() == (fn / f"{name}.parquet").read_bytes()


def test_aliases_with_the_mothers_handed_in_equal_aliases_that_walk_the_lineage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Aliases with the mothers handed in equal those that walk the lineage."""
    day = tmp_path / "raw" / "P" / "WFM" / "2026-10-08"
    day.mkdir(parents=True)
    (day / "lineage.csv").write_text("strategy,identity,mother\na,W,M\nb,M,W\nc,X,M\n")
    monkeypatch.setattr(late, "DATA", tmp_path)
    mother = late.mothers("P")
    for i in ("M", "W", "X", "Z"):
        assert late.aliases("P", i, mother) == late.aliases("P", i)


def test_an_archive_folds_the_deferred_distributions_before_it_copies_the_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`collect.freeze` folds the deferred distributions of every study folder, whoever calls it."""
    from core.archive import collect
    from core.study import draws
    folder = tmp_path / "reports" / "P" / "Results" / "2026-10-10" / "gate"
    folder.mkdir(parents=True)
    row = draws.record("t", "m", 0.5, np.arange(10.0), identity="i", strategy="S1")
    draws.merge(folder, [row], defer=True)
    assert not (folder / draws.FILE).exists()           # what a file-by-name copy of the folder would miss
    monkeypatch.setattr(collect, "DATA", tmp_path)
    collect.freeze("P", "i", tmp_path / "out")
    assert (folder / draws.FILE).exists() and not list((folder / draws.SHARDS).glob("*.parquet"))


def test_a_side_is_whole_only_if_every_sqx_file_was_taken(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two files of one identity collapse in `collect.index`: the side is not whole, so `export_trades` still runs."""
    import argparse
    from studies.screening.gate import harvest
    for bank, n in (("Results", 2), ("OOS", 1)):
        (tmp_path / bank).mkdir()
        for i in range(n):
            (tmp_path / bank / f"S{i}.sqx").write_bytes(b"x")
    monkeypatch.setattr(harvest, "databank_dir", lambda p, d, install: tmp_path / d)
    monkeypatch.setattr(harvest, "export_dir", lambda p, d, day: tmp_path / "raw" / d)
    a = argparse.Namespace(project="P", databank="Results", oos_databank="OOS", exports=True)
    taken = {"IS": [tmp_path / "Results" / "S0.sqx"], "OOS": [tmp_path / "OOS" / "S0.sqx"]}   # 1 identity, 2 files in IS
    assert set(harvest.whole_sides(a, taken, tmp_path)) == {"OOS"}
    a.exports = False
    assert harvest.whole_sides(a, taken, tmp_path) == {}


def test_the_databank_export_manifest_is_dated_at_the_harvest_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`harvest.export` writes the manifest with `since=began` and the three files `export_trades` leaves."""
    import argparse
    from sqx.export import export_trades
    from studies.screening.gate import harvest
    f = tmp_path / "S0.sqx"
    f.write_bytes(b"x")
    seen: dict = {}
    monkeypatch.setattr(harvest.sqxfile, "symbol", lambda p: ("EURUSD", "EURUSD_LOM_M30"))
    monkeypatch.setattr(harvest.collect, "identities", lambda files: {p: "id" for p in files})
    monkeypatch.setattr(export_trades, "lineage", lambda *a: None)
    monkeypatch.setattr(harvest.manifest, "write", lambda *a, **k: seen.update(k))
    out = tmp_path / "out"
    out.mkdir()
    harvest.export(out, argparse.Namespace(project="P"), "Results", [f], {"trades": 1}, tmp_path, 123.5)
    assert seen == {"since": 123.5}
    assert (out / "identity.csv").read_text() == "strategy,identity\nS0,id\n"
    assert (out / "timeframes.csv").read_text() == "strategy,timeframe\nS0,M30\n"


def _main_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, n_files: int = 1) -> tuple:
    """`harvest.main` with every outside call faked: one pair, `n_files` .sqx per databank."""
    import sys
    from studies.screening.gate import harvest
    banks = {}
    for bank in ("Results", "OOS"):
        (tmp_path / bank).mkdir()
        banks[bank] = [tmp_path / bank / f"S{i}.sqx" for i in range(n_files)]
        for f in banks[bank]:
            f.write_bytes(b"x")
    raw = {b: tmp_path / "raw" / b for b in banks}
    for r in raw.values():
        r.mkdir(parents=True)
        (r / "manifest.json").write_text("{}")
    seen: dict = {"manifests": [], "exports": 0}

    def tables(taken: dict, work: Path, whole: dict) -> dict:
        """Fake `harvest.tables`: record the manifests present, return one frame pair."""
        seen["manifest_at_tables"] = {b: (r / "manifest.json").exists() for b, r in raw.items()}
        frame = pd.DataFrame({"identity": ["i"], "v": [1]})
        side = {"metrics": pd.DataFrame({"x": [1]}, index=["i"]), "trades": frame, "equity": frame,
                "packed": {}, "sample": "s"}
        return {"IS": side, "OOS": side}

    monkeypatch.setattr(harvest, "databank_dir", lambda p, d, install: tmp_path / d)
    monkeypatch.setattr(harvest, "export_dir", lambda p, d, day: raw[d])
    monkeypatch.setattr(harvest, "harvest_dir", lambda p, d, day: tmp_path / "harvest")
    monkeypatch.setattr(harvest, "MASTER", tmp_path)
    monkeypatch.setattr(harvest.collect, "index", lambda d: {"i": banks[d.name][0]})
    monkeypatch.setattr(harvest.pairing, "pair", lambda b, o: ({"i": (b["i"], o["i"])}, {}, []))
    monkeypatch.setattr(harvest.collect, "tables", tables)
    monkeypatch.setattr(harvest.fanout, "run", lambda fn, d, w: [(k, "shape") for k in d])
    monkeypatch.setattr(harvest, "export", lambda *a: seen.__setitem__("exports", seen["exports"] + 1))
    monkeypatch.setattr(harvest.manifest, "write", lambda *a, **k: seen["manifests"].append(k))
    monkeypatch.setattr(sys, "argv", ["h", "--project", "P", "--databank", "Results", "--oos-databank", "OOS", "--exports"])
    return harvest, seen


def test_exports_unsign_the_whole_sides_before_packing_and_the_cosecha_is_dated_at_began(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A kill while `trades.parquet` is rewritten must leave the side without a manifest; the cosecha's own carries `since`."""
    harvest, seen = _main_env(tmp_path, monkeypatch)
    harvest.main()
    assert seen["manifest_at_tables"] == {"Results": False, "OOS": False}
    assert seen["exports"] == 2
    assert len(seen["manifests"]) == 1 and isinstance(seen["manifests"][0]["since"], float)


def test_a_side_with_no_sqx_is_never_whole(tmp_path: Path) -> None:
    """Zero taken of zero files is not «whole»: `export` would index `files[0]`."""
    import argparse
    from studies.screening.gate import harvest
    (tmp_path / "Results").mkdir()
    a = argparse.Namespace(project="P", databank="Results", oos_databank="Results", exports=True)
    import unittest.mock as um
    with um.patch.object(harvest, "databank_dir", lambda p, d, i: tmp_path / d), \
            um.patch.object(harvest, "export_dir", lambda p, d, day: tmp_path / "raw"):
        assert harvest.whole_sides(a, {"IS": [], "OOS": []}, tmp_path) == {}


def _full(gate: object, block: int, given: dict) -> dict:
    """A block holding every statistic the view reads (1.0) but the two SQX stopped storing, unless `given` has them."""
    return {**{k: 1.0 for _, k in gate.VIEW[block] if k not in ("ParameterCount", "DoFRatio")}, **given}


def test_any_other_missing_statistic_still_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3: only DoFRatio / ParameterCount may be absent; a block lacking ProfitFactor raises KeyError, never reads 0."""
    from studies.screening.gate import collect as gate
    block = _full(gate, 10, {"NumberOfTrades": 30.0})
    del block["ProfitFactor"]
    monkeypatch.setitem(gate._STAGED, "S", Path("S.sqx"))
    with pytest.raises(KeyError, match="ProfitFactor"):
        gate.metrics({"S": ({10: block, 20: {}}, None, "H1")})


def test_the_gate_metrics_read_a_strategy_whose_sqx_carries_no_dof_ratio_nor_parameter_count(monkeypatch: pytest.MonkeyPatch) -> None:
    """🔬 2026-10-13: the conductor stopped storing both on 2026-10-06; `Test_Perf66_A` died on `KeyError: 'DoFRatio'`."""
    from core import sqxfile
    from studies.screening.gate import collect as gate
    stats = {"S": {10: _full(gate, 10, {"NumberOfTrades": 30.0}), 20: {}}}      # no DoFRatio, no ParameterCount
    monkeypatch.setitem(gate._STAGED, "S", Path("S.sqx"))
    monkeypatch.setattr(sqxfile, "param_count", lambda f: 4)
    got, label = gate.metrics({"S": (stats["S"], None, "H1")})
    assert label == "(IS)" and got.loc["S", "Param Count"] == 4 and got.loc["S", "DoF Ratio"] == 7.5


def test_the_gate_metrics_ignore_sqxs_own_param_count_and_dof_ratio_when_the_export_carries_them(monkeypatch: pytest.MonkeyPatch) -> None:
    """Owner P9=A: Python's value always wins, even when SQX's export carries a different one (OPEN #86)."""
    from core import sqxfile
    from studies.screening.gate import collect as gate
    stats = {"S": {10: _full(gate, 10, {"NumberOfTrades": 30.0, "ParameterCount": 9.0, "DoFRatio": 3.3}), 20: {}}}
    monkeypatch.setitem(gate._STAGED, "S", Path("S.sqx"))
    monkeypatch.setattr(sqxfile, "param_count", lambda f: 4)
    got, _ = gate.metrics({"S": (stats["S"], None, "H1")})
    assert got.loc["S", "Param Count"] == 4 and got.loc["S", "DoF Ratio"] == 7.5

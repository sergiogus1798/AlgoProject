"""Encargo 66, the data reviewer's findings: each test fails on the code before the fix."""

import concurrent.futures as cf
import hashlib
import json
import types
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from core import sqxretest
from core.archive import collect, harvest
from core.store import write
from core.study import draws


# 1. the store's prefix -> folder cache -------------------------------------------------------------
def test_a_folder_made_right_after_a_listing_is_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A strategy folder created inside the same clock tick as the listing is still found."""
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path)
    write._SEEN.clear()
    (tmp_path / "c1" / "A 11111111").mkdir(parents=True)
    write.folder("11111111")                     # lists
    for i in range(300):
        ident = f"{i + 2:08d}"
        (tmp_path / "c1" / f"S{i} {ident}").mkdir()
        assert write.folder(ident, "cX", "nm") == tmp_path / "c1" / f"S{i} {ident}"


def test_put_sqx_twice_in_a_cell_leaves_one_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Saving a strategy, then another, then the first again: no manifest under `_/`."""
    monkeypatch.setattr(write, "store_dir", lambda: tmp_path)
    write._SEEN.clear()
    sqx = tmp_path / "in.sqx"
    with zipfile.ZipFile(sqx, "w") as z:
        z.writestr("x", "x")
    monkeypatch.setattr(write.sqxfile, "identity", lambda path: "abcdef0123" if Path(path) == sqx or True else "")
    write.put_sqx(sqx, "cell", {"strategy": "n"})
    write.put_sqx(sqx, "cell", {"strategy": "n"})
    assert not (tmp_path / "_").exists()
    assert len(list(tmp_path.glob("*/*/manifest.json"))) == 1


# 2 + 4. the archive ---------------------------------------------------------------------------------
def test_freeze_folds_deferred_draws_for_every_caller(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`collect.freeze` consolidates each study folder itself."""
    folder = tmp_path / "reports" / "P" / "Results" / "2026-10-10" / "gate"
    folder.mkdir(parents=True)
    draws.merge(folder, [draws.record("t", "m", 0.5, np.arange(10.0), identity="i", strategy="S1")], defer=True)
    monkeypatch.setattr(collect, "DATA", tmp_path)
    collect.freeze("P", "i", tmp_path / "out")
    assert (folder / draws.FILE).exists() and not list((folder / draws.SHARDS).glob("*.parquet"))


def test_release_empties_both_caches(tmp_path: Path) -> None:
    """After a save or an archive nothing stays cached; the caches take threads."""
    f = tmp_path / "a.json"
    f.write_text("{}")
    collect._json(f)
    harvest._PARTS["x"] = (1, None, None, None, None)
    assert collect._READ
    collect.release()
    harvest.release()
    assert not collect._READ and not harvest._PARTS
    with cf.ThreadPoolExecutor(8) as ex:
        assert list(ex.map(lambda _: collect._json(f), range(64))) == [{}] * 64


# 3. the 16.5 marker ---------------------------------------------------------------------------------
def _variants_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, live: bool = False) -> tuple:
    """`variants` with every outside call faked; returns (module, state, calls)."""
    from pipeline.autopilot import variants
    parent = tmp_path / "x" / "strategies" / "A.sqx"
    parent.parent.mkdir(parents=True)
    parent.write_bytes(b"one")
    brief = tmp_path / "design_brief_A.json"
    brief.write_text(json.dumps({"strategy": "A", "source": str(tmp_path / "x" / "spp")}))
    state = {"cfg": {"pilot": 1}, "legs": [{"databank": "d"}], "card": {"spread": 1}, "mother": "m1"}
    calls: list[str] = []
    monkeypatch.setattr(variants, "briefs", lambda project: [brief])
    monkeypatch.setattr(variants, "variants_dir", lambda project, strategy: tmp_path / strategy)
    monkeypatch.setattr(variants.live, "mine", lambda role: live)
    monkeypatch.setattr(variants.registry, "rows", lambda: [{"name": "P", "symbol": "S"}])
    monkeypatch.setattr(variants.inputs, "load", lambda: state["cfg"])
    monkeypatch.setattr(variants.legmod, "legs", lambda *a: state["legs"])
    monkeypatch.setattr(variants.assetdata, "load", lambda s: state["card"])
    monkeypatch.setattr(variants.sqxfile, "identity", lambda p: state["mother"])
    monkeypatch.setattr(variants, "wire", lambda *a, **k: calls.append("wire"))
    monkeypatch.setattr(variants, "_py", lambda *a: calls.append(a[0]))
    return variants, state, calls


@pytest.mark.parametrize("key,new", [("cfg", {"pilot": 0}), ("legs", [{"databank": "e"}]),
                                     ("card", {"spread": 2}), ("mother", "m2")])
def test_a_changed_input_other_than_the_brief_recomputes_16_5(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, key: str, new: object) -> None:
    """Config, legs, cost card and the mother's file are all in the marker's hash."""
    variants, state, calls = _variants_env(monkeypatch, tmp_path)
    variants.run("P", "r")
    variants.run("P", "r")
    assert calls.count("sqx.variants.make") == 1
    state[key] = new
    variants.run("P", "r")
    assert calls.count("sqx.variants.make") == 2


def test_live_with_every_mother_finished_never_wires(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A second live run over finished mothers performs zero `wire` calls."""
    variants, _, calls = _variants_env(monkeypatch, tmp_path, live=True)
    variants.run("P", "r")
    assert calls.count("wire") == 2                # strip, restore
    calls.clear()
    variants.run("P", "r")
    assert "wire" not in calls and "sqx.variants.make" not in calls


# 5. days.py int16 -------------------------------------------------------------------------------------
def test_opens_summed_as_int16_do_not_wrap() -> None:
    """The real dtype of `opens` (int16): a day of 1,440 minutes opening 30 each is 43,200."""
    from portfolio.common.construct.equity import days
    n = 1440
    t = pd.date_range("2026-01-05", periods=n, freq="min").values
    zero = np.zeros(n)
    path = {"t": t, "worst": zero, "best": zero, "close": zero, "realised": zero, "open": zero,
            "opens": np.full(n, 30, np.int16)}
    days._FRAME_CACHE.clear()
    assert int(days.server_days(path, "UTC", "UTC")["opened"].iloc[0]) == 43200


# 6. oos2Reading inputs ---------------------------------------------------------------------------------
def test_mother_trades_keeps_the_files_row_labels(tmp_path: Path) -> None:
    """The filtered read returns the labels the whole-file mask gave."""
    from studies.optimisation.oos2Reading import inputs as oos2
    n = 60
    t = pd.DataFrame({"variant_id": np.random.default_rng(0).choice(["v1", "v2"], n),
                      "Open time": pd.date_range("2025-01-01", periods=n, freq="h")})
    t["Close time"] = t["Open time"] + pd.Timedelta("30min")
    t.to_parquet(tmp_path / oos2.TRADES)
    pd.DataFrame({"variant_id": ["v1", "v2"], "origin": [False, True]}).to_parquet(tmp_path / "manifest.parquet")
    span = (pd.Timestamp("2025-01-01"), pd.Timestamp("2026-01-01"))
    old = t[t["variant_id"] == "v2"]
    pd.testing.assert_frame_equal(oos2.mother_trades(tmp_path, span), old)


# 7. sqxretest.stored -----------------------------------------------------------------------------------
def test_stored_and_simulations_agree_with_a_gap_and_a_repeated_number(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulations numbered 0, 1, 5, and number 5 twice under the folder: both count 3."""
    path = tmp_path / "s.sqx"
    base = "Results/Main: X"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{base}/{sqxretest.RESULTS}", "<x/>")
        for n in (0, 1, 5):
            z.writestr(f"{base}/MonteCarloRetest_Simulation{n}Orders.bin", b"")
        z.writestr(f"{base}/old/MonteCarloRetest_Simulation5Orders.bin", b"")
    monkeypatch.setattr(sqxretest, "_orders", lambda raw, member: np.array([1.0]))
    assert sqxretest.stored(path) == len(sqxretest.simulations(path)["index"]) == 3


# 9. mt5 reconcile ---------------------------------------------------------------------------------------
def test_reconcile_cuts_the_rebuild_to_the_week_and_equals_the_old_logic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rebuilding MAE/MFE only for trades near the week equals rebuilding all of them (the old code)."""
    from mt5.reconcile import judge, run, week as weeks
    inst = {"tick_size": 0.01, "point_value": 100.0}
    cfg = yaml.safe_load(run.CONFIG.read_text(encoding="utf-8"))
    cfg["pairing"]["entry_tolerance_bars"] = 1
    opens = pd.to_datetime(["2026-09-06 20:00", "2026-09-13 22:00", "2026-09-14 06:00", "2026-09-15 12:00",
                            "2026-09-20 23:00", "2026-09-21 02:00", "2026-10-30 09:00"])
    close = opens + pd.Timedelta(hours=5)       # the second runs into the week; the fifth runs out of it
    sqx = pd.DataFrame({"Ticket": range(1, 8), "Type": ["Buy", "Sell"] * 3 + ["Buy"], "Open time": opens,
                        "Open price": 150.0 + np.arange(7), "Size": 0.1, "Close time": close,
                        "Close price": 150.4 + np.arange(7), "Profit/Loss": np.arange(7.0)})
    live = sqx.drop(columns="Ticket").iloc[[1, 2, 3, 4]].assign(Size=0.3)
    minutes = pd.date_range("2026-09-01", "2026-11-01", freq="1min")
    rng = np.random.default_rng(1)
    mid = 150 + np.cumsum(rng.normal(0, 0.02, len(minutes)))
    bars = pd.DataFrame({"High": mid + 0.05, "Low": mid - 0.05}, index=minutes)
    want_all = types.SimpleNamespace(bounds=lambda w: (pd.Timestamp("1900-01-01"), pd.Timestamp("2200-01-01")), cut=weeks.cut)
    new = judge.reconcile(sqx, live, "2026-W38", "H1", inst, ("EETUS", "EETUS"), bars, cfg)
    monkeypatch.setattr(judge, "weeks", want_all)       # old logic: rebuild every trade, cut after
    old = judge.reconcile(sqx, live, "2026-W38", "H1", inst, ("EETUS", "EETUS"), bars, cfg)
    for key in ("pairs", "sqx_only", "live_only"):
        pd.testing.assert_frame_equal(new[key], old[key])
    assert new["summary"] == old["summary"]


def test_a_failing_archive_still_releases_the_caches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`archive` raising halfway must not leave parsed reports in the daemon."""
    from ui.daemon.strategy import archive_write
    collect._READ["x"] = 1
    harvest._PARTS["x"] = (1, None, None, None, None)
    monkeypatch.setattr(archive_write, "archive_dir", lambda: tmp_path)
    monkeypatch.setattr(archive_write, "_source", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        archive_write.archive("P", "Results", "id", "8", family="f")
    assert not collect._READ and not harvest._PARTS

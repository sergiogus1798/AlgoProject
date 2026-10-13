"""Known answers for the audited bugs fixed in encargo 66: each test failed before its fix."""

import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import barstore
from core.study import draws
from core.surface import plateau
from ledger import cells, record
from pipeline.autopilot import plan
from pipeline.campaign import run as campaign
from portfolio.common.construct.equity import excursions
from sqx.variants import legs as legmod, united, varianttrades
from studies.data.feedQuality import touch
from studies.readings.monkey import many
from studies.research.memory import attempts
from tests.test_ledger_cells import setup as cells_setup


def _merge_one(args: tuple[str, str]) -> None:
    """One process merges one strategy's row."""
    folder, name = args
    draws.merge(Path(folder), [draws.record("t", "z", 1.0, np.arange(50.0), strategy=name)])


def test_concurrent_merges_keep_every_strategy(tmp_path: Path) -> None:
    """Eight `--strategy` processes merging into one report folder lose none of the rows."""
    names = [f"s{i}" for i in range(16)]
    with mp.get_context("fork").Pool(8) as pool:
        pool.map(_merge_one, [(str(tmp_path), n) for n in names], chunksize=1)
    assert sorted(pd.read_parquet(tmp_path / draws.FILE)["strategy"]) == sorted(names)


def test_united_drawdown_peak_starts_at_zero() -> None:
    """A curve that opens with a loss has its deepest trough counted from the start balance."""
    daily = pd.DataFrame({"v": [-100.0, -100.0, 0.0, 50.0]})
    assert united.from_curves(daily)["Drawdown"].iloc[0] == 200.0


def test_reopen_reads_the_newest_folder_with_a_status_and_a_cut_run(tmp_path: Path) -> None:
    """A refused retry's empty folder and a run killed mid-step (no FIN) both reopen their step."""
    def data() -> dict:
        """A rail whose step 16.5 reads as done."""
        return {"steps": [{"n": "16.5", "kind": "sqx", "state": "done",
                           "tests": [{"state": "done"}]}]}
    old, empty, out = tmp_path / "1", tmp_path / "2", tmp_path / "3"
    for d in (old, empty, out):
        d.mkdir()
    (old / "estado.txt").write_text("10:00:00 [4/9] paso 16.5 · variants\n", encoding="utf-8")
    assert plan.reopen(data(), out)["steps"][0]["state"] == "pending"
    (old / "estado.txt").write_text("10:00:00 FIN · 9 acciones · resumen en x\n", encoding="utf-8")
    assert plan.reopen(data(), out)["steps"][0]["state"] == "done"


def test_a_rejudged_step_8_neither_lowers_screened_nor_signs_again(monkeypatch: object,
                                                                    tmp_path: Path) -> None:
    """Resuming with step 8 done judges the cut bank: `screened` stays at its first value."""
    cells_setup(monkeypatch, tmp_path)
    assert cells.note("Test_A_1", 10000) is True
    assert cells.note("Test_A_1", 300) is False
    assert cells._judged()["Test_A_1"]["screened"] == "10000"


def test_a_keep_that_raises_ends_the_cell_failed(monkeypatch: object) -> None:
    """The cell is not left `running` for `following()` to pick forever."""
    marks = []
    cell = {"project": "Test_X", "palette": "p", "template": "t", "symbol": "S", "timeframe": "H1",
            "direction": "long"}
    monkeypatch.setattr(campaign, "_attempt", lambda *a, **k: 0)
    monkeypatch.setattr(campaign, "_command", lambda *a, **k: [])
    monkeypatch.setattr(campaign, "_newest", lambda p: None)
    monkeypatch.setattr(campaign.keep, "keep", lambda *a: 1 / 0)
    monkeypatch.setattr(campaign.ledger, "mark", lambda c, state, **f: marks.append((state, f)))
    assert campaign.once(cell, {}) == "failed"
    assert marks[-1][0] == "failed" and "ZeroDivisionError" in marks[-1][1]["error"]


def test_variant_trades_find_the_export_whatever_the_day(monkeypatch: object, tmp_path: Path) -> None:
    """The reader takes the export that just ran, not `date.today()`'s folder."""
    for leg in legmod.legs():
        folder = tmp_path / leg["databank"] / "2000-01-02" / varianttrades.TAG
        folder.mkdir(parents=True)
        pd.DataFrame({"Symbol": ["F"], "strategy": ["a(1)"]}).to_parquet(folder / "trades.parquet")
    monkeypatch.setattr(varianttrades, "export_dir",
                        lambda p, db, day, tag="": tmp_path / db / day / tag if day else tmp_path / db)
    monkeypatch.setattr(varianttrades, "main_feed", lambda p: "F")
    work = tmp_path / "work"
    work.mkdir()
    assert varianttrades.gather(work, "Test_X") == len(legmod.legs())


def test_monkey_panel_with_no_pair_long_enough_says_so(capsys: object) -> None:
    """Every pair under `min_trades` is a clean message, not an IndexError."""
    sample = {("a", "M"): pd.DataFrame({"x": [1, 2]})}
    with pytest.raises(SystemExit, match="nada que medir"):
        many.run(sample, {}, {"verdict": {"min_trades": 5}}, 1)
    assert "1 de 1 pares" in capsys.readouterr().out


def test_one_candidate_has_no_sharpe_std_to_write() -> None:
    """NaN is not JSON: with one score the spread is None."""
    got = record.distribution(np.array([1.5]))
    assert got["sharpe_std"] is None
    json.dumps(got, allow_nan=False)


def test_projects_csv_is_replaced_whole(monkeypatch: object, tmp_path: Path) -> None:
    """The per-cell file goes through a rename, so a reader never meets it empty."""
    cells_setup(monkeypatch, tmp_path)
    seen = []
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda a, b: (seen.append(b), real(a, b))[1])
    cells.note("Test_A_1", 40)
    assert tmp_path / "projects.csv" in seen


def test_bar_cache_is_written_whole(monkeypatch: object, tmp_path: Path) -> None:
    """The per-timeframe parquet lands by rename: an interrupted write leaves no final name."""
    idx = pd.date_range("2024-01-01", periods=120, freq="min")
    m1 = pd.DataFrame({c: 1.0 for c in barstore.AGG}, index=idx)
    cache = tmp_path / "H1.parquet"
    monkeypatch.setattr(barstore, "current", lambda f: f)
    monkeypatch.setattr(barstore, "library", lambda: {"F": {"version": "v"}})
    monkeypatch.setattr(barstore, "bar_cache", lambda *a: cache)
    monkeypatch.setattr(barstore, "source", lambda f: m1)
    seen = []
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda a, b: (seen.append(b), real(a, b))[1])
    barstore.read("F", "H1")
    assert seen == [cache] and cache.exists()


def test_a_trade_before_the_first_bar_has_no_excursion() -> None:
    """Its MAE and MFE are NaN; the panel goes on."""
    bars = pd.DataFrame({"High": [2.0, 2.0], "Low": [1.0, 1.0]},
                        index=pd.to_datetime(["2024-01-01 10:00", "2024-01-01 10:01"]))
    trades = pd.DataFrame({"Open time": pd.to_datetime(["2024-01-01 09:00"]),
                           "Close time": pd.to_datetime(["2024-01-01 10:01"]),
                           "Type": ["Buy"], "Size": [1.0], "Open price": [1.5]})
    got = excursions.rebuild(trades, bars, 1.0)
    assert got["mae"].isna().all() and got["mfe"].isna().all()


def test_half_of_a_negative_best_is_below_it() -> None:
    """With every value negative the half-max line is best - |best| / 2, as plateau_fraction's."""
    assert plateau.above_half_max(np.array([-1.0, -1.2, -10.0])) == pytest.approx(2 / 3)


def test_a_trade_on_the_first_bar_has_no_bar_before_it() -> None:
    """Its signal bar is its own, not the last bar of the day (index -1)."""
    index = pd.date_range("2024-01-01", periods=5, freq="h")
    trades = pd.DataFrame({"Open time": [index[0]], "Close time": [index[2]]})
    got = touch.bars(trades, index, "H1")
    assert got["signal"][0][0] == got["entry"][0][0]


def test_research_projects_are_attempts_too() -> None:
    """Rule 6 names three prefixes."""
    assert attempts.NAME.match("Research_USATEC_breakout_H1")


def test_a_simple_project_gets_a_cell_per_side() -> None:
    """`simple:long` and `simple:short` land in cells of their own (owner, 2026-10-13)."""
    from core.store import save
    row = {"symbol": "DAX40", "timeframe": "H1"}
    assert save.cell_of(row | {"template": "simple:long"}) == "DAX40_H1_simple_long"
    assert save.cell_of(row | {"template": "simple:short"}) == "DAX40_H1_simple_short"
    assert save.cell_of(row | {"template": "lib/ruptura/t.sqx"}) == "DAX40_H1_ruptura"


def test_a_resumed_16_5_skips_a_finished_mother_and_redoes_a_changed_brief(monkeypatch: object,
                                                                         tmp_path: Path) -> None:
    """The marker holds the brief's hash: same brief, no rerun; another brief, rerun."""
    from pipeline.autopilot import variants
    brief = tmp_path / "design_brief_A.json"
    brief.write_text(json.dumps({"strategy": "A", "source": str(tmp_path / "x" / "spp"), "v": 1}))
    calls: list[str] = []
    monkeypatch.setattr(variants, "wire", lambda *a, **k: None)
    monkeypatch.setattr(variants, "briefs", lambda project: [brief])
    monkeypatch.setattr(variants, "variants_dir", lambda project, strategy: tmp_path / strategy)
    monkeypatch.setattr(variants.live, "mine", lambda role: False)
    monkeypatch.setattr(variants.legmod, "legs", lambda *a: [])
    monkeypatch.setattr(variants, "_py", lambda *a: calls.append(a[0]))
    variants.run("P", "r")
    first = calls.count("sqx.variants.make")
    variants.run("P", "r")
    assert (first, calls.count("sqx.variants.make")) == (1, 1)
    brief.write_text(json.dumps({"strategy": "A", "source": str(tmp_path / "x" / "spp"), "v": 2}))
    variants.run("P", "r")
    assert calls.count("sqx.variants.make") == 2


def _note_one(args: tuple[str, int]) -> None:
    """One process notes one run of the same input under its own config."""
    import time
    from ledger import tried
    folder, i = args
    read = tried.read
    tried.read = lambda study: (lambda f: (time.sleep(0.2), f)[1])(read(study))   # widen the race
    tried.path = lambda study, p=Path(folder): p / f"{study}.jsonl"
    tried.note_run("S", "m", "in", f"cfg{i}", "t")


def test_eight_processes_noting_runs_keep_eight_rows_in_one_search(tmp_path: Path) -> None:
    """Eight forked processes noting a run each leave eight rows under one search id."""
    from ledger import tried
    with mp.get_context("fork").Pool(8) as pool:
        pool.map(_note_one, [(str(tmp_path), i) for i in range(8)], chunksize=1)
    rows = [json.loads(x) for x in (tmp_path / "S.jsonl").read_text().splitlines()]
    assert len(rows) == 8 and len({r["search_id"] for r in rows}) == 1

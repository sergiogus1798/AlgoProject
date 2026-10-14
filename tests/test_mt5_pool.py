"""The validated pool's register on the real checks on disk: rebuilt rows, latest verdict wins, append-only."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.verify import pool  # noqa: E402

# Real checks of 2026-09-30 (USDJPY H1, ohlc_m1): 16.9.76 and 10.9.72 validate on FTMO and
# not on Hantec, 21.9.59 on neither; the first two XAUUSD attempts crashed before judging.
PASSED = "20260930-142145_Strategy_10_9_72"
FAILED = "20260930-141929_Strategy_21_9_59"
CRASHED = "20260929-194218_Strategy_3_48_75"
ID_PASSED = "746c8da7383ed634aa93bebeb8b02b973d23d08b429e191e77a82e847c03066b"


@pytest.fixture
def register(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The register in a temp folder; the checks on disk are only read."""
    monkeypatch.setattr(pool, "ROOT", tmp_path / "pool")
    return tmp_path / "pool"


def test_a_finished_check_gives_one_row_per_judged_firm() -> None:
    """Run.json and result.json become the register's columns, the firm's own verdict word kept."""
    rows = {r["firm"]: r for r in pool.rows_of(pool.RUNS / PASSED)}
    assert set(rows) == {"ftmo", "hantec"}
    ftmo = rows["ftmo"]
    assert set(ftmo) == set(pool.COLUMNS)
    assert (ftmo["identity"], ftmo["verdict"], rows["hantec"]["verdict"]) == (
        ID_PASSED,
        "pass",
        "fail",
    )
    assert (ftmo["symbol"], ftmo["timeframe"], ftmo["model"]) == (
        "USDJPY",
        "H1",
        "ohlc_m1",
    )
    assert (ftmo["window_from"], ftmo["window_to"]) == ("2022-06-01", "2026-09-24")
    assert (
        ftmo["verified_on"] == "2026-09-30T14:24:01"
        and ftmo["config_hash"] == "a3597d820eae2ca4"
    )
    assert ftmo["sqx_trades"] == 398 and 0.96 < ftmo["row_1"] < 0.97
    # the thresholds of that day, read off the ledger row the check left, not off today's file
    assert (
        len(ftmo["thresholds_hash"]) == 16
        and ftmo["thresholds_hash"] == rows["hantec"]["thresholds_hash"]
    )


def test_a_check_without_verdict_gives_no_row(tmp_path: Path) -> None:
    """A firm judged `none` (too few SQX trades) is not recorded."""
    import json
    import shutil

    run = tmp_path / PASSED
    shutil.copytree(pool.RUNS / PASSED, run)
    res = json.loads((run / "result.json").read_text(encoding="utf-8"))
    res["summary"]["firms"]["ftmo"]["state"] = "none"
    (run / "result.json").write_text(json.dumps(res), encoding="utf-8")
    assert [r["firm"] for r in pool.rows_of(run)] == ["hantec"]


def test_a_crashed_check_gives_no_row() -> None:
    """A check that never judged is not a verdict."""
    assert pool.rows_of(pool.RUNS / CRASHED) == []


def test_a_refused_firm_gives_no_row() -> None:
    """Hantec was refused on gold (no confirmed commission): only FTMO was judged."""
    rows = pool.rows_of(pool.RUNS / "20260929-194955_Strategy_3_48_75")
    assert [(r["firm"], r["verdict"]) for r in rows] == [("ftmo", "fail")]


def test_rebuilt_register_reads_only_the_validated(register: Path) -> None:
    """Every finished check on disk recorded: FTMO holds the two that validate, Hantec none."""
    rows = pool.rebuild()
    pool.record(rows)
    assert pool.pending(rows) == [] and len(pool.history("ftmo")) >= 13
    ftmo = pool.read("ftmo")
    assert {"Strategy 16.9.76", "Strategy 10.9.72"} <= set(ftmo["strategy"])
    assert not {"Strategy 21.9.59", "Strategy 3.48.75", "Strategy 10.1.79"} & set(
        ftmo["strategy"]
    )
    assert ftmo["identity"].is_unique and set(ftmo["verdict"]) == {"pass"}
    assert pool.read("hantec").empty
    assert pool.read("the5ers").empty  # a firm nobody verified on: empty, not an error


def test_first_verdict_counts_and_nothing_is_rewritten(register: Path) -> None:
    """Owner 2026-10-11: reruns stay in the history but the first verdict is what `read` gives."""
    good = pool.rows_of(pool.RUNS / PASSED)[:1]
    bad = [
        {
            **good[0],
            "verdict": "fail",
            "run": "later",
            "verified_on": "2026-10-02T09:00:00",
        }
    ]
    pool.record(good)
    pool.record(bad)
    assert (
        list(pool.read("ftmo")["identity"]) == [ID_PASSED]
        and len(pool.history("ftmo")) == 2
    )
    # a failed first verdict is not rescued by a later pass; another window counts on its own
    other = {**good[0], "run": "r3", "window_from": "1999-01-01"}
    pool.record(
        [
            {
                **good[0],
                "identity": "x" * 64,
                "verdict": "fail",
                "verified_on": "2026-10-01",
            },
            {**good[0], "identity": "x" * 64, "run": "r2", "verified_on": "2026-10-05"},
            other,
        ]
    )
    assert (
        "x" * 64 not in set(pool.read("ftmo")["identity"])
        and len(pool.read("ftmo")) == 2
    )
    assert pool.pending(good + bad) == []
    assert (
        register.joinpath("ftmo.csv").read_text(encoding="utf-8").count("\n") == 6
    )  # header + 5


def test_another_version_of_the_strategy_does_not_inherit(register: Path) -> None:
    """Encargo 34 §4: another stop is another identity, and it is not in the pool."""
    pool.record(pool.rows_of(pool.RUNS / PASSED))
    assert "0" * 64 not in set(pool.read("ftmo")["identity"])
    assert ID_PASSED in set(pool.read("ftmo")["identity"])


def test_the_autopilot_finalist_fills_mother_and_project() -> None:
    """What only the autopilot knows travels into the row."""
    row = pool.rows_of(
        pool.RUNS / FAILED, "Trade_USDJPY_x_H1", {"mother": "Strategy 21.9"}
    )[0]
    assert (row["project"], row["mother"]) == ("Trade_USDJPY_x_H1", "Strategy 21.9")

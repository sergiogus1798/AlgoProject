"""Encargo 66, tanda E: export_retest packs a live session's `.abk` in place of one orderstocsv pass, fakes only."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import sqxfile
from sqx.export import export_retest


STATS = {
    "Strategy 2.1.1": {10: {"NumberOfTrades": 2, "NetProfit": 715.585}},
    "Strategy 10.4.7": {10: {"NumberOfTrades": 1, "NetProfit": 190.5}},
    "Strategy 3.3.3": {10: {"NumberOfTrades": 0, "NetProfit": 0.0}},
}


def _retest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, banks: dict
) -> tuple[dict, list]:
    """Run export_retest on fake databanks A and B; `banks` maps a databank to the `.abk` to leave for it."""
    from tests.test_perf66_algobank import strategies, write
    from tests.test_perf66_algobank_pack import _csv

    bank, ran, written = strategies(), [], {}
    for db, held in banks.items():
        if held:
            (tmp_path / "abk").mkdir(parents=True, exist_ok=True)
            write(tmp_path / "abk" / f"{db}.abk", bank, data=1)

    def stage(
        project: str, db: str, dest: Path, limit: int, install: Path, prefix: str
    ) -> dict:
        """The databank's three strategies, as files named after them."""
        dest.mkdir(parents=True, exist_ok=True)
        for s in bank:
            (dest / f"{prefix}{s['name']}.sqx").write_text(s["xml"])
        return {s["name"]: "H1" for s in bank}

    def trades(sqx: Path, raw: Path, data: str) -> None:
        """orderstocsv: one CSV per staged file."""
        raw.mkdir()
        ran.append(sorted(f.name for f in sqx.iterdir()))
        for f in sqx.iterdir():
            _csv(
                raw / f"{f.stem}.csv",
                next(s for s in bank if f.stem.endswith(s["name"])),
                {"XAUUSD": 2, "XAGUSD": 3},
            )

    for name, val in {
        "export_dir": lambda p, db, day, batch="": tmp_path / "out" / db,
        "worker_dir": lambda role: tmp_path,
        "stage": stage,
        "sign": lambda *a: 0,
    }.items():
        monkeypatch.setattr(export_retest, name, val)
    monkeypatch.setattr(export_retest.exportdrv, "trades", trades)
    monkeypatch.setattr(
        export_retest.identities,
        "many",
        lambda files, n: {f: sqxfile._hashed(f.read_text()) for f in files},
    )
    monkeypatch.setattr(
        export_retest.membank, "bank_dir", lambda p, r: tmp_path / "abk"
    )
    monkeypatch.setattr(
        export_retest.manifest,
        "write",
        lambda out, meta, cmd, res, since: written.__setitem__(out.name, res),
    )
    monkeypatch.setattr(
        export_retest.fanout, "run", lambda fn, d, w: [(k, fn(k)) for k in d]
    )

    def every(f: Path) -> dict:
        """The .sqx's results: the main one, and for 10.4.7 its silver one (2 trades, -27.25)."""
        name = f.stem.split("__", 1)[1]
        return {
            "Main: XAUUSD_M1/H1": STATS[name],
            "Portfolio": {},
            **(
                {
                    "AdditionalMarket: XAGUSD_M1/H1": {
                        10: {"NumberOfTrades": 2, "NetProfit": -27.25}
                    }
                }
                if name == "Strategy 10.4.7"
                else {}
            ),
        }

    monkeypatch.setattr(export_retest.sqxstats, "every", every)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--project",
            "Test_X",
            "--role",
            "custodian",
            *[a for db in banks for a in ("--databank", db)],
        ],
    )
    export_retest.main()
    return written, ran


def test_export_retest_from_memory_equals_orderstocsv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P4: a databank taken from the `.abk` packs the same Parquet and manifest block as the orderstocsv route."""
    mem, none = tmp_path / "mem", tmp_path / "csv"
    got_mem, ran_mem = _retest(monkeypatch, mem, {"A": True, "B": True})
    got_csv, ran_csv = _retest(monkeypatch, none, {"A": False, "B": False})
    assert (
        ran_mem == [] and len(ran_csv) == 1 and len(ran_csv[0]) == 6
    )  # no sqcli at all vs today's one pass
    assert got_mem == got_csv
    for db in "AB":
        pd.testing.assert_frame_equal(
            pd.read_parquet(mem / "out" / db / "trades.parquet"),
            pd.read_parquet(none / "out" / db / "trades.parquet"),
            check_exact=True,
            check_categorical=True,
        )


def test_export_retest_mixed_sends_only_the_untaken_to_orderstocsv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """P4: with A taken and B not, orderstocsv sees B's strategies only and both directories are written."""
    got, ran = _retest(monkeypatch, tmp_path, {"A": True, "B": False})
    assert (
        len(ran) == 1 and all(n.startswith("1__") for n in ran[0]) and len(ran[0]) == 3
    )
    assert set(got) == {"A", "B"} and all(
        (tmp_path / "out" / db / "trades.parquet").exists() for db in "AB"
    )


def test_export_retest_refuses_a_dump_that_is_not_the_sqx_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Same strategies but another net profit in the .sqx: the `.abk` is not taken, one line names the strategy."""
    STATS["Strategy 2.1.1"][10]["NetProfit"] = 700.0
    try:
        _, ran = _retest(monkeypatch, tmp_path, {"A": True, "B": True})
    finally:
        STATS["Strategy 2.1.1"][10]["NetProfit"] = 715.585
    assert len(ran) == 1 and len(ran[0]) == 6
    assert capsys.readouterr().out.count(".abk no vale: Strategy 2.1.1") == 2


def _fallbacks(path: Path) -> list[str]:
    """The details of the `fallback` rows of a phase log."""
    import csv

    return (
        [r[3] for r in csv.reader(open(path, encoding="utf-8")) if r[2] == "fallback"]
        if path.exists()
        else []
    )


def test_export_retest_records_a_refused_abk_as_a_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A `.abk` that exists and is refused leaves a `fallback` row `project/databank: reason`; the export still completes."""
    log = tmp_path / "fases.csv"
    monkeypatch.setenv("ALGO_PHASES", str(log))
    STATS["Strategy 2.1.1"][10]["NetProfit"] = 700.0
    try:
        got, ran = _retest(monkeypatch, tmp_path, {"A": True, "B": True})
    finally:
        STATS["Strategy 2.1.1"][10]["NetProfit"] = 715.585
    assert set(got) == {"A", "B"} and len(ran) == 1
    rows = _fallbacks(log)
    assert len(rows) == 2 and all(
        r.startswith(("Test_X/A: ", "Test_X/B: ")) and "Strategy 2.1.1" in r
        for r in rows
    )


def test_export_retest_without_an_abk_records_no_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No `.abk` at all is the restart route, not a fallback."""
    log = tmp_path / "fases.csv"
    monkeypatch.setenv("ALGO_PHASES", str(log))
    _retest(monkeypatch, tmp_path, {"A": False, "B": False})
    assert _fallbacks(log) == []

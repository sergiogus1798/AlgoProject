"""Encargo 66, tanda E: `liverun.export` dumps the stale banks and cleans up; `export_trades` takes an `.abk`."""

from pathlib import Path
from types import SimpleNamespace

import pytest


class _Run:
    """A fake `Popen` of afterrun: prints `lines`, ends with `rc`."""

    def __init__(self, cmd: list, lines: list[str], rc: int, seen: list) -> None:
        """Record the command."""
        self.stdout, self.returncode, self._rc = lines, rc, rc
        seen.append(cmd)

    def wait(self) -> int:
        """The exit code."""
        return self._rc


@pytest.fixture
def live(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict:
    """`liverun.export` over a project: Results (stale harvest, retest OOS), Fresh, Cross (a stale cross-market trades bank)."""
    from ui.daemon.launch import liverun

    env = {"dumped": [], "procs": [], "lines": [], "rc": 0, "dir": tmp_path / "shm"}
    todo = {
        "Results": {"harvest": ("c", [])},
        "Fresh": {},
        "OOS": {},
        "Cross": {"trades": ("c", [])},
    }
    monkeypatch.setattr(liverun.progress, "installs", lambda: {"custodian": tmp_path})
    monkeypatch.setattr(
        liverun.afterrun,
        "scope",
        lambda top, ran, names: {("P", b): True for b in ("Results", "Fresh", "Cross")},
    )
    monkeypatch.setattr(
        liverun.state,
        "status",
        lambda p, b: {"databank": b, "partner": "OOS" if b == "Results" else None},
    )
    monkeypatch.setattr(
        liverun.state, "commands", lambda p, now, exports=True: todo[now["databank"]]
    )
    monkeypatch.setattr(liverun.find, "files", lambda top, p, b: b)
    monkeypatch.setattr(liverun.find, "cross_market", lambda b: b == "Cross")
    monkeypatch.setattr(liverun, "bank_dir", lambda p, r: env["dir"])
    monkeypatch.setattr(
        liverun.membank,
        "run",
        lambda r, p, banks: env["dumped"].append(banks) or {b: 1 for b in banks},
    )
    monkeypatch.setattr(
        liverun.subprocess,
        "Popen",
        lambda cmd, **k: _Run(cmd, env["lines"], env["rc"], env["procs"]),
    )
    env["dir"].mkdir()
    return env


def test_liverun_export_dumps_only_the_stale_banks_each_in_its_mode(live: dict) -> None:
    """A fresh bank is not dumped; the harvest's bank and its retest go "main", a cross-market trades bank "all"; the folder is gone."""
    from ui.daemon.launch import liverun

    liverun.export("custodian", "P", {"Results"})
    assert (
        live["dumped"] == [{"Results": "main", "OOS": "main", "Cross": "all"}]
        and not live["dir"].exists()
    )
    cmd = live["procs"][0]
    assert (
        cmd[-2:] == ["--databank", "Results"] and "--live" in cmd and "--project" in cmd
    )


@pytest.mark.parametrize("fail", ["run", "afterrun"])
def test_liverun_export_removes_the_dump_folder_on_any_failure(
    live: dict, monkeypatch: pytest.MonkeyPatch, fail: str
) -> None:
    """The /dev/shm folder goes when the dump raised and when afterrun exited non-zero."""
    from ui.daemon.launch import liverun

    if fail == "run":
        monkeypatch.setattr(
            liverun.membank,
            "run",
            lambda r, p, banks: (_ for _ in ()).throw(SystemExit("boom")),
        )
    live["rc"] = 1 if fail == "afterrun" else 0
    with pytest.raises(SystemExit):
        liverun.export("custodian", "P")
    assert not live["dir"].exists()


def test_liverun_export_failure_names_why_a_bank_was_not_taken(live: dict) -> None:
    """No fallback in a live session: the reason `take` printed reaches the error the step reports."""
    from ui.daemon.launch import liverun

    live["lines"], live["rc"] = (
        [
            "P/Results: Results.abk no vale: modo all, se pide main\n",
            "exportando trades\n",
        ],
        1,
    )
    with pytest.raises(SystemExit, match="modo all, se pide main"):
        liverun.export("custodian", "P")


def test_export_trades_takes_a_bound_abk_and_its_pack_equals_the_csv_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`held` returns the bank when the .sqx stats bind; otherwise None and the reason; `bankfile.pack` equals `tradepack.pack` of the CSVs."""
    import argparse
    import pandas as pd
    from core import bankfile, tradepack
    from sqx.export import export_trades
    from tests.test_perf66_algobank import strategies, write
    from tests.test_perf66_algobank_pack import _csv

    bank = strategies()[:2]
    files = [tmp_path / f"{b['name']}.sqx" for b in bank]
    [f.write_bytes(b"x") for f in files]
    write(tmp_path / "R.abk", bank)
    stats = {
        "Strategy 2.1.1": {10: {"NumberOfTrades": 2, "NetProfit": 715.585}},
        "Strategy 10.4.7": {10: {"NumberOfTrades": 1, "NetProfit": 190.5}},
    }
    taken = lambda *a: bankfile.load(tmp_path / "R.abk")  # noqa: E731
    monkeypatch.setattr(export_trades, "bank_dir", lambda p, r: tmp_path)
    monkeypatch.setattr(
        export_trades.identities, "many", lambda fs, n: {f: "id" for f in fs}
    )
    monkeypatch.setattr(export_trades.membank, "take", taken)
    monkeypatch.setattr(
        export_trades,
        "fanout",
        SimpleNamespace(CORES=1, run=lambda fn, d, w: [(f, stats[f.stem]) for f in d]),
    )
    monkeypatch.setattr(export_trades.sqxview, "measured", lambda st: 10)
    a = argparse.Namespace(project="P", role="x", databank="R")
    assert export_trades.held(a, tmp_path) is not None
    stats["Strategy 2.1.1"][10]["NetProfit"] += 5
    assert export_trades.held(a, tmp_path) is None
    csvs = []
    for st in bank:
        csvs.append(tmp_path / f"{st['name']}.csv")
        _csv(csvs[-1], st, {"XAUUSD": 2, "XAGUSD": 3})
    want = tradepack.pack(sorted(csvs), tmp_path / "w.parquet", per_market=False)
    assert bankfile.pack(taken(), tmp_path / "g.parquet", per_market=False) == want
    pd.testing.assert_frame_equal(
        pd.read_parquet(tmp_path / "g.parquet"),
        pd.read_parquet(tmp_path / "w.parquet"),
        check_exact=True,
    )

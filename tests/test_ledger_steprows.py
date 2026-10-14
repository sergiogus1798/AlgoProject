"""A recorded build leaves a step-6 row, and the report prints the study's N and the global N."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import report, steprows, study as studymod, trials  # noqa: E402

LINE = (
    "Strategies generated: 4332347, Time per strategy: 10 ms., Time per accepted strategy: "
    "9 s., Accepted: 4600, Rejected: 4327747, Strategies per hour: 346188\n"
)
ROW = {
    "name": "Test_X",
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "template": "/lib/foo/template.sqx",
}


@pytest.fixture
def ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A ledger and a registry that live in a temporary folder."""
    monkeypatch.setattr(
        studymod, "ledger_file", lambda s: tmp_path / "ledger" / f"{s}.jsonl"
    )
    monkeypatch.setattr(steprows.registry, "rows", lambda: [ROW])
    return tmp_path


def test_build_row_and_both_ns(
    ledger: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Build and WFM rows land once, N counts generated, and the report prints both Ns."""
    logs = ledger / "log"
    logs.mkdir()
    (logs / "global_log_20261004_100000.log").write_text("noise\n" + LINE)
    assert steprows.built(logs) == (4332347, 4600)
    assert (
        steprows.built(logs, since=9e12) is None
    )  # a log older than the run is not its

    steprows.log_build("Test_X", logs)
    steprows.log_wfm("Test_X", Path("/exp/wfm"), 7, "test")
    steprows.log_wfm("Test_X", Path("/exp/wfm"), 7, "test")  # same export: written once
    frame = studymod.read("XAUUSD_H1_foo")
    build = frame[frame["step"] == 6].iloc[0]
    assert (build["n_in"], build["n_out"], build["segment"]) == (4332347, 4600, "build")
    assert len(frame[frame["step"] == 19]) == 3

    counted = trials.accumulated(frame)
    assert counted["n"] == 4332347  # generated counts in N, not in sigma
    other = frame.assign(study="other")
    assert trials.overall([frame, other])["n"] == 2 * 4332347
    assert trials.overall([])["n"] == 0

    monkeypatch.setattr(sys, "argv", ["report", "--study", "XAUUSD_H1_foo"])
    report.main()
    printed = capsys.readouterr().out
    assert "N global entre 1 estudios: 4332347" in printed
    assert "N = 43323" in printed


def test_log_cut_once_and_never_inside_the_workflow(
    ledger: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A standalone cut leaves one row; under ALGO_AUTONOMOUS the judge's row is the only one."""
    monkeypatch.delenv("ALGO_AUTONOMOUS", raising=False)
    steprows.log_cut("Test_X", 8, (100, 12), "decay: no DESCARTAR", "test")
    row = studymod.read("XAUUSD_H1_foo").iloc[0]
    assert (row["step"], row["n_in"], row["n_out"], row["segment"]) == (
        8,
        100,
        12,
        "oos1",
    )
    monkeypatch.setenv("ALGO_AUTONOMOUS", "1")
    steprows.log_cut("Test_X", 8, (100, 12), "decay: no DESCARTAR", "test")
    assert len(studymod.read("XAUUSD_H1_foo")) == 1

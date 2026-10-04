"""The autopilot's timing table: a nested phase's seconds leave its parent, and SQX stays apart."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from core import phases  # noqa: E402
from pipeline.autopilot import timing  # noqa: E402


def test_children_leave_their_parent(tmp_path: Path) -> None:
    """One action of 100 s: start 10, sqx 50, stop 30 of which the export is 20, 10 unnamed."""
    path = tmp_path / "P" / "run" / "fases.csv"
    path.parent.mkdir(parents=True)
    rows = [(1010.0, 10, "start", ""), (1060.0, 50, "sqx", "OOS"), (1085.0, 20, "export", ""),
            (1090.0, 30, "stop", ""), (1100.0, 100, "accion", "7 sqx")]   # written as each ends
    path.write_text("".join(f"{end - s:.3f},{s:.3f},{name},{detail},1\n"
                            for end, s, name, detail in rows), encoding="utf-8")
    own = timing.own(timing.pd.read_csv(path, names=phases.COLUMNS)).set_index("phase")["own"]
    assert own.round(3).to_dict() == {"accion": 10, "start": 10, "sqx": 50, "stop": 10,
                                      "export": 20}
    text = timing.table(path)
    assert "| 7 sqx | 100 | 50 | 10 | 10 | 20 | 0 | 0 | 10 |" in text
    assert "todo lo demás 0.8 min (50 % del total)" in text


def test_phase_writes_only_when_asked(tmp_path: Path,
                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """Without `ALGO_PHASES` nothing is written; with it, one row per block."""
    monkeypatch.delenv(phases.ENV, raising=False)
    with phases.phase("sqx"):
        pass
    monkeypatch.setenv(phases.ENV, str(tmp_path / "fases.csv"))
    with phases.phase("stop", "custodian"):
        pass
    assert (tmp_path / "fases.csv").read_text(encoding="utf-8").split(",")[2:4] == ["stop",
                                                                                     "custodian"]

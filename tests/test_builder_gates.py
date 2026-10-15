"""Builder gates: a live project name is refused, a refusal leaves the install's template alone,
a clock block fixed in a template is refused, store-resume passes the right builder arguments."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot.resume import builder_argv
from sqx.projects import buildrules, registry


def test_exists_live_folder_and_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A folder or a live row blocks a name; a retired row does not."""
    monkeypatch.setattr(buildrules, "worker_dir", lambda role: tmp_path)
    rows = [
        {"name": "Test_a", "install": "SQX_w2", "retired": ""},
        {"name": "Test_b", "install": "SQX_w2", "retired": "2026-10-01"},
    ]
    monkeypatch.setattr(registry, "rows", lambda: rows)
    (tmp_path / "user/projects/Test_c").mkdir(parents=True)
    assert "SQX_w2" in buildrules.exists("Test_a", "custodian")
    assert buildrules.exists("Test_b", "custodian") is None
    assert "Test_c" in buildrules.exists("Test_c", "custodian")
    assert buildrules.exists("Test_d", "custodian") is None


def test_clock_fixed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only clock keys come back; the list is `buildcensus.kind`'s, not a copy."""
    monkeypatch.setattr(buildrules, "rules", lambda p: None)
    monkeypatch.setattr(
        buildrules, "blocks", lambda n: {"Vortex", "BarHourIs", "CurrentHour"}
    )
    assert buildrules.clock_fixed(Path("x.sqx")) == ["BarHourIs", "CurrentHour"]


def test_resume_arguments() -> None:
    """`simple:long` becomes --simple long; a path stays --template."""
    row = {
        "template": "simple:short",
        "purpose": "p",
        "symbol": "EURUSD",
        "timeframe": "H1",
    }
    argv = builder_argv("Test_x", row, 3, "custodian")
    assert argv[argv.index("--simple") + 1] == "short" and "--template" not in argv
    row["template"] = "/lib/t.sqx"
    argv = builder_argv("Test_x", row, 3, "custodian")
    assert argv[argv.index("--template") + 1] == "/lib/t.sqx" and "--simple" not in argv


def test_early_gates() -> None:
    """A workflow on M5 is refused, on H1 it is not."""
    assert buildrules.early_gates("Test_zz", "custodian", None, True, "M5")
    assert not buildrules.early_gates("Test_zz", "custodian", None, True, "H1")
    assert not buildrules.early_gates("Test_zz", "custodian", None, False, "M5")


def test_off_segment_refuses_a_window_beyond_its_segment() -> None:
    """A main-feed range inside its segment passes; one reaching past it is named."""
    from core.assetdata import load, window
    from sqx.projects.resources import off_segment

    data = load("XAUUSD")
    lo, hi = window(data, "oos1")

    def cfx(a: int, b: int) -> dict[str, bytes]:
        """One staged task with a main-feed range."""
        return {
            "T.xml": f'<Symbol name="{data["sqx_symbol"]}" dateFrom="{a}" dateTo="{b}"></Symbol>'.encode()
        }

    r = {
        "project_asset": "XAUUSD",
        "feed": data["sqx_symbol"],
        "segments": {"T.xml": "oos1"},
    }
    assert off_segment(r, cfx(lo, hi)) == []
    assert "fuera de oos1" in off_segment(r, cfx(lo - 1, hi))[0]

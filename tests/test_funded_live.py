"""Known-answer tests of the live protocol: SPRT boundaries and crossings, and stage A's rows."""

import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import assetwrite
from core.assetwrite import failures
from core.assetyaml import safe_load
from portfolio.funded.live import real, sprt, stage_a

SPRT = {"mu0": 0.0, "mu1": 0.10, "sigma": 0.706, "ln_a": 2.89, "ln_b": -2.25}
CFG = {
    "trades": 30,
    "tolerance_bars": 1,
    "matched_min": 0.95,
    "trade_gap_max_r": 0.05,
    "daily_corr_min": 0.95,
    "dd_rel_gap_max": 0.10,
    "max_offset_h": 3,
}
PNL = [
    100.0,
    -50.0,
    80.0,
    -120.0,
    60.0,
    -30.0,
    150.0,
    -90.0,
    40.0,
    -70.0,
] * 3  # one trade a day, 30 days


def test_boundaries() -> None:
    """The limits come out of the parameters at +14.4 and -11.2 R, drift 0.05."""
    drift, lower, upper = sprt.boundaries(SPRT)
    assert (round(drift, 2), round(lower, 1), round(upper, 1)) == (0.05, -11.2, 14.4)


def test_crossings() -> None:
    """+1 R each: 0.95 n >= 14.405 first at n=16; -1 R each: -1.05 n <= -11.215 first at n=11."""
    up = sprt.run([1.0] * 40, SPRT)
    assert (up["verdict"], up["n"]) == ("raise", 16)
    down = sprt.run([-1.0] * 40, SPRT)
    assert (down["verdict"], down["n"]) == ("retire", 11)
    inside = sprt.run([1.0, -1.0] * 20, SPRT)
    assert (inside["verdict"], inside["n"]) == ("continue", 40)


def trades(pnl: list[float], extra: int = 0) -> pd.DataFrame:
    """One 'buy' a day at 10:00 closing at 11:00, plus `extra` zero-P&L trades at 15:00."""
    days = pd.date_range("2026-01-05", periods=len(pnl), freq="D")
    rows = [
        ("buy", d + pd.Timedelta(hours=10), d + pd.Timedelta(hours=11), p)
        for d, p in zip(days, pnl)
    ]
    rows += [
        ("buy", d + pd.Timedelta(hours=15), d + pd.Timedelta(hours=16), 0.0)
        for d in days[:extra]
    ]
    return pd.DataFrame(
        rows, columns=["Type", "Open time", "Close time", "Profit/Loss"]
    )


def judged(real_pnl: list[float], extra: int = 0) -> dict:
    """Stage A on a SQX backtest of PNL against `real_pnl`."""
    return stage_a.run(trades(PNL, extra), trades(real_pnl), "H1", 10000.0, CFG)


def test_stage_a_pass() -> None:
    """Identical trades pass every row."""
    res = judged(PNL)
    assert not res["out"] and not res["warning"] and res["n"] == 30


def test_stage_a_each_row_fails() -> None:
    """A P&L three times the SQX one fails the gap row; a mirrored one the correlation row; a reordered one the drawdown."""
    assert "2" in judged([3 * p for p in PNL])["failed"]
    assert "3a" in judged([-p for p in PNL])["failed"]
    assert "5" in judged(sorted(PNL))["failed"]


def test_stage_a_matched_only_warns() -> None:
    """Five unmatched SQX trades put matched below 0.95 and nothing else: a warning, the strategy stays."""
    res = judged(PNL, extra=5)
    assert res["warning"] and not res["out"]


def test_stage_a_applies_the_clock() -> None:
    """A SQX side one hour late is moved back by the judge's own clock search and then passes."""
    late = trades(PNL)
    for c in ("Open time", "Close time"):
        late[c] = late[c] + pd.Timedelta(hours=1)
    res = stage_a.run(late, trades(PNL), "H1", 10000.0, CFG)
    assert res["hours"] == -1 and not res["out"]


def test_stage_a_short_sample_has_no_verdict() -> None:
    """Fewer real trades than the protocol reads never take a strategy out."""
    res = stage_a.run(trades(PNL), trades([-p for p in PNL[:10]]), "H1", 10000.0, CFG)
    assert res["failed"] and not res["ready"] and not res["out"]


def test_r_is_the_judges_mean_loss() -> None:
    """SQX losses -50 -120 -30 -90 -70 (x3) average 72: a real +144 is +2 R."""
    sqx = trades(PNL)
    got = real.r_values(trades([144.0, -72.0]), sqx)
    assert got == [2.0, -1.0]


def test_live_failure_writer() -> None:
    """On a temp copy of a card: one entry appended, a second after it, comments and keys kept."""
    tmp = Path(tempfile.mkdtemp())
    card = next(
        p for p in failures.SYMBOLS.glob("*.yaml") if not p.name.startswith("_")
    )
    shutil.copy(card, tmp / "TEST.yaml")
    old, failures.SYMBOLS = failures.SYMBOLS, tmp
    noop, assetwrite.reindex = assetwrite.reindex, lambda: 0
    try:
        before = (tmp / "TEST.yaml").read_text(encoding="utf-8")
        failures.add_live_failure("TEST", date(2026, 10, 12), "S1", "2", 0.1234567)
        failures.add_live_failure("TEST", date(2026, 10, 13), "S2", "3a", None)
        text = (tmp / "TEST.yaml").read_text(encoding="utf-8")
    finally:
        failures.SYMBOLS, assetwrite.reindex = old, noop
        shutil.rmtree(tmp, ignore_errors=True)
    doc = safe_load(text)
    assert doc["live_failures"] == [
        {"date": "2026-10-12", "strategy": "S1", "row": "2", "value": 0.1235},
        {"date": "2026-10-13", "strategy": "S2", "row": "3a", "value": None},
    ]
    assert text.startswith(before.rstrip("\n")[:200]) and "live_failures" not in before


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")

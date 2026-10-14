#!/usr/bin/env python3
"""The funded-firms spread method on toy ticks and a toy card."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.data.spread import funded


def day(folder: Path, name: str, spread: float) -> None:
    """One sample day: a quote every 10 s for an hour, bid 100, ask 100 + spread."""
    t = pd.date_range("2026-01-05 10:00", periods=360, freq="10s")
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"bid": 100.0, "ask": 100.0 + spread, "time_msc": t}).to_parquet(
        folder / f"{name}.parquet"
    )


def test_widest_firm_takes_the_larger_of_last12_and_last3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The widest firm wins with the larger of its last-12 and last-3 sample means."""
    monkeypatch.setattr(funded, "HIST", tmp_path)
    for m in range(1, 13):  # FTMO: 0.01 % for 9 months, 0.05 % the last three
        day(tmp_path / "ftmo" / "TOY", f"2026-{m:02d}-05", 0.01 if m <= 9 else 0.05)
        day(tmp_path / "hantec" / "TOY", f"2026-{m:02d}-05", 0.02)  # flat 0.02 %
    firm, _, per = funded.widest("TOY")
    assert firm == "ftmo", per
    assert abs(per["ftmo"] - 0.0005) < 1e-9, per  # last 3 beats the 12-mean 0.02 %
    assert abs(per["hantec"] - 0.0002) < 1e-9, per
    with pytest.raises(ValueError):
        funded.widest("NOPE")


def test_plan_converts_pct_to_points_and_whys_carry_the_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0.02 % of a price of 100 on a 0.01 tick is 2 points; slippage 35 % of it; the marker is there."""
    monkeypatch.setattr(funded, "HIST", tmp_path)
    for m in range(1, 13):
        day(tmp_path / "ftmo" / "TOY", f"2026-{m:02d}-05", 0.02)
    card = {"symbol": "TOY", "instrument": {"tick_size": 0.01}}
    monkeypatch.setattr(funded, "load", lambda s: card)
    monkeypatch.setattr(
        funded, "segment_prices", lambda d: dict.fromkeys(funded.SEGMENTS, 100.0)
    )
    p = funded.plan("TOY", 1.0, 0.35)
    assert p["spreads"]["spread_is"] == 2.0 and p["slippage"]["slippage_is"] == 0.7, p
    assert all(
        "sin factor" in w
        for f, w in funded.whys(p, "2026-10-14", 0.35).items()
        if f.startswith("spread")
    )
    with pytest.raises(ValueError):
        funded.plan("TOY", 1.25, 0.35)

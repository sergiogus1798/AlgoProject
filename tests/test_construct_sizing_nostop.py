#!/usr/bin/env python3
"""OPEN #113 (1): a member with no stop is sized by its worst build day of floating loss."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import portfolio.common.construct.inputs.risk as risk


def _archive(tmp: Path) -> tuple[str, str]:
    """A fake archived stopless strategy: two build days, one OOS day that must not count."""
    folder = tmp / "NOSTOP" / "v1"
    (folder / "harvest").mkdir(parents=True)
    (folder / "strategy.sqx").write_bytes(b"")
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    (folder / "view.json").write_text(
        '{"tearsheet": "sin tearsheet"}', encoding="utf-8"
    )
    pd.DataFrame(
        {
            "Close time": pd.to_datetime(
                [
                    "2020-01-02 10:00",
                    "2020-01-02 18:00",
                    "2020-01-03 12:00",
                    "2024-05-01 12:00",
                ]
            ),
            "MAE ($)": [-300.0, -500.0, -650.0, -5000.0],
            "Size": [0.4, 0.8, 0.3, 2.0],
            "sample": ["IS", "IS", "IS", "OOS"],
        }
    ).to_parquet(folder / "harvest" / "trades.parquet")
    return "NOSTOP", "v1"


def test_sizing_without_stop() -> None:
    """Same-day MAEs add up, OOS is ignored, the factor scales the worst day to one unit of r*S."""
    real = risk.archive_read.archive_dir
    with tempfile.TemporaryDirectory() as tmp:
        risk.archive_read.archive_dir = lambda: Path(tmp)
        try:
            got = risk.sizing(*_archive(Path(tmp)))
        finally:
            risk.archive_read.archive_dir = real
    assert got["worst_day"] == 800.0, got
    assert got["factor"] == 1 / 800.0, got
    assert got["min_size"] == 0.3, got


def test_refuses_no_loss() -> None:
    """A build that never went against the strategy cannot be sized."""
    trades = pd.DataFrame(
        {
            "Close time": pd.to_datetime(["2020-01-02"]),
            "MAE ($)": [0.0],
            "sample": ["IS"],
        }
    )
    try:
        risk.worst_day(trades)
    except ValueError:
        return
    raise AssertionError("a lossless build must be refused")


if __name__ == "__main__":
    test_sizing_without_stop()
    test_refuses_no_loss()
    print("test_construct_sizing_nostop: ok")

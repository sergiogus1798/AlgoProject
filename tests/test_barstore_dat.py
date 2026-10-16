"""The bar library is filled from SQX's .dat at full precision, and its fingerprint tells sources apart."""

from pathlib import Path

import pandas as pd
import pytest

from core import barstore, tickfile


def _frame() -> pd.DataFrame:
    """Three M1 bars with three-decimal prices."""
    idx = pd.date_range("2026-01-05 00:00", periods=3, freq="1min", name="t")
    return pd.DataFrame(
        {
            "Open": [2000.123, 2000.456, 2000.789],
            "High": [2001.0, 2001.0, 2001.0],
            "Low": [1999.0, 1999.0, 1999.0],
            "Close": [2000.456, 2000.789, 2000.111],
            "Volume": [1.0, 2.0, 3.0],
        },
        index=idx,
    )


def test_store_keeps_three_decimals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """store() writes the .dat's prices unrounded and leaves no temp file."""
    frame = _frame()
    dat = tmp_path / "F_M1.dat"
    dat.write_bytes(b"x")
    monkeypatch.setattr(tickfile, "bars", lambda feed: frame)
    monkeypatch.setattr(barstore, "bar_file", lambda feed: dat)
    monkeypatch.setattr(
        barstore, "bar_source", lambda feed: tmp_path / "F" / "M1.parquet"
    )
    entry = barstore.store("F")
    got = pd.read_parquet(tmp_path / "F" / "M1.parquet").set_index("t")
    assert got["Close"].tolist() == frame["Close"].tolist()  # not rounded to 2 decimals
    assert entry["bars"] == 3 and entry["dat"] == 1
    assert not list((tmp_path / "F").glob(".*tmp"))  # atomic write leaves no temp


def test_fingerprint_depends_on_source_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """A new source tag changes every version string, so old resampled caches die."""
    frame = _frame()
    before = barstore.fingerprint(frame)
    monkeypatch.setattr(barstore, "SOURCE", "export")
    assert barstore.fingerprint(frame) != before

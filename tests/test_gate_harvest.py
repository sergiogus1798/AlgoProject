#!/usr/bin/env python3
"""Known answers for the harvest's same-day guard: a different set is set aside, the same is not."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import paths
from studies.screening.gate import harvest


def write(out: Path, ids: list[str]) -> None:
    """Leave a harvest folder holding a `metrics.parquet` of these identities."""
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"x": 1}, index=pd.Index(ids, name="identity")).to_parquet(out / "metrics.parquet")


def test_different_set_is_kept_and_invisible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """10 then 2 strategies the same day: both stay; the newest the readers see is the day folder."""
    monkeypatch.setattr(paths, "DATA", tmp_path)
    out = paths.harvest_dir("P", "Results", "2026-10-04")
    write(out, [str(i) for i in range(10)])
    moved = harvest.set_aside(out, {"1", "2"})
    write(out, ["1", "2"])
    assert moved is not None and len(pd.read_parquet(moved / "metrics.parquet")) == 10
    bank = out.parent
    assert sorted(bank.glob("*/metrics.parquet")) == [out / "metrics.parquet"]
    assert sorted((tmp_path / "harvest" / "P").glob("*/*/metrics.parquet")) == [out / "metrics.parquet"]
    assert paths.harvest_dir("P", "Results", "2026-10-04") == out


def test_same_set_twice_is_one_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The same strategies again overwrite in place: nothing is set aside."""
    monkeypatch.setattr(paths, "DATA", tmp_path)
    out = paths.harvest_dir("P", "Results", "2026-10-04")
    write(out, ["a", "b"])
    assert harvest.set_aside(out, {"b", "a"}) is None
    assert harvest.set_aside(out.parent / "2026-10-05", {"a"}) is None
    assert not (out.parent / "_aparte").exists()

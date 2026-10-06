#!/usr/bin/env python3
"""Gate level 1b, data quality: known answers on hand-made frames."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market.feed import scale
from studies.screening.gate import level1b_data

INDEX = pd.date_range("2024-01-01", periods=48, freq="h")      # H1 bars, 2 days
M0 = int(scale.minutes(INDEX[:1])[0])


def frame(spans: list, close_to: int = 47) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ten trades in two bars each; trades 0-1 sit on bars 0-3, the rest far away."""
    opens = [INDEX[0], INDEX[2]] + [INDEX[10 + 2 * i] for i in range(8)]
    oos = pd.DataFrame({"identity": 1, "open_time": opens,
                        "close_time": [o + pd.Timedelta("1h") for o in opens]})
    oos.loc[9, "close_time"] = INDEX[close_to]
    return oos, pd.DataFrame(spans, columns=["start_min", "end_min"]).assign(cls="vuelta")


def mark(oos: pd.DataFrame, ev: pd.DataFrame) -> np.ndarray:
    """Flag the trades touched by the events, on the shared bar index."""
    return level1b_data.dataquality.mark(oos, INDEX, 60, ev)


def test_mark_includes_both_bars_and_half_open() -> None:
    """Both end bars count and the interval is half open."""
    oos, ev = frame([(M0 + 60 * 3 + 30, M0 + 60 * 3 + 31)])     # inside bar 3
    assert list(np.flatnonzero(mark(oos, ev))) == [1]           # trade 1 ends on bar 3
    oos, ev = frame([(M0 + 60 * 4 - 5, M0 + 60 * 4)])           # ends exactly where bar 4 opens
    assert not mark(oos, ev)[2:].any()


def test_none_affected() -> None:
    """No event touches a trade: nothing affected, ratio 1."""
    oos, ev = frame([(M0 + 60 * 5, M0 + 60 * 5 + 5)])
    oos["excess"] = 1.0
    out = level1b_data.dataquality.facts(oos, mark(oos, ev))
    assert out.loc[1, "n_afectadas"] == 0 and out.loc[1, "ret_datos"] == 1


def test_all_gains_in_affected() -> None:
    """All the gains inside the affected trades leave nothing."""
    oos, ev = frame([(M0, M0 + 5)])                              # trade 0 only
    oos["excess"] = [100.0] + [0.0, 0.1] * 4 + [0.0]
    out = level1b_data.dataquality.facts(oos, mark(oos, ev))
    assert out.loc[1, "n_afectadas"] == 1 and abs(out.loc[1, "ret_datos"]) < 0.1
    oos, ev = frame([(M0, M0 + 5), (M0 + 60 * 2, M0 + 60 * 2 + 5)])
    oos["excess"] = [100.0, 90.0] + [0.0, 0.1] * 4
    out = level1b_data.dataquality.facts(oos, mark(oos, ev))
    assert out.loc[1, "t_a"] > 10 and out.loc[1, "ret_datos"] < 0.01


def test_nonpositive_mean_has_no_ratio() -> None:
    """A non-positive mean has no ratio."""
    oos, ev = frame([(M0, M0 + 5)])
    oos["excess"] = -1.0
    assert np.isnan(level1b_data.dataquality.facts(oos, mark(oos, ev)).loc[1, "ret_datos"])


def level(tmp: Path, oos: pd.DataFrame, ev: pd.DataFrame | None, bars_to: str | None) -> pd.DataFrame:
    """Write the inventory files (if any) and run level 1b on them."""
    if ev is not None:
        ev.to_parquet(tmp / "events.parquet")
        (tmp / "summary.json").write_text(json.dumps({"bars_to": bars_to}))
    data = {"oos": oos, "bars": pd.DataFrame(index=INDEX), "quality": tmp}
    return level1b_data.run(data, pd.Index([1]), {})


def test_absent_inventory_and_short_inventory_give_nan(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A missing or too short inventory gives NaN."""
    oos, ev = frame([(M0, M0 + 5)])
    oos["excess"] = 1.0
    assert level(tmp_path, oos, None, None).isna().all().all()                  # no files
    assert "sin inventario" in caplog.text
    assert level(tmp_path, oos, ev, "2024-01-01 05:00").isna().all().all()      # ends too early
    assert "antes de la ultima" in caplog.text
    assert level(tmp_path, oos, ev, "2024-01-03 00:00").loc[1, "n_afectadas"] == 1


def test_empty_harvest_is_empty() -> None:
    """An empty harvest gives an empty frame."""
    assert level1b_data.run({}, pd.Index([1, 2]), {}).shape == (2, 3)

#!/usr/bin/env python3
"""The distributions the optimisation studies keep reproduce their own p, and a one-strategy run merges."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import draws
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import reading

CFG = config.load(["null.draws=400"])


def test_wfc_rows_reproduce_p_mas_and_p_nivel() -> None:
    """The planted family of test_wfc.py: (1 + n_ge) / (1 + n) of each row is the study's own p."""
    rng = np.random.default_rng(0)
    skill = np.arange(60.0)
    gross = skill / 50 + rng.normal(0, 2.0, (140, 1)) + rng.normal(0, 0.3, (140, 60))
    weeks = {"gross": gross, "net": gross - skill / 20}
    e_oos = {k: w.sum(axis=0) / 2.7 for k, w in weeks.items()}
    e_is = {"gross": skill * 30.0, "net": skill * 30.0 - 600.0}
    kept = []
    found = reading.measure(e_is, e_oos, weeks, 2.7, CFG, name="M", comp="c1", record=kept)
    rows = {d["metric"]: d for d in kept}
    for metric in ("p_mas", "p_nivel"):
        row = rows[metric]
        assert (1 + row["n_ge"]) / (1 + row["n"]) == pytest.approx(found[metric])
        assert row["strategy"] == "M" and len(row["draws"]) == row["n"]


def test_merge_keeps_the_other_strategies() -> None:
    """A second strategy's run replaces only its own rows of the same test."""
    def row(name: str, value: float) -> dict:
        """One recorded distribution for a strategy."""
        return draws.record("t", "m", value, np.arange(10.0), strategy=name, seed=1)
    with tempfile.TemporaryDirectory() as tmp:
        draws.merge(Path(tmp), [row("a", 1.0), row("b", 2.0)])
        draws.merge(Path(tmp), [row("b", 3.0)])
        got = pd.read_parquet(Path(tmp) / draws.FILE)
    assert sorted(got["observed"]) == [1.0, 3.0]

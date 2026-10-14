#!/usr/bin/env python3
"""Known-answer test: a constant IS column has no p, stays in the table as NaN and cannot abort the BH step."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.analysis import correlations
from studies.screening.isOos import many


def test_constant_column_does_not_abort_isoos() -> None:
    """One constant IS column among two real ones: the study still runs, the constant one is no discovery."""
    rng = np.random.default_rng(0)
    n = 200
    x = rng.normal(size=n)
    cols = {
        "a (IS)": x,
        "b (IS)": rng.normal(size=n),
        "const (IS)": np.ones(n),
        "Profit factor (OOS)": x + 0.1 * rng.normal(size=n),
    }
    got = many.run(
        {
            "columns": cols,
            "n": n,
            "is": ["a (IS)", "b (IS)", "const (IS)"],
            "oos": ["Profit factor (OOS)"],
        },
        {},
    )
    assert got is not None
    rows = correlations.predictors(
        cols, "Profit factor (OOS)", ["a (IS)", "const (IS)"]
    )
    assert any(np.isnan(r["p"]) for r in rows), "the constant column keeps its NaN row"


if __name__ == "__main__":
    test_constant_column_does_not_abort_isoos()
    print("ok")

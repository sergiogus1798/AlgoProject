"""Known answers for the kept distributions: the bins hold every draw and the p can be redone."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import draws


def test_the_histogram_holds_every_draw_and_the_p_can_be_redone() -> None:
    """Nothing is clipped: the counts add up to the draws, the edges span them, and the
    empirical p comes back from `n_ge` alone."""
    drawn = np.random.default_rng(0).standard_normal(5000)
    drawn[7] = 40.0                                   # one extreme draw must not be lost
    row = draws.record("t", "z", 1.9, drawn, "abc", rung="timing")
    assert sum(row["counts"]) == 5000 and len(row["edges"]) == draws.BINS + 1
    assert row["edges"][0] == drawn.min() and row["edges"][-1] == 40.0
    assert (row["n_ge"] + 1) / (row["n"] + 1) == ((drawn >= 1.9).sum() + 1) / 5001
    assert row["draws"][-1] == 40.0 and len(row["draws"]) == 5000 and len(row["high"]) == 0
    assert abs((1.9 - row["mean"]) / row["sd"] - (1.9 - drawn.mean()) / drawn.std(ddof=1)) < 1e-12


def test_without_the_draws_the_tails_stay_exact() -> None:
    """A cell of a tensor keeps no draws, but its hundred extremes of each side."""
    drawn = np.arange(1000.0)
    row = draws.record("t", "z", 990.5, drawn, raw=False)
    assert len(row["draws"]) == 0 and list(row["high"]) == list(np.arange(900.0, 1000.0))
    assert sum(h >= 990.5 for h in row["high"]) == row["n_ge"] == 9


def test_a_dead_distribution_does_not_look_healthy() -> None:
    """All NaN is an empty histogram with n_finite 0; a constant one is a single full bin."""
    dead = draws.record("t", "z", 1.0, np.full(10, np.nan))
    assert dead["n_finite"] == 0 and dead["counts"] == [] and np.isnan(dead["mean"])
    flat = draws.record("t", "z", 1.0, np.ones(10))
    assert sum(flat["counts"]) == 10 and max(flat["counts"]) == 10


def test_a_part_rewritten_leaves_the_other_tests_rows(tmp_path: Path) -> None:
    """The gate saves level by level: a level run again replaces its own rows only."""
    draws.save(tmp_path, [draws.record("a", "z", 0.0, np.arange(5.0))])
    draws.save(tmp_path, [draws.record("b", "z", 0.0, np.arange(5.0))])
    draws.save(tmp_path, [draws.record("a", "z", 9.0, np.arange(5.0))])
    got = pd.read_parquet(tmp_path / draws.FILE)
    assert sorted(got["test"]) == ["a", "b"] and got.set_index("test").loc["a", "observed"] == 9.0
    draws.save(tmp_path, [])


if __name__ == "__main__":
    import tempfile
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(Path(tempfile.mkdtemp())) if "tmp_path" in fn.__annotations__ else fn()
    print("ok")

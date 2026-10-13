"""Encargo 66, the data reviewer's findings on the draws shards: names, concurrency and the deferred fold."""

from pathlib import Path

import numpy as np
import pandas as pd

from core.study import draws


def _rows(name: object, test: str = "t", seed: int = 0) -> list[dict]:
    """One draws row for strategy `name`."""
    return [draws.record(test, "z", 1.0, np.random.default_rng(seed).normal(size=50), strategy=name)]


def test_names_that_sanitise_alike_keep_their_own_shard(tmp_path: Path) -> None:
    """`a/b` and `a_b` each keep their rows, with different test sets."""
    draws.merge(tmp_path, _rows("a/b", "t1"), defer=True)
    draws.merge(tmp_path, _rows("a_b", "t2"), defer=True)
    assert len(list((tmp_path / draws.SHARDS).glob("*.parquet"))) == 2
    got = draws.read(tmp_path)
    assert sorted(zip(got["strategy"], got["test"])) == [("a/b", "t1"), ("a_b", "t2")]


def test_a_row_without_strategy_survives_the_fold(tmp_path: Path) -> None:
    """A None strategy is not dropped by the groupby."""
    draws.merge(tmp_path, _rows(None), defer=True)
    got = draws.read(tmp_path)
    assert got is not None and len(got) == 1


def _two_tests(args: tuple[str, str]) -> None:
    """Merge one test of strategy S into the shards under (path, test name)."""
    draws.merge(Path(args[0]), _rows("S", args[1], seed=len(args[1])), defer=True)


def test_two_tests_of_one_strategy_written_concurrently_lose_nothing(tmp_path: Path) -> None:
    """Sixteen tests of one strategy by eight processes: sixteen rows after the fold."""
    import multiprocessing as mp
    with mp.get_context("fork").Pool(8) as pool:
        pool.map(_two_tests, [(str(tmp_path), "t" * (i + 1)) for i in range(16)])
    assert len(draws.read(tmp_path)) == 16


def _old_merge(path: Path, rows: list[dict]) -> None:
    """The merge as it was: read the file, drop the rows of the same tests and strategies, append."""
    new, f = pd.DataFrame(rows), path / draws.FILE
    if f.exists():
        old = pd.read_parquet(f)
        gone = old["test"].isin(set(new["test"])) & old["strategy"].isin(set(new["strategy"]))
        new = pd.concat([old[~gone], new], ignore_index=True)
    draws._write(f, new)


def test_deferred_fold_equals_the_old_merge_in_row_order(tmp_path: Path) -> None:
    """Same rows in the same ORDER as merging one after another the old way."""
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    batches = [_rows("s0", "a"), _rows("s1", "a", 1), _rows("s0", "b", 2), _rows("s1", "a", 3), _rows("s2", "b", 4)]
    for b in batches:
        _old_merge(old, b)
        draws.merge(new, b, defer=True)
    pd.testing.assert_frame_equal(draws.read(new).map(lambda v: v.tolist() if hasattr(v, "tolist") else v),
                                  pd.read_parquet(old / draws.FILE).map(lambda v: v.tolist() if hasattr(v, "tolist") else v))

"""Encargo 66 §1.1: concurrent `--strategy` merges keep every row, consolidate == serial merge, save is fast."""

import multiprocessing as mp
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.study import draws

NAMES = [f"s{i}" for i in range(16)]


def _rows(name: str, test: str = "t") -> list[dict]:
    """One strategy's recorded distribution, seeded by its name."""
    rng = np.random.default_rng(sum(map(ord, name + test)))
    return [draws.record(test, "z", 1.0, rng.normal(size=200), strategy=name, seed=1)]


def _deferred(args: tuple[str, str]) -> None:
    """One process writes one strategy's rows, deferred."""
    draws.merge(Path(args[0]), _rows(args[1]), defer=True)


def _norm(df: pd.DataFrame) -> pd.DataFrame:
    """Rows in a canonical order, lists as tuples, so frames compare."""
    df = df.copy()
    for c in draws.LISTS + ("counts",):
        df[c] = df[c].map(lambda v: tuple(np.asarray(v).tolist()))
    return df.sort_values(["test", "strategy"]).reset_index(drop=True)


def test_deferred_by_8_processes_consolidates_to_the_serial_result(tmp_path: Path) -> None:
    """16 strategies by 8 processes: all present, equal to serial `merge`s; shards gone."""
    par, ser = tmp_path / "par", tmp_path / "ser"
    ser.mkdir()
    draws.merge(par, _rows("s0", "old"))                       # a population row that must stay
    draws.merge(ser, _rows("s0", "old"))
    with mp.get_context("fork").Pool(8) as pool:
        pool.map(_deferred, [(str(par), n) for n in NAMES], chunksize=1)
    assert not (par / draws.FILE).exists() or len(pd.read_parquet(par / draws.FILE)) == 1
    for n in NAMES:
        draws.merge(ser, _rows(n))
    assert draws.consolidate(par) == 16 and draws.consolidate(par) == 0
    got = pd.read_parquet(par / draws.FILE)
    assert len(got) == 17 and not list((par / draws.SHARDS).glob("*.parquet"))
    pd.testing.assert_frame_equal(_norm(got), _norm(pd.read_parquet(ser / draws.FILE)))


def test_deferred_replaces_only_its_own_rows(tmp_path: Path) -> None:
    """A deferred rerun of one strategy replaces its rows of the same test, nothing else."""
    draws.merge(tmp_path, _rows("a") + _rows("b"))
    draws.merge(tmp_path, [draws.record("t", "z", 9.0, np.arange(5.0), strategy="a")], defer=True)
    draws.consolidate(tmp_path)
    got = pd.read_parquet(tmp_path / draws.FILE).set_index("strategy")
    assert len(got) == 2 and got.loc["a", "observed"] == 9.0 and got.loc["b", "observed"] == 1.0


def test_save_timing_level_9(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Prints the time of one save of 600 raw rows; the 19-level figure is the audit's 23.8 s per 6,000."""
    rows = [draws.record("t", "z", 0.0, np.random.default_rng(i).normal(size=5000), strategy=f"s{i}")
            for i in range(600)]
    t = time.perf_counter()
    draws.save(tmp_path, rows)
    with capsys.disabled():
        print(f"\nsave 600 rows x 5000 draws: {time.perf_counter() - t:.2f} s")
    assert len(pd.read_parquet(tmp_path / draws.FILE)) == 600


def _read_n(folder: str) -> int:
    """A reader's view: how many rows it sees."""
    got = draws.read(Path(folder))
    return 0 if got is None else len(got)


def test_plain_read_sees_deferred_rows(tmp_path: Path) -> None:
    """No explicit consolidate: `read` folds the pending files and returns the row."""
    draws.merge(tmp_path, _rows("a"), defer=True)
    got = draws.read(tmp_path)
    assert list(got["strategy"]) == ["a"] and not list((tmp_path / draws.SHARDS).glob("*.parquet"))


def test_concurrent_readers_during_deferred_writers_lose_nothing(tmp_path: Path) -> None:
    """8 writers and 2 readers at once; once all are done, every strategy is there exactly once."""
    with mp.get_context("fork").Pool(8) as pool:
        w = pool.map_async(_deferred, [(str(tmp_path), n) for n in NAMES], chunksize=1)
        r = [pool.apply_async(_read_n, (str(tmp_path),)) for _ in range(2)]
        w.get()
        [x.get() for x in r]
    got = draws.read(tmp_path)
    assert sorted(got["strategy"]) == sorted(NAMES)


def test_reset_clears_both(tmp_path: Path) -> None:
    """`reset` removes the parquet and the pending files: nothing comes back at the next read."""
    draws.merge(tmp_path, _rows("a"))
    draws.merge(tmp_path, _rows("b"), defer=True)
    draws.reset(tmp_path)
    assert draws.read(tmp_path) is None


def test_two_threads_through_consolidate_lose_no_row(tmp_path: Path) -> None:
    """The lock is per thread: a second thread waits instead of walking in on the first one's fold."""
    import threading
    for n in NAMES:
        draws.merge(tmp_path, _rows(n), defer=True)
    errors: list[BaseException] = []
    orig = draws._write

    def slow(path: Path, df: pd.DataFrame) -> None:
        """`_write` after a pause."""
        time.sleep(0.3)             # widens the window in which a second thread would overlap
        orig(path, df)

    def go() -> None:
        """Consolidate, collecting any error."""
        try:
            draws.consolidate(tmp_path)
        except BaseException as exc:
            errors.append(exc)

    draws._write = slow
    try:
        ts = [threading.Thread(target=go) for _ in range(2)]
        [t.start() for t in ts]
        [t.join() for t in ts]
    finally:
        draws._write = orig
    assert not errors and len(pd.read_parquet(tmp_path / draws.FILE)) == len(NAMES)

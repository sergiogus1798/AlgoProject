"""Encargo 66 §9.8: the tick file decoded by jobs of blocks equals the serial decode (the oracle)."""

import functools
import struct
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from core import tickfile, tickparallel
from tests.test_spread import ASIS, MINUS, PLUS, T0, record, utf


def _write(path: Path, ticks: list[tuple[int, int, int]]) -> None:
    """A plain 4.2 tick file as SQX writes it: every block opens with an absolute record."""
    out = [
        utf("4.2"),
        utf("D"),
        utf("ABCDEFGH"),
        struct.pack(">qi", 0, 0),
        utf("SnRbTs"),
    ]
    prev = None
    for n, (t, ask, bid) in enumerate(ticks):
        if n % 1000 == 0:
            out.append(bytes(range(15)) + struct.pack(">i", n // 1000))
        if n % 1000 == 0:
            out.append(
                record([(t, 8, ASIS), (ask, 8, ASIS), (bid, 8, ASIS), (0, 1, ASIS)])
            )
        else:
            fields = []
            for now, was in ((t, prev[0]), (ask, prev[1]), (bid, prev[2])):
                d = now - was
                fields.append(
                    (
                        abs(d),
                        1 if abs(d) < 256 else 2 if abs(d) < 65536 else 4,
                        PLUS if d >= 0 else MINUS,
                    )
                )
            out.append(record(fields + [(0, 1, PLUS)]))
        prev = (t, ask, bid)
    path.write_bytes(b"".join(out))


def _ticks(n: int, seed: int) -> list[tuple[int, int, int]]:
    """n ticks: bursts of 1-60 ms steps (whole blocks inside one minute) and gaps up to 3 minutes."""
    rng = np.random.default_rng(seed)
    gap = np.where(
        rng.random(n) < 0.002, rng.integers(1_000, 180_000, n), rng.integers(1, 60, n)
    )
    t = T0 + np.cumsum(gap)
    bid = 100_000_000 + np.cumsum(rng.integers(-50, 51, n))
    return list(
        zip(t.tolist(), (bid + rng.integers(100, 900, n)).tolist(), bid.tolist())
    )


@pytest.mark.parametrize(
    "n,size", [(61_500, 4), (61_500, 7), (23_000, 2), (200_000, 16)]
)
def test_jobs_equal_serial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, n: int, size: int
) -> None:
    """Same minutes, same columns, same tick count as the serial decode, with minutes straddling jobs."""
    path = tmp_path / "X_TICK.dat"
    _write(path, _ticks(n, seed=n + size))
    want, ticks = tickfile.read(path)  # fewer than 2 jobs of 4096 blocks: serial
    decode = tickparallel.decode
    monkeypatch.setattr(tickparallel, "decode", functools.partial(decode, size=size))
    got, count = tickfile.read(path)
    assert count == ticks == n
    assert_frame_equal(got, want, check_exact=True)
    assert (got.index == want.index).all() and (got["n"] == want["n"]).all()
    buf = np.memmap(path, np.uint8, mode="r")
    starts, _, _ = tickparallel.skeleton(buf, tickfile._data_start(buf))
    assert len(starts) == -(-n // 1000)
    assert (
        decode(buf, tickfile._data_start(buf), size) is not None
    )  # the jobs ran, not the fallback


def test_not_absolute_falls_back(tmp_path: Path) -> None:
    """A block that does not open with an absolute record is refused (None): the serial decode runs."""
    from tests.test_spread import write

    path = tmp_path / "X_TICK.dat"
    write(path, _ticks(30_000, 1))  # only the first tick as-is
    buf = np.memmap(path, np.uint8, mode="r")
    assert tickparallel.decode(buf, tickfile._data_start(buf), 4) is None


def _serial(path: Path) -> tuple[pd.DataFrame, int]:
    """The oracle: `tickfile._minutes` over the whole file, as `read` frames it."""
    buf = np.memmap(path, np.uint8, mode="r")
    stamp, rows, ticks = tickfile._minutes(buf, tickfile._data_start(buf), 400_000)
    frame = pd.DataFrame(
        rows, columns=tickfile.COLUMNS, index=pd.to_datetime(stamp, unit="ms")
    )
    frame.index.name = "t"
    return frame.astype({"n": np.int32}), int(ticks)


def test_time_back_at_a_job_edge_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Time jumping back exactly where job 1 starts (tick 4000): None, and the read equals the serial one."""
    ticks = _ticks(30_000, 5)
    ticks = ticks[:4000] + [(t - 3 * 86_400_000, a, b) for t, a, b in ticks[4000:]]
    path = tmp_path / "X_TICK.dat"
    _write(path, ticks)
    buf = np.memmap(path, np.uint8, mode="r")
    assert tickparallel.decode(buf, tickfile._data_start(buf), 4) is None
    monkeypatch.setattr(
        tickparallel, "decode", functools.partial(tickparallel.decode, size=4)
    )
    got, count = tickfile.read(path)
    want, n = _serial(path)
    assert count == n
    assert_frame_equal(got, want, check_exact=True)


@pytest.mark.parametrize("cut", [1, 5, 11, 20])
def test_truncated_tail_equals_serial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cut: int
) -> None:
    """A file cut mid-record: jobs or fallback, the frame and the tick count equal the serial decode."""
    path = tmp_path / "X_TICK.dat"
    _write(path, _ticks(30_000, 6))
    path.write_bytes(path.read_bytes()[:-cut])
    monkeypatch.setattr(
        tickparallel, "decode", functools.partial(tickparallel.decode, size=4)
    )
    got, count = tickfile.read(path)
    want, n = _serial(path)
    assert count == n
    assert_frame_equal(got, want, check_exact=True)

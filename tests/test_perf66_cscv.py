#!/usr/bin/env python3
"""Encargo 66 §9.23: the fused row kernel of the CSCV returns what the numpy passes it replaced did."""

import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.cscv.measure import cscv

KEYS = ("pick", "sr_in", "sr_out", "omega", "hist", "lo", "hi", "track_out", "track_omega")


def oracle(got: dict, member: np.ndarray, chunk: int, bins: int, reach: float,
           track: int | None = None) -> dict:
    """`cscv.run` as it stood before the kernel (2026-10-13): argmax, rank and histogram in numpy."""
    n, s1, s2 = got["n"], got["s1"], got["s2"]
    all_n, all1, all2 = n.sum(), s1.sum(axis=0), s2.sum(axis=0)
    flat = (n[:, None] * s2 - s1 * s1 <= cscv.FLAT * n[:, None] * s2).sum(axis=0)
    safe = bool(flat.max() < len(n) // 2)
    halves, width = member.shape[0], s1.shape[1]
    lo, hi = cscv.edges(got, reach)
    per_bin = bins / (hi - lo)
    out = {"pick": np.empty(2 * halves, np.int64), "sr_in": np.empty(2 * halves),
           "sr_out": np.empty(2 * halves), "omega": np.empty(2 * halves),
           "hist": np.zeros(bins, np.int64), "lo": lo, "hi": hi}
    if track is not None:
        out |= {"track_out": np.empty(2 * halves), "track_omega": np.empty(2 * halves)}
    for at in range(0, halves, chunk):
        take = member[at:at + chunk]
        rows = np.arange(len(take))
        size = (take @ n)[:, None]
        a1, a2 = take @ s1, take @ s2
        b1, b2 = all1 - a1, all2 - a2
        first = cscv.sharpe(size, a1, a2, safe)
        second = cscv.sharpe(all_n - size, b1, b2, safe)
        for side, (train, test) in enumerate(((first, second), (second, first))):
            to = slice(at + side * halves, at + side * halves + len(take))
            pick = train.argmax(axis=1)
            chosen = test[rows, pick]
            out["pick"][to], out["sr_in"][to], out["sr_out"][to] = pick, train[rows, pick], chosen
            out["omega"][to] = (np.count_nonzero(test < chosen[:, None], axis=1) + 1) / (width + 1)
            if track is not None:
                own = test[:, track]
                out["track_out"][to] = own
                out["track_omega"][to] = ((np.count_nonzero(test < own[:, None], axis=1) + 1)
                                          / (width + 1))
            cell = ((test - lo) * per_bin).astype(np.int64)
            np.clip(cell, 0, bins - 1, out=cell)
            out["hist"] += np.bincount(cell.ravel(), minlength=bins)
    return out


def panel(kind: str) -> np.ndarray:
    """An adversarial panel, weeks x variants."""
    rng = np.random.default_rng(66)
    x = rng.normal(0.02, 1.0, (203, 24))
    if kind == "ties":          # identical columns and a coarse grid: ties in and out of sample
        x = np.round(x)
        x[:, 5:9] = x[:, [4]]
    elif kind == "one":
        x = x[:, :1]
    elif kind == "constant":    # a column that never moves, one that moves in one block only
        x[:, 2], x[:, 7], x[:4, 7] = 0.3, 0.0, 1.0
    elif kind == "all_flat":
        x = np.full((203, 6), 0.1)
    elif kind == "nan":
        x[17, 3] = np.nan
    elif kind == "nan_first":   # the first column, so argmax's «first NaN» is column 0
        x[0, 0], x[90, 11] = np.nan, np.nan
    elif kind == "inf":
        x[40, 9], x[41, 10] = np.inf, -np.inf
    elif kind == "huge":        # cancellation in n·Σx² − (Σx)²
        x[:, 1] = 1e9 + 1e-4 * x[:, 1]
        x[:, 4] *= 1e-200
    elif kind == "short":       # fewer rows than two per block
        x = x[:20]
    return x


def same(values: np.ndarray, blocks: int, chunk: int, bins: int, track: int | None) -> None:
    """Assert both implementations agree bit for bit, dtype included, NaN equal to NaN."""
    member = cscv.partitions(blocks)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        want = oracle(cscv.sums(values, blocks), member, chunk, bins, 6.0, track)
        got = cscv.run(cscv.sums(values, blocks), member, chunk, bins, 6.0, track)
    assert set(got) == set(want)
    for key in KEYS:
        if key in want:
            a, b = np.asarray(got[key]), np.asarray(want[key])
            assert a.dtype == b.dtype and a.shape == b.shape, key
            assert np.array_equal(a, b, equal_nan=a.dtype.kind == "f"), key
            if a.dtype.kind == "f":     # the sign of a zero too
                assert np.array_equal(np.signbit(a), np.signbit(b)), key


@pytest.mark.parametrize("kind", ["plain", "ties", "one", "constant", "all_flat", "nan",
                                  "nan_first", "inf", "huge", "short"])
@pytest.mark.parametrize("blocks", [4, 6, 10])
def test_same_numbers(kind: str, blocks: int) -> None:
    """Every adversarial panel, even and odd block counts, with and without a tracked column."""
    values = panel(kind)
    for track in (None, 0, values.shape[1] - 1):
        for chunk in (1, 7, 10_000):
            same(values, blocks, chunk, 64, track)


def test_production_shape() -> None:
    """16 blocks (12,870 partitions), 520 weeks, 1,000 variants, 512 bins, chunks of 128."""
    values = np.random.default_rng(1).standard_t(5, (520, 1000)) * 0.02 + 0.001
    same(values, 16, 128, 512, 437)
    same(values[:, :30], 16, 128, 512, None)


def test_ties_take_the_first_and_rank_lowest() -> None:
    """Two identical best columns: the first is picked and neither counts as below the other."""
    values = panel("plain")
    values[:, 0] += 0.5
    values[:, 1] = values[:, 0]
    found = cscv.run(cscv.sums(values, 10), cscv.partitions(10), 64, 64, 6.0)
    assert not (found["pick"] == 1).any() and (found["pick"] == 0).any()
    alone = cscv.run(cscv.sums(values[:, [0] + list(range(2, 24))], 10), cscv.partitions(10),
                     64, 64, 6.0)
    top = found["pick"] == 0
    assert np.array_equal(found["omega"][top] * 25, alone["omega"][top] * 24)


def test_odd_or_tiny_block_counts_are_refused() -> None:
    """Owner P8: an odd count is not the published statistic."""
    for blocks in (1, 3, 7, 15):
        with pytest.raises(ValueError, match="even number of blocks"):
            cscv.partitions(blocks)
    assert cscv.partitions(4).shape == (3, 4)

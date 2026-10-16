"""Encargo 66 §3.4 and §3.9c: the gate's resampling made lighter gives the numbers it gave — each oracle below is the code replaced."""

import itertools
import time
import tracemalloc
import warnings
from collections.abc import Callable

import numpy as np
import pytest

from core import metrics
from studies.screening.analysis import improvement, resample


def old_drawdowns(
    build: np.ndarray,
    mean: float,
    length: int,
    block: int,
    sequences: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """`resample.null_drawdowns` before the streaming kernel: index matrix, copy, cumsum."""
    shifted = build - build.mean() + mean
    block = min(block, len(shifted))
    starts = rng.integers(0, len(shifted) - block + 1, (sequences, -(-length // block)))
    index = (starts[:, :, None] + np.arange(block)).reshape(sequences, -1)[:, :length]
    curve = np.cumsum(shifted[index], axis=-1)  # the old max_drawdown, frozen here
    return (np.maximum(np.maximum.accumulate(curve, axis=-1), 0.0) - curve).max(axis=-1)


def old_q_null(
    values: np.ndarray, sizes: np.ndarray, permutations: int, rng: np.random.Generator
) -> tuple:
    """`resample.q_null` before the in-place kernel: one permutations x trades matrix."""
    centred = values - values.mean()
    starts = np.cumsum(sizes) - sizes
    between = (
        np.add.reduceat(
            rng.permuted(np.tile(centred, (permutations, 1)), axis=1), starts, axis=1
        )
        ** 2
        / sizes
    ).sum(axis=1)
    observed = (np.add.reduceat(centred, starts) ** 2 / sizes).sum()
    return (
        between,
        float(observed),
        len(centred) * np.finfo(float).eps * (centred @ centred),
    )


def old_resampled(
    rng: np.random.Generator, kept: np.ndarray, level: float, draws: int
) -> tuple:
    """`improvement._resampled` before the chunks: the draws x survivors matrix whole."""
    draw = kept[rng.integers(0, kept.size, (draws, kept.size))]
    return np.median(draw, axis=1), (draw > level).mean(axis=1)


def same(a: np.ndarray, b: np.ndarray) -> bool:
    """Bit for bit, a NaN equal to a NaN in the same place."""
    return a.dtype == b.dtype and np.array_equal(a, b, equal_nan=True)


def peak(call: Callable[[], object]) -> int:
    """Bytes at the high-water mark of one call."""
    tracemalloc.start()
    call()
    top = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return top


def clock(call: Callable[[], object]) -> float:
    """Seconds of the faster of two calls."""
    took = []
    for _ in range(2):
        start = time.perf_counter()
        call()
        took.append(time.perf_counter() - start)
    return min(took)


def dd_cases() -> list[tuple]:
    """The 335 cases of the prototype (`v4b/j2a.py`): (label, build, oos, block, sequences)."""
    g = np.random.default_rng(3)
    cases = []
    for nb, length, block in itertools.product(
        (1, 2, 3, 7, 8, 9, 50, 1500), (1, 2, 7, 8, 9, 17, 300, 301), (1, 3, 8, 64, 5000)
    ):
        cases.append(
            (
                f"grid {nb} {length} {block}",
                g.standard_t(3, nb) * 100,
                g.standard_t(3, length) * 100 + 3,
                block,
                2000,
            )
        )
    b0, p0 = g.standard_t(3, 1500) * 100, g.standard_t(3, 300) * 100
    spot = np.arange(1500) == 700
    cases += [
        ("length not a multiple of the block", b0, p0, 7, 5000),
        ("block longer than the build", b0[:5], p0, 8, 5000),
        ("build of one trade", b0[:1], p0, 8, 5000),
        ("oos of one trade", b0, p0[:1], 8, 5000),
        ("all positive", np.abs(b0) + 1, np.abs(p0) + 1, 8, 5000),
        ("all negative", -np.abs(b0) - 1, -np.abs(p0) - 1, 8, 5000),
        ("constant build", np.full(200, 5.0), p0, 8, 5000),
        ("1e15 and cents", b0 * 1e13 + 0.01, p0 * 1e13, 8, 5000),
        ("whole cents", np.round(b0), np.round(p0), 8, 5000),
        ("20000 sequences, five draws of block starts", b0, p0, 8, 20000),
        ("three blocks a sequence, odd count", b0, p0[:17], 8, 20001),
        ("build of 70000", g.standard_t(3, 70000), p0, 8, 5000),
        ("NaN in the build", np.where(spot, np.nan, b0), p0, 8, 5000),
        (
            "NaN in oos, so in the mean",
            b0,
            np.where(np.arange(300) == 10, np.nan, p0),
            8,
            5000,
        ),
        ("inf in the build", np.where(spot, np.inf, b0), p0, 8, 5000),
    ]
    return cases


def test_drawdowns_are_the_old_ones() -> None:
    """3.4a: vector, `dd_p`, `dd_esperado_r` and the generator's state, on the 335 cases and the edges."""
    g = np.random.default_rng(8)
    b0, p0 = g.standard_t(3, 1500) * 100, g.standard_t(3, 300) * 100
    spot = np.arange(1500) == 700
    extra = [
        ("-inf in the build", np.where(spot, -np.inf, b0), p0, 8, 5000),
        (
            "both infinities",
            np.where(spot, np.inf, np.where(np.arange(1500) == 9, -np.inf, b0)),
            p0,
            8,
            5000,
        ),
        ("overflow to inf", np.full(50, 1e308), np.full(40, 1e308), 8, 500),
        ("one sequence", b0, p0, 8, 1),
        ("all trades equal", np.full(300, -7.5), np.full(120, -7.5), 8, 5000),
        ("all zero", np.zeros(300), np.zeros(120), 8, 5000),
        ("one trade each side", b0[:1], p0[:1], 1, 5000),
        ("integers in", np.arange(-40, 60), np.arange(-9, 30), 8, 5000),
    ]
    cases = dd_cases()
    assert len(cases) == 335
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore")
        for label, build, pnl, block, sequences in cases + extra:
            r0, r1 = resample.stream(42, "id"), resample.stream(42, "id")
            a = old_drawdowns(build, pnl.mean(), len(pnl), block, sequences, r0)
            b = resample.null_drawdowns(
                build, pnl.mean(), len(pnl), block, sequences, r1
            )
            assert same(a, b), label
            assert r0.bit_generator.state == r1.bit_generator.state, label
            seen = metrics.dd_money(metrics.cumulative(pnl.astype(float)))
            assert resample.p_upper(a, seen) == resample.p_upper(b, seen), label
            assert same(np.percentile(a, 95) / 250.0, np.percentile(b, 95) / 250.0), (
                label
            )
    # No trades on a side is an error on both, never a drawdown of zero.
    for build, length, error in ((b0, 0, ValueError), (b0[:0], 5, ZeroDivisionError)):
        for form in (old_drawdowns, resample.null_drawdowns):
            with pytest.raises(error), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                form(build, 1.0, length, 8, 10, resample.stream(1, "x"))


def before(kind: int) -> np.random.Generator:
    """A stream in one of five states, one of them with half a 64-bit output still unspent."""
    rng = resample.stream(9 + kind % 2, "k" * (1 + kind // 3))
    if kind in (1, 4):
        rng.integers(0, 10, 3)  # three 32-bit halves: `has_uint32` is left set
    if kind == 2:
        rng.random(5)
    return rng


def q_same(
    values: np.ndarray, sizes: np.ndarray, permutations: int, kind: int = 0
) -> bool:
    """Whether q_null gives what the old one gave: null, observed, slack, p and state after."""
    r0, r1 = before(kind), before(kind)
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore")
        a, b = (
            old_q_null(values, sizes, permutations, r0),
            resample.q_null(values, sizes, permutations, r1),
        )
        ok = same(a[0], b[0]) and same(np.array(a[1:]), np.array(b[1:]))
        if permutations:
            ok = ok and resample.p_upper(*a) == resample.p_upper(*b)
    return ok and r0.bit_generator.state == r1.bit_generator.state


def test_q_null_is_the_old_one() -> None:
    """3.9c: the 525 combinations of the prototype (`v4b/j2b.py`), its chunk sizes now stream states."""
    done = 0
    for n, groups in itertools.product(
        (2, 3, 7, 8, 9, 31, 300, 1000, 1001), (2, 3, 12)
    ):
        if groups > n:
            continue
        values = np.random.default_rng(n * 100 + groups).standard_t(3, n) * 100
        sizes = np.full(groups, n // groups)
        sizes[-1] += n - sizes.sum()
        for permutations, kind in itertools.product(
            (1, 5, 4096, 5000, 12345), range(5)
        ):
            assert q_same(values, sizes, permutations, kind), (
                n,
                groups,
                permutations,
                kind,
            )
            done += 1
    assert done == 525


def test_q_null_on_the_edges() -> None:
    """3.9c: the cases of `p5py/p2.py`, the sums numpy splits, and inputs that are not a clean sample."""
    g = np.random.default_rng(3)
    for n, groups in (
        (120, 4),
        (300, 6),
        (300, 12),
        (1000, 12),
        (3000, 12),
        (17, 2),
        (2000, 200),
        (2000, 700),
        (20001, 2),
        (400, 400),
    ):
        values = np.round(g.normal(5, 80, n), 2)
        cut = np.sort(g.choice(np.arange(1, n), groups - 1, replace=False))
        assert q_same(values, np.diff(np.r_[0, cut, n]), 5 if n > 5000 else 1500), (
            n,
            groups,
        )
    values = g.standard_t(3, 96) * 100
    sizes = np.array([20, 30, 46])
    assert q_same(values, sizes, 1) and q_same(values, sizes, 0)
    assert q_same(values, np.array([96]), 300), "one period"
    assert q_same(values, np.array([20, 0, 30, 46]), 300), (
        "an empty period in the middle"
    )
    assert q_same(np.full(96, 3.25), sizes, 300), "all trades equal"
    assert q_same(np.where(np.arange(96) == 7, np.nan, values), sizes, 300), "a NaN"
    assert q_same(np.where(np.arange(96) == 7, np.inf, values), sizes, 300), "an inf"
    assert q_same(values * 1e300, sizes, 300), "squares that overflow"
    assert q_same(np.arange(96), sizes, 300), "integers in"
    assert q_same(values[:1], np.array([1]), 50) and q_same(
        values[:2], np.array([1, 1]), 500
    )
    with pytest.raises(AssertionError):  # 3.4b's invariant: short sizes were swallowed
        resample.q_null(values, np.array([20, 30]), 10, resample.stream(1, "x"))
    with pytest.raises(TypeError):
        resample.q_null(values, sizes, 10, np.random.Generator(np.random.MT19937(1)))
    # The same stream goes on to the same numbers, as tests/test_gate_resample.py uses it.
    r0, r1 = resample.stream(5, "a"), resample.stream(5, "a")
    for _ in range(3):
        a, b = (
            old_q_null(r0.standard_t(4, 96), sizes, 201, r0),
            resample.q_null(r1.standard_t(4, 96), sizes, 201, r1),
        )
        assert same(a[0], b[0])


def test_resampled_in_chunks_is_the_old_one() -> None:
    """3.4d: the same medians, hit rates and generator, with a tenth of the matrix held."""
    g = np.random.default_rng(4)
    population = {
        "t": g.standard_t(3, 1000),
        "one": np.array([0.3]),
        "two": np.array([1.0, -1.0]),
        "equal": np.full(40, 2.0),
        "nan": np.where(np.arange(90) == 5, np.nan, g.normal(size=90)),
        "integers": np.arange(37),
        "seven": g.normal(size=7),
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for (label, kept), draws in itertools.product(
            population.items(), (0, 1, 249, 250, 251, 2000)
        ):
            r0, r1 = np.random.default_rng(11), np.random.default_rng(11)
            for _ in range(2):  # lift() takes block after block off one generator
                a, b = (
                    old_resampled(r0, kept, 0.1, draws),
                    improvement._resampled(r1, kept, 0.1, draws),
                )
                assert same(a[0], b[0]) and same(a[1], b[1]), (label, draws)
            assert r0.bit_generator.state == r1.bit_generator.state, (label, draws)
    y = g.standard_t(3, 3000)
    mask = y > np.quantile(y, 0.6)
    assert improvement.lift(y, mask, 0.0, reach=6000)["p"] > 0
    kept = g.normal(size=4000)
    was = peak(lambda: old_resampled(np.random.default_rng(1), kept, 0.0, 2000))
    now = peak(
        lambda: improvement._resampled(np.random.default_rng(1), kept, 0.0, 2000)
    )
    print(
        f"\n3.4d _resampled 2000 x 4000: peak {was / 1e6:.0f} MB -> {now / 1e6:.0f} MB"
    )
    assert now < was / 4


def test_it_is_faster() -> None:
    """3.4a and 3.9c on one core: the same call before and after, printed, and never slower."""
    g = np.random.default_rng(2)
    resample.null_drawdowns(g.normal(size=50), 0.0, 20, 8, 10, resample.stream(1, "x"))
    resample.q_null(g.normal(size=40), np.array([20, 20]), 3, resample.stream(1, "x"))
    print()
    for nb, length in ((1500, 300), (5000, 1000)):
        build, mean = g.standard_t(3, nb) * 100, 3.0
        was = clock(
            lambda: [
                old_drawdowns(build, mean, length, 8, 5000, resample.stream(1, "x"))  # noqa: B023 timed immediately
                for _ in range(8)
            ]
        )
        now = clock(
            lambda: resample.null_drawdowns(
                build, mean, length, 8, 40_000, resample.stream(1, "x")
            )
        )  # noqa: B023 timed immediately
        print(
            f"3.4a drawdowns build {nb} oos {length}: {was / 4e4 * 1e6:.2f} -> "
            f"{now / 4e4 * 1e6:.2f} us per sequence (x{was / now:.1f})"
        )
        assert now < was
    for n, groups, permutations in (
        (120, 4, 40_000),
        (300, 12, 20_000),
        (1000, 12, 6000),
    ):
        values, sizes = np.round(g.normal(5, 80, n), 2), np.full(groups, n // groups)
        sizes[-1] += n - sizes.sum()
        was = clock(
            lambda: old_q_null(values, sizes, permutations, resample.stream(1, "x"))
        )  # noqa: B023 timed immediately
        now = clock(
            lambda: resample.q_null(
                values, sizes, permutations, resample.stream(1, "x")
            )
        )  # noqa: B023 timed immediately
        print(
            f"3.9c q_null n {n} periods {groups}: {was / permutations * 1e6:.2f} -> "
            f"{now / permutations * 1e6:.2f} us per shuffle (x{was / now:.1f}), "
            f"matrix {permutations * n * 8 / 1e6:.0f} MB -> 0"
        )
        assert now < was

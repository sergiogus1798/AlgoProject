#!/usr/bin/env python3
"""Known-answer and property checks of the resampling index generators against their textbook definitions."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from scipy import stats

from engines.resample import draws as D

RES = {"pass": 0, "bad": 0}
Z = 3.2905  # two-sided 99.9 % normal quantile


def report(name: str, ok: bool, detail: str = "") -> None:
    """Count and print one check."""
    RES["pass" if ok else "bad"] += 1
    print(("PASS " + name) if ok else f"FAIL {name}: {detail}")


def guard(name: str) -> Callable:
    """Decorate a check so an exception counts as an ERROR and the script continues."""

    def deco(fn: Callable) -> Callable:
        """Wrap `fn` in the error guard."""

        def run(*a: Any, **k: Any) -> None:
            """Call `fn`, reporting any exception."""
            fn(*a, **k)

        return run

    return deco


def draw(fn: str, n: int, size: int, block: int, seed: int) -> Any:
    """Draw `n` index rows from the generator named `fn` with a fixed seed."""
    return getattr(D, fn)(n, size, np.random.default_rng(seed), block)


def chi2_uniform(values: Any, size: int, name: str) -> None:
    """Report a chi-square test that `values` are uniform on 0..size-1."""
    counts = np.bincount(np.asarray(values).ravel(), minlength=size)
    chi, p = stats.chisquare(counts)
    report(name, p > 0.001, f"chi2={chi:.1f} p={p:.2g} (uniform expected, alpha 0.001)")


def steps_break(a: Any, size: int, circular: bool) -> Any:
    """Mark the steps between consecutive indices that are not +1."""
    d = np.diff(a, axis=1)
    return (d != 1) & ((d % size) != 1) if circular else d != 1


PAIRS = [(10, 3), (12, 4), (7, 1), (9, 20), (10, 10), (50, 7)]
ALL = ["iid_shuffle", "block_shuffle", "stationary", "iid_bootstrap", "block_bootstrap"]


@guard("generic")
def generic() -> None:
    """Shape, dtype, range and seed behaviour of every generator."""
    for fn in ALL:
        for size, block in PAIRS:
            a = draw(fn, 40, size, block, 1)
            tag = f"{fn} size={size} block={block}"
            report(
                f"shape/dtype/range {tag}",
                a.shape == (40, size)
                and np.issubdtype(a.dtype, np.integer)
                and a.min() >= 0
                and a.max() < size,
                f"shape={a.shape} dtype={a.dtype} range=({a.min()},{a.max()})",
            )
        a1, a2, b = (
            draw(fn, 30, 25, 5, 7),
            draw(fn, 30, 25, 5, 7),
            draw(fn, 30, 25, 5, 8),
        )
        report(f"same seed same array {fn}", np.array_equal(a1, a2))
        report(f"different seed differs {fn}", not np.array_equal(a1, b))


@guard("perm")
def permutations() -> None:
    """Both shuffles return permutations."""
    for fn in ("iid_shuffle", "block_shuffle"):
        for size, block in PAIRS:
            a = draw(fn, 300, size, block, 2)
            ok = (np.sort(a, axis=1) == np.arange(size)).all()
            report(
                f"permutation {fn} size={size} block={block}",
                ok,
                "a row is not a permutation",
            )


@guard("iid_shuffle")
def iid_shuffle_uniform() -> None:
    """The slot of position 0 is uniform under the iid shuffle."""
    a = draw("iid_shuffle", 40000, 10, 1, 3)
    slot = np.argmax(a == 0, axis=1)
    chi2_uniform(slot, 10, "iid_shuffle: slot of position 0 uniform")


@guard("block_shuffle")
def block_shuffle_structure() -> None:
    """Block shuffle keeps blocks whole, on a fixed grid and in order."""
    for size, block in PAIRS:
        a = draw("block_shuffle", 2000, size, block, 4)
        nblk = -(-size // block)
        brk = np.diff(a, axis=1) != 1
        report(
            f"block_shuffle breaks<=blocks size={size} block={block}",
            brk.sum(1).max() <= nblk,
            f"max breaks {brk.sum(1).max()} > {nblk}",
        )
        starts_ok = (a[:, 0] % block == 0).all() and np.where(
            brk, a[:, 1:] % block == 0, True
        ).all()
        report(
            f"block_shuffle fixed boundaries size={size} block={block}",
            bool(starts_ok),
            "a run starts off the grid 0, block, 2*block...",
        )
        chk = (
            (a[:, 1:] % block != 0) <= (np.diff(a, axis=1) == 1)
        ).all()  # inside a block => step +1
        report(
            f"block_shuffle inside order size={size} block={block}",
            bool(chk),
            "inside-block step differs from +1",
        )
    a = draw("block_shuffle", 40000, 10, 1, 5)
    chi2_uniform(
        np.argmax(a == 0, axis=1),
        10,
        "block_shuffle block=1: slot of position 0 uniform",
    )


@guard("iid_bootstrap")
def iid_bootstrap_checks() -> None:
    """The iid bootstrap is uniform, repeats, and has the expected distinct fraction."""
    size = 20
    a = draw("iid_bootstrap", 20000, size, 1, 6)
    chi2_uniform(a, size, "iid_bootstrap: marginal uniform")
    chi2_uniform(a[:, 0], size, "iid_bootstrap: first slot uniform")
    report("iid_bootstrap: has repeats", any(len(set(r)) < size for r in a[:50]))
    dist = np.array([len(set(r)) for r in a]) / size
    exp = 1 - (1 - 1 / size) ** size
    se = dist.std(ddof=1) / np.sqrt(len(dist))
    report(
        "iid_bootstrap: distinct fraction",
        abs(dist.mean() - exp) < Z * se,
        f"observed={dist.mean():.4f} expected={exp:.4f} band=+-{Z * se:.4f}",
    )


@guard("block_bootstrap")
def block_bootstrap_checks() -> None:
    """Circular block bootstrap: inside steps are +1, starts uniform, breaks bounded."""
    for size, block in [(50, 7), (40, 5), (12, 4)]:
        a = draw("block_bootstrap", 20000, size, block, 9)
        d = np.diff(a, axis=1)
        nblk = -(-size // block)
        inside = np.ones(size - 1, bool)
        inside[block - 1 :: block] = False  # steps that cross an output block boundary
        ok = ((d[:, inside] % size) == 1).all()
        report(
            f"block_bootstrap inside step +1 (mod size) size={size} block={block}",
            bool(ok),
            "inside-block step not +1",
        )
        wrap = (d[:, inside] == 1 - size).any()
        print(
            f"INFO block_bootstrap wraps around the end (circular): {bool(wrap)} (size={size} block={block})"
        )
        chi2_uniform(
            a[:, ::block],
            size,
            f"block_bootstrap block starts uniform size={size} block={block}",
        )
        if wrap:
            for col in (0, size - 1, size // 2):
                chi2_uniform(
                    a[:, col],
                    size,
                    f"block_bootstrap circular marginal col {col} size={size}",
                )
        brk = (steps_break(a, size, True)).sum(1)
        report(
            f"block_bootstrap breaks<=blocks-1 size={size} block={block}",
            brk.max() <= nblk - 1,
            f"max {brk.max()}",
        )


@guard("stationary")
def stationary_checks() -> None:
    """Stationary bootstrap: geometric restart rate, memorylessness and uniform margins."""
    size, n = 300, 4000
    for block in (1, 5, 20, 60):
        a = draw("stationary", n, size, block, 11)
        brk = steps_break(a, size, True)
        p_exp = (1 / block) * (
            1 - 1 / size
        )  # a restart can land on the next position by chance
        k, m = brk.sum(), brk.size
        band = Z * np.sqrt(p_exp * (1 - p_exp) / m)
        report(
            f"stationary restart rate block={block}",
            abs(k / m - p_exp) < band,
            f"observed={k / m:.5f} expected={p_exp:.5f} band=+-{band:.5f}",
        )
        # geometric lengths are memoryless: the restart rate after a restart (length 1) and after a run are both 1/block
        prev, nxt = brk[:, :-1], brk[:, 1:]
        for label, mask in (
            ("after a restart, P(length=1)", prev),
            ("after a continuation", ~prev),
        ):
            mm = mask.sum()
            if mm < 200:
                continue
            q = nxt[mask].mean()
            b2 = Z * np.sqrt(p_exp * (1 - p_exp) / mm)
            report(
                f"stationary memoryless {label} block={block}",
                abs(q - p_exp) < b2,
                f"observed={q:.5f} expected={p_exp:.5f} band=+-{b2:.5f}",
            )
        chi2_uniform(a[:, 0], size, f"stationary marginal col 0 block={block}")
        chi2_uniform(
            a[:, size - 1], size, f"stationary marginal last col block={block}"
        )
    chi2_uniform(
        draw("stationary", 4000, 50, 8, 12),
        50,
        "stationary marginal all slots (size=50 block=8, loose pooled)",
    )


@guard("stationary_vs_arch")
def stationary_vs_arch() -> None:
    """Mean run length of the stationary bootstrap matches the arch library."""
    try:
        from arch.bootstrap import StationaryBootstrap
    except ImportError:
        print("INFO skipped (no arch)")
        return
    size, block, n = 300, 12, 3000
    mine = draw("stationary", n, size, block, 13)
    bs = StationaryBootstrap(block, np.arange(size), seed=13)
    ref = np.array([np.asarray(bs.update_indices()) for _ in range(n)])
    out = []
    for a in (mine, ref):
        brk = steps_break(a, size, True)
        out.append(size / (brk.sum(1) + 1))  # mean run length per row
    se = np.sqrt(out[0].var(ddof=1) / n + out[1].var(ddof=1) / n)
    diff = out[0].mean() - out[1].mean()
    report(
        "stationary mean run length vs arch",
        abs(diff) < Z * se,
        f"project={out[0].mean():.3f} arch={out[1].mean():.3f} diff={diff:.3f} band=+-{Z * se:.3f}",
    )


def ar1(T: int, phi: float, seed: int) -> Any:
    """Simulate an AR(1) series after a 200-step burn-in."""
    e = np.random.default_rng(seed).normal(size=T + 200)
    x = np.zeros(T + 200)
    for t in range(1, T + 200):
        x[t] = phi * x[t - 1] + e[t]
    return x[200:]


@guard("ar1")
def ar1_variance() -> None:
    """On AR(1) data the block methods recover the long-run variance and the iid one understates it."""
    T, phi, block = 2000, 0.6, 20
    x = ar1(T, phi, 21)
    true = 1 / (1 - phi) ** 2 / T
    marg = 1 / (1 - phi**2) / T
    v = {
        fn: draw(fn, 4000, T, block, 22)
        for fn in ("stationary", "block_bootstrap", "iid_bootstrap")
    }
    var = {fn: x[a].mean(1).var(ddof=1) for fn, a in v.items()}
    for fn in ("stationary", "block_bootstrap"):
        report(
            f"AR(1) {fn} variance of mean within 35% of long-run",
            abs(var[fn] / true - 1) < 0.35,
            f"observed={var[fn]:.3e} expected={true:.3e} ratio={var[fn] / true:.2f}",
        )
    r = var["iid_bootstrap"]
    report(
        "AR(1) iid_bootstrap understates (near marginal/T, far below long-run)",
        r < 0.5 * true and abs(r / marg - 1) < 0.35,
        f"observed={r:.3e} marginal/T={marg:.3e} long-run={true:.3e}",
    )


for f in (
    generic,
    permutations,
    iid_shuffle_uniform,
    block_shuffle_structure,
    iid_bootstrap_checks,
    block_bootstrap_checks,
    stationary_checks,
    stationary_vs_arch,
    ar1_variance,
):
    f()
print(f"SUMMARY pass={RES['pass']} bad={RES['bad']}")
sys.exit(1 if RES["bad"] else 0)

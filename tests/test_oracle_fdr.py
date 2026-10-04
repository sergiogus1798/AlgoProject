#!/usr/bin/env python3
"""Oracle test: engines.inference.fdr against scipy and statsmodels BH, plus null and planted-signal calibration."""

import math
import random
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

from engines.inference import fdr

bad = 0


def rep(ok: bool, name: str, msg: str = "") -> None:
    """Print PASS, or FAIL with `msg` and count the failure.

    Args:
        ok: Whether the check held.
        name: Check label.
        msg: Detail printed on failure.
    """
    global bad
    if ok:
        print("PASS", name)
    else:
        bad += 1
        print(f"FAIL {name}: {msg}")


def run(name: str, f: Callable[[], None]) -> None:
    """Run one check, counting an exception as an ERROR.

    Args:
        name: Check label.
        f: The check, called with no arguments.
    """
    global bad
    try:
        f()
    except Exception as e:
        bad += 1
        print(f"ERROR {name}: {type(e).__name__}: {e}")


def rows_of(p: Iterable[float]) -> list[dict]:
    """Wrap p-values as the metric rows fdr expects.

    Args:
        p: The p-values.

    Returns:
        Rows named m0, m1, ... each with its p.
    """
    return [{"metric": f"m{i}", "p": float(x)} for i, x in enumerate(p)]


def a() -> None:
    """adjusted() equals scipy and statsmodels BH on random p-vectors."""
    rng = np.random.default_rng(1)
    worst = 0
    worst2 = 0
    for k in range(200):
        n = int(rng.integers(1, 501))
        p = rng.random(n)
        if k % 3 == 0 and n > 3:
            p = np.round(p, 2)
        if n > 2 and k % 5 == 0:
            p[0] = 0.0
            p[-1] = 1.0
        q = fdr.adjusted(rows_of(p))
        qa = np.array([q[f"m{i}"] for i in range(n)])
        worst = max(worst, np.max(np.abs(qa - stats.false_discovery_control(p, method="bh"))))
        worst2 = max(worst2, np.max(np.abs(qa - multipletests(p, method="fdr_bh")[1])))
    rep(worst <= 1e-12 and worst2 <= 1e-12, "a_adjusted",
        f"max diff scipy {worst:.3g}, statsmodels {worst2:.3g}")


run("a_adjusted", a)


def b() -> None:
    """discoveries() equals statsmodels' rejections and the adjusted q-values at four alphas."""
    rng = np.random.default_rng(2)
    badc = 0
    tot = 0
    for k in range(100):
        n = int(rng.integers(1, 400))
        p = np.round(rng.random(n) ** 2, 3 if k % 2 else 8)
        r = rows_of(p)
        q = fdr.adjusted(r)
        for al in (0.01, 0.05, 0.10, 0.20):
            d = fdr.discoveries(r, al)
            tot += 1
            ref = {f"m{i}" for i in np.where(multipletests(p, alpha=al, method="fdr_bh")[0])[0]}
            ref2 = {m for m, v in q.items() if v <= al}
            if d != ref or d != ref2:
                badc += 1
    rep(badc == 0, "b_discoveries", f"{badc}/{tot} mismatches")


run("b_discoveries", b)


def c() -> None:
    """The Benjamini-Hochberg 1995 worked example gives four discoveries."""
    p = [0.0001, 0.0004, 0.0019, 0.0095, 0.0201, 0.0278, 0.0298, 0.0344, 0.0459, 0.3240,
         0.4262, 0.5719, 0.6528, 0.7590, 1.0]
    d = fdr.discoveries(rows_of(p), 0.05)
    rep(d == {"m0", "m1", "m2", "m3"}, "c_BH1995", f"got {sorted(d)}")


run("c_BH1995", c)


def d() -> None:
    """Under the global null the share of runs with any discovery stays within the alpha band."""
    rng = np.random.default_rng(3)
    al = 0.05
    R = 2000
    hits = 0
    for _ in range(R):
        if fdr.discoveries(rows_of(rng.random(1000)), al):
            hits += 1
    s = hits / R
    band = 2.576 * math.sqrt(al * (1 - al) / R)
    print(f"INFO d_global_null share={s:.4f} alpha={al} 99% band=[{al-band:.4f},{al+band:.4f}]")
    rep(s <= al + band, "d_global_null", f"share {s:.4f} > {al+band:.4f}")


run("d_global_null", d)


def e() -> None:
    """With planted signals the mean false discovery proportion sits at its target."""
    rng = np.random.default_rng(4)
    al = 0.05
    R = 500
    fdp = []
    pw = []
    for _ in range(R):
        p = np.concatenate([rng.random(900), rng.beta(0.05, 1, 100)])
        d = fdr.discoveries(rows_of(p), al)
        idx = {int(x[1:]) for x in d}
        v = sum(i < 900 for i in idx)
        fdp.append(v / max(len(idx), 1))
        pw.append(sum(i >= 900 for i in idx) / 100)
    m = np.mean(fdp)
    se = np.std(fdp, ddof=1) / math.sqrt(R)
    print(f"INFO e_planted meanFDP={m:.5f} se={se:.5f} target={al*0.9:.4f} power={np.mean(pw):.4f}")
    rep(m <= al + 3*se and m >= al*0.9 - 3*se, "e_planted", f"meanFDP {m:.5f} se {se:.5f}")


run("e_planted", e)


def f() -> None:
    """Shuffling the rows changes neither discoveries nor adjusted values."""
    rng = np.random.default_rng(5)
    p = np.round(rng.random(300) ** 2, 3)
    r = rows_of(p)
    s = r[:]
    random.Random(1).shuffle(s)
    ok = (all(fdr.discoveries(r, a) == fdr.discoveries(s, a) for a in (0.01, 0.05, 0.2))
          and fdr.adjusted(r) == fdr.adjusted(s))
    rep(ok, "f_order_invariance", "differs")


run("f_order_invariance", f)


def g() -> None:
    """Report what a NaN p-value does (INFO lines only, nothing asserted)."""
    r = rows_of([0.001, 0.01, 0.5, 0.9])
    r.append({"metric": "nan", "p": float("nan")})
    try:
        d = fdr.discoveries(r, 0.05)
        print(f"INFO g_nan discoveries={sorted(d)} nan_named={'nan' in d}")
    except Exception as e:
        print(f"INFO g_nan discoveries raises {type(e).__name__}: {e}")
    try:
        q = fdr.adjusted(r)
        print(f"INFO g_nan adjusted={q}")
    except Exception as e:
        print(f"INFO g_nan adjusted raises {type(e).__name__}: {e}")


run("g_nan", g)
sys.exit(1 if bad else 0)

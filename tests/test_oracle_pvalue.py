#!/usr/bin/env python3
"""Oracle test: engines.nulls.verdict.pvalue is the exact (1 + count) / (n + 1) rank p-value and calibrated under the null."""

import math
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from engines.nulls import verdict

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
    """Run one check; an exception ends the script with its traceback.

    Args:
        name: Check label.
        f: The check, called with no arguments.
    """
    f()


G = verdict.GOOD_HIGH
print("INFO GOOD_HIGH =", dict(G))
hi = next((k for k, v in G.items() if v is True), None)
lo = next((k for k, v in G.items() if v is False), None)
print(
    f"INFO using high={hi} low={lo}" + ("" if lo else "  (no False direction exists)")
)


def a() -> None:
    """The p-value equals (1 + count of draws at least as good) / (n + 1) on a small tied sample."""
    d = np.array([1.0, 2.0, 2.0, 3.0, 5.0])
    cases = [
        (
            2.0,
            1 + 3,
        ),
        (0.0, 5),
        (9.0, 0),
        (5.0, 1),
        (1.0, 5),
        (3.0, 2),
    ]  # noqa: F841
    for name, up in ((hi, True), (lo, False)):
        if name is None:
            print(f"INFO a_exact skipped direction up={up}")
            continue
        for s in (2.0, 0.0, 9.0, 5.0, 1.0, 3.0):
            cnt = int(np.sum(d >= s)) if up else int(np.sum(d <= s))
            exp = (1 + cnt) / 6
            got = verdict.pvalue(s, d, name)
            rep(
                abs(got - exp) < 1e-15,
                f"a_exact_{'high' if up else 'low'}_seen{s}",
                f"got {got} exp {exp}",
            )


run("a_exact", a)


def null(
    draw: Callable[[Any, int], Any], name: str, tag: str, cons: bool = False
) -> None:
    """Check P(p <= alpha) over many null replications at four alphas.

    Args:
        draw: Called as draw(rng, size), returns the null sample (first value is the seen one).
        name: Metric name passed to verdict.pvalue.
        tag: Label prefix of the checks.
        cons: If True only require conservativeness (p <= alpha), else exactness within a band.
    """
    rng = np.random.default_rng(987654)
    R = 20000
    n = 199
    ps = np.empty(R)
    for i in range(R):
        x = draw(rng, n + 1)
        ps[i] = verdict.pvalue(x[0], x[1:], name)
    for al in (0.01, 0.05, 0.10, 0.50):
        emp = np.mean(ps <= al + 1e-12)
        exp = math.floor(al * 200 + 1e-9) / 200
        band = 2.576 * math.sqrt(max(exp * (1 - exp), 1e-9) / R)
        if cons:
            rep(
                emp <= al + 2.576 * math.sqrt(al * (1 - al) / R),
                f"{tag}_{name}_a{al}",
                f"P(p<=a)={emp:.4f} > a={al}",
            )
        else:
            rep(
                abs(emp - exp) <= band,
                f"{tag}_{name}_a{al}",
                f"P(p<=a)={emp:.4f} expected {exp:.4f} +-{band:.4f}",
            )


def bc() -> None:
    """Calibration under normal, t(2) and tied Poisson nulls, in both directions."""
    for name in (hi, lo):
        if name is None:
            continue
        null(lambda r, n: r.standard_normal(n), name, "b_normal")
        null(lambda r, n: r.standard_t(2, n), name, "b_t2")
        null(lambda r, n: r.poisson(3, n).astype(float), name, "c_poisson", cons=True)


run("bc", bc)


def dd() -> None:
    """An extreme seen value gives exactly 1 / (n + 1), never zero."""
    for name in (hi, lo):
        if name is None:
            continue
        d = np.zeros(99)
        s = 1e9 if G[name] else -1e9
        p = verdict.pvalue(s, d, name)
        rep(abs(p - 1 / 100) < 1e-15 and p > 0, f"d_min_{name}", f"p={p}")


run("dd", dd)


def e() -> None:
    """Report what NaN in the seen value or in the draws does (INFO lines only)."""
    name = hi
    d = np.arange(1.0, 100.0)
    for lab, s, dr in (("seen_nan", float("nan"), d),):
        print(f"INFO e_{lab} -> {verdict.pvalue(s, dr, name)}")
    dn = d.copy()
    dn[:10] = np.nan
    seen = 50.0
    c = int(np.sum(d[10:] >= seen))
    fin = d[10:]
    only = (1 + c) / (len(fin) + 1)
    den = (1 + c) / (len(dn) + 1)
    got = verdict.pvalue(seen, dn, name)
    print(f"INFO e_draws_nan got={got} nonNaN_only={only} NaN_in_denominator={den}")


run("e", e)
sys.exit(1 if bad else 0)

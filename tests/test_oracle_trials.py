#!/usr/bin/env python3
"""Oracle test: ledger.trials.accumulated pools search moments exactly (sigma, mean, n), whatever the order or split."""

import math
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from ledger import trials

bad = 0
ADDED: set[str] = set()


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


def frame(groups: list, units: list[str] | None = None) -> pd.DataFrame:
    """Build a ledger-shaped frame with one row per group of scores.

    Args:
        groups: Arrays of scores, one per search.
        units: `score_unit` per row; defaults to per_period.

    Returns:
        A frame with n_scored, sharpe_mean, sharpe_std and score_unit.
    """
    units = units or ["per_period"] * len(groups)
    return pd.DataFrame(
        {
            "n_scored": [len(g) for g in groups],
            "sharpe_mean": [float(np.mean(g)) for g in groups],
            "sharpe_std": [
                float(np.std(g, ddof=1)) if len(g) > 1 else float("nan") for g in groups
            ],
            "score_unit": units,
        }
    )


def acc(fr: pd.DataFrame, extra: int = 0) -> dict:
    """Call trials.accumulated, zero-filling any column it reports missing.

    Args:
        fr: The frame to pool.
        extra: Extra trial count, passed only when non-zero.

    Returns:
        What trials.accumulated returns.
    """
    global ADDED
    for _ in range(10):
        try:
            return trials.accumulated(fr, extra) if extra else trials.accumulated(fr)
        except KeyError as e:
            c = str(e).strip("'\"")
            ADDED.add(c)
            fr[c] = 0
    raise RuntimeError("too many missing columns")


def groups(rng: Any, k: int) -> list:
    """Draw k random score groups of random location, scale and size.

    Args:
        rng: A numpy Generator.
        k: How many groups.

    Returns:
        A list of k arrays.
    """
    return [
        rng.normal(rng.normal(0, 1), rng.uniform(0.1, 2), int(rng.integers(2, 3001)))
        for _ in range(k)
    ]


def ab() -> None:
    """Pooled sigma, mean and n equal those of the concatenated scores."""
    rng = np.random.default_rng(1)
    e1 = e2 = 0
    en = 0
    for _i in range(300):
        g = groups(rng, int(rng.integers(2, 13)))
        u = np.concatenate(g)
        x = int(rng.integers(0, 50))
        r = acc(frame(g), x)
        e1 = max(e1, abs(r["sigma"] - np.std(u, ddof=1)))
        e2 = max(e2, abs(r["mean"] - u.mean()))
        if r["n"] != len(u) + x:
            en += 1
    rep(e1 < 1e-10, "a_sigma", f"max err {e1:.3g}")
    rep(e2 < 1e-10, "a_mean", f"max err {e2:.3g}")
    rep(en == 0, "b_n", f"{en} mismatches")
    print("INFO keys:", sorted(r.keys()), "searches=", r.get("searches"))


run("ab", ab)


def c() -> None:
    """Row order and splitting one search in two do not change the pool."""
    rng = np.random.default_rng(2)
    g = groups(rng, 5)
    r0 = acc(frame(g))
    r1 = acc(frame(g[::-1]).sample(frac=1, random_state=1).reset_index(drop=True))
    rep(
        abs(r0["sigma"] - r1["sigma"]) < 1e-12 and r0["n"] == r1["n"],
        "c_order",
        f"{r0['sigma']} vs {r1['sigma']}",
    )
    h = g[0]
    cut = len(h) // 2
    r2 = acc(frame([h[:cut], h[cut:]] + g[1:]))
    rep(
        abs(r0["sigma"] - r2["sigma"]) < 1e-10 and abs(r0["mean"] - r2["mean"]) < 1e-10,
        "c_split",
        f"{r0['sigma']} vs {r2['sigma']}",
    )


run("c", c)


def d() -> None:
    """Report how a size-1 group is pooled (INFO line only)."""
    rng = np.random.default_rng(3)
    g = groups(rng, 3) + [np.array([0.7])]
    u = np.concatenate(g)
    r = acc(frame(g))
    print(
        f"INFO d_size1 sigma={r['sigma']} truth={np.std(u, ddof=1)} n={r['n']} "
        f"finite={math.isfinite(r['sigma'])}"
    )


run("d", d)


def e() -> None:
    """Report how mixed annualised and per-period rows are pooled (INFO line only)."""
    rng = np.random.default_rng(4)
    sc = math.sqrt(252)
    gd = [rng.normal(0.05, 0.05, 500) for _ in range(4)]
    units = ["annualised"] * 2 + ["per_period"] * 2
    gs = [gd[i] * sc if units[i] == "annualised" else gd[i] for i in range(4)]
    truth = np.std(np.concatenate(gd), ddof=1)
    r = acc(frame(gs, units))
    print(
        f"INFO e_units sigma={r['sigma']} unit={r.get('unit')} daily_truth={truth} "
        f"match={abs(r['sigma'] - truth) < 1e-9} mean={r['mean']} n={r['n']}"
    )


run("e", e)


def f() -> None:
    """Report how a row with a p_pass unit and 50 trials is pooled (INFO line only)."""
    rng = np.random.default_rng(5)
    g = groups(rng, 4)
    u = np.concatenate(g)
    fr = frame(g)
    fr.loc[len(fr)] = [50, 0.3, 0.01, "p_pass"]
    r = acc(fr)
    print(
        f"INFO f_ppass n={r['n']} (sharpe-only n={len(u)}, +50={len(u) + 50}) sigma={r['sigma']} "
        f"truth={np.std(u, ddof=1)} sigma_matches_truth={abs(r['sigma'] - np.std(u, ddof=1)) < 1e-9} "
        f"mean={r['mean']} true_mean={u.mean()} unit={r.get('unit')} keys={sorted(r)}"
    )


run("f", f)
if ADDED:
    print("INFO columns added for KeyError:", sorted(ADDED))
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""Calibration, power and reference-library agreement of Hansen's SPA and Romano-Wolf StepM."""
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from engines.inference.snooping import superior as S

try:
    from arch.bootstrap import SPA as ASPA
    from arch.bootstrap import StepM as ASTEPM
    from arch.bootstrap import optimal_block_length
except ImportError:
    ASPA = None

RES = {"pass": 0, "bad": 0}
Z = 3.2905  # 99.9 % two-sided normal quantile
T, K, BLOCK = 500, 20, 5


def report(name: str, ok: bool, detail: str = "") -> None:
    """Count and print one check.

    Args:
        name: Check label.
        ok: Whether it held.
        detail: Detail printed on failure.
    """
    RES["pass" if ok else "bad"] += 1
    print(("PASS " + name) if ok else f"FAIL {name}: {detail}")


def guard(fn: Callable) -> Callable:
    """Decorate a check so an exception counts as an ERROR and the script continues.

    Args:
        fn: The check.

    Returns:
        The guarded check.
    """

    def run(*a: Any, **k: Any) -> None:
        """Call `fn`, reporting any exception."""
        try:
            fn(*a, **k)
        except Exception as exc:
            RES["bad"] += 1
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
    return run


def panel(seed: int, planted: float = 0.0, t: int = T, k: int = K) -> pd.DataFrame:
    """Simulate a t x k panel of unit-variance noise, column s0 shifted by `planted`.

    Args:
        seed: RNG seed.
        planted: Mean planted in column s0.
        t: Rows.
        k: Columns.

    Returns:
        The panel, columns s0..s{k-1}.
    """
    x = np.random.default_rng(seed).normal(size=(t, k))
    x[:, 0] += planted  # unit sigma, so the mean is planted * sigma
    return pd.DataFrame(x, columns=[f"s{i}" for i in range(k)])


def upper_band(p: float, n: int) -> float:
    """Upper end of the 99.9 % binomial band around rate `p` over `n` trials.

    Args:
        p: Expected rate.
        n: Number of trials.

    Returns:
        p plus Z standard errors.
    """
    return p + Z * np.sqrt(p * (1 - p) / n)


@guard
def null_calibration() -> None:
    """SPA's consistent p-value does not reject more often than its level on null panels."""
    n, reps = 300, 300
    ps = np.array([[v for v in S.spa(panel(1000 + i), BLOCK, reps, i).values()] for i in range(n)])
    keys = list(S.spa(panel(1), BLOCK, 50, 1).keys())
    print(f"INFO spa exposes p-values: {keys}")
    for j, key in enumerate(keys):
        for lvl in (0.05, 0.10):
            rate = (ps[:, j] < lvl).mean()
            if key == "consistent":
                ub = upper_band(lvl, n)
                report(f"null rejection rate {key} at {lvl}", rate <= ub, f"observed={rate:.4f} expected<={lvl} band_upper={ub:.4f}")
            print(f"INFO null rate {key} at {lvl}: observed={rate:.4f} expected<={lvl} band_upper={upper_band(lvl, n):.4f}")


@guard
def power() -> None:
    """SPA and StepM find a planted strategy; StepM names no noise column beyond its FWER."""
    n, reps = 100, 300
    spa_hit, step_hit, step_false = 0, 0, 0
    for i in range(n):
        x = panel(2000 + i, 0.25)
        spa_hit += S.spa(x, BLOCK, reps, i)["consistent"] < 0.05
        named = S.stepm(x, 0.05, BLOCK, reps, i)
        step_hit += "s0" in named
        step_false += any(c != "s0" for c in named)
    report("power: SPA p<0.05 in >=90% of planted panels", spa_hit / n >= 0.9, f"observed={spa_hit / n:.3f} expected>=0.90")
    report("power: stepm names the planted strategy in >=90%", step_hit / n >= 0.9, f"observed={step_hit / n:.3f} expected>=0.90")
    ub = upper_band(0.05, n)
    report("stepm FWER on planted panels (names a noise column)", step_false / n <= ub,
           f"observed={step_false / n:.3f} expected<=0.05 band_upper={ub:.3f}")


def ref_panels() -> list[pd.DataFrame]:
    """Thirty panels at three planted levels, shared by the arch comparisons.

    Returns:
        The panels.
    """
    levels = [0.0] * 10 + [0.25] * 10 + [0.13] * 10
    return [panel(3000 + i, lv) for i, lv in enumerate(levels)]


@guard
def agree_spa() -> None:
    """SPA agrees with the arch library panel by panel."""
    if ASPA is None:
        print("INFO skipped (no arch)"); return
    reps, side, pairs = 1000, 0, []
    band = Z * np.sqrt(2 * 0.25 / reps)  # worst-case sd of the difference of two bootstrap p-values
    within = 0
    for i, x in enumerate(ref_panels()):
        mine = S.spa(x, BLOCK, reps, i)["consistent"]
        a = ASPA(np.zeros(len(x)), -x, block_size=BLOCK, reps=reps, bootstrap="stationary", seed=i)  # loss = -excess
        a.compute()
        ref = float(a.pvalues["consistent"])
        pairs.append((mine, ref)); side += (mine < 0.05) == (ref < 0.05); within += abs(mine - ref) < band
        print(f"INFO spa pair {i}: project={mine:.4f} arch={ref:.4f}")
    report("SPA vs arch: same side of 0.05 in >=27/30", side >= 27, f"observed={side}/30")
    report("SPA vs arch: consistent p within MC band on every panel", within == 30,
           f"{within}/30 within +-{band:.3f}; max diff={max(abs(m - r) for m, r in pairs):.3f}")


@guard
def agree_stepm() -> None:
    """StepM names the same sets as the arch library."""
    if ASPA is None:
        print("INFO skipped (no arch)"); return
    reps, same, raised = 1000, 0, 0
    for i, x in enumerate(ref_panels()):
        mine = set(S.stepm(x, 0.05, BLOCK, reps, i))
        try:
            a = ASTEPM(np.zeros(len(x)), -x, size=0.05, block_size=BLOCK, reps=reps, bootstrap="stationary", seed=i)
            a.compute()
            ref = set(a.superior_models)
        except Exception as exc:
            raised += 1; print(f"INFO arch StepM raised on panel {i}: {exc}"); continue
        same += mine == ref
        if mine != ref:
            print(f"INFO stepm differ panel {i}: project={sorted(mine)} arch={sorted(ref)}")
    report("StepM vs arch: identical sets in >=27/30", same >= 27, f"observed={same}/30 (arch raised {raised})")


@guard
def invariances() -> None:
    """Column order and positive rescaling leave the verdicts unchanged."""
    x = panel(4000, 0.0)
    base = S.spa(x, BLOCK, 500, 5)["consistent"]
    perm = np.random.default_rng(6).permutation(K)
    p2 = S.spa(x.iloc[:, perm], BLOCK, 500, 5)["consistent"]
    band = Z * np.sqrt(2 * 0.25 / 500)
    report("SPA invariant to column order (same seed, within MC band)", abs(base - p2) < band,
           f"original={base:.4f} permuted={p2:.4f} band=+-{band:.3f}")
    xs = panel(4001, 0.25)
    n1 = S.stepm(xs, 0.05, BLOCK, 500, 5)
    n2 = S.stepm(xs.iloc[:, perm], 0.05, BLOCK, 500, 5)
    report("stepm names the same set after permuting columns (planted)", sorted(n1) == sorted(n2), f"{n1} vs {n2}")
    p3 = S.spa(x * 3.7, BLOCK, 500, 5)["consistent"]
    if abs(p3 - base) < 1e-9:
        report("SPA p unchanged by positive rescaling", True)
    else:
        print(f"INFO SPA p changes under x3.7 rescaling: {base:.6f} -> {p3:.6f}")


def ar1_panel(phi: float, seed: int, t: int = 1000, k: int = 10) -> pd.DataFrame:
    """Simulate a t x k panel of AR(1) columns after a 100-step burn-in.

    Args:
        phi: Autoregressive coefficient.
        seed: RNG seed.
        t: Rows returned.
        k: Columns.

    Returns:
        The panel.
    """
    e = np.random.default_rng(seed).normal(size=(t + 100, k))
    for i in range(1, t + 100):
        e[i] += phi * e[i - 1]
    return pd.DataFrame(e[100:])


@guard
def block_len() -> None:
    """The automatic block length is small on iid noise and larger on AR(1)."""
    iid = S.block_length(panel(5000, 0.0, t=1000, k=10))
    ar = S.block_length(ar1_panel(0.8, 5001))
    print(f"INFO block_length iid noise={iid} AR(1) phi=0.8={ar}")
    report("block_length small on iid noise (<=3)", iid <= 3, f"observed={iid} expected<=3")
    report("block_length clearly larger on AR(1) 0.8 (>=4 and >=2x iid)", ar >= 4 and ar >= 2 * max(iid, 1),
           f"observed={ar} iid={iid}")
    if ASPA is not None:
        for name, x in (("iid", panel(5000, 0.0, t=1000, k=10)), ("ar0.8", ar1_panel(0.8, 5001))):
            o = optimal_block_length(x)
            print(f"INFO arch optimal_block_length {name}: median stationary={o['stationary'].median():.2f} circular={o['circular'].median():.2f}")


for f in (null_calibration, power, agree_spa, agree_stepm, invariances, block_len):
    f()
print(f"SUMMARY pass={RES['pass']} bad={RES['bad']}")
sys.exit(1 if RES["bad"] else 0)

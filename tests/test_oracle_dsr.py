#!/usr/bin/env python3
"""Checks core.significance and core.surface.plateau
against scipy and the Bailey / Lopez de Prado formulas."""

import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = (
    Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
)
sys.path.insert(0, str(ROOT))

from core import metrics  # noqa: E402
from core import significance as sg  # noqa: E402
from core.surface import plateau as pl  # noqa: E402

BAD: list[str] = []
EULER = 0.5772156649015329


def ok(name: str, cond: bool, detail: str = "") -> None:
    """Print PASS or FAIL for one check and record failures."""
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}: {detail}")
        BAD.append(name)


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    """Relative-or-absolute closeness."""
    return abs(a - b) <= tol * max(1.0, abs(b))


def vf(sr: float, g3: float, g4: float) -> float:
    """Reference variance factor 1 - g3*SR + (g4-1)/4*SR^2."""
    return 1 - g3 * sr + (g4 - 1) / 4 * sr * sr


def ref_emax(sigma: float, n: int) -> float:
    """Reference Bailey-LdP expected maximum of n N(0, sigma^2) draws."""
    if n < 2:
        return 0.0
    return sigma * (
        (1 - EULER) * stats.norm.ppf(1 - 1 / n)
        + EULER * stats.norm.ppf(1 - 1 / (n * np.e))
    )


def t_moments() -> None:
    """Sharpe, skew, raw kurtosis against scipy."""
    x = np.random.default_rng(1).standard_t(5, 500) * 0.01 + 0.002
    sh, sk, ku = sg.moments(x)
    ok("moments.sharpe", close(sh, x.mean() / x.std(ddof=1)), f"{sh}")
    ok("moments.skew", close(sk, stats.skew(x)), f"{sk} vs {stats.skew(x)}")
    ok(
        "moments.kurt_raw",
        close(ku, stats.kurtosis(x, fisher=False)),
        f"{ku} vs {stats.kurtosis(x, fisher=False)}",
    )
    z = np.random.default_rng(2).normal(size=400000)
    _, sk, ku = sg.moments(z)
    ok("moments.normal", abs(sk) < 0.02 and abs(ku - 3) < 0.05, f"skew {sk} kurt {ku}")


def t_psr() -> None:
    """PSR and variance_factor against the closed formula, then calibration."""
    x = np.random.default_rng(3).standard_t(6, 300) * 0.01 + 0.0015
    sh, sk, ku = sg.moments(x)
    ok(
        "variance_factor",
        close(sg.variance_factor(sh, sk, ku), vf(sh, sk, ku)),
        "formula",
    )
    ok(
        "variance_factor.normal0",
        close(sg.variance_factor(0.0, 0.0, 3.0), 1.0),
        "SR=0 normal -> 1",
    )
    for b in (0.0, 0.05):
        r = sg.psr(x, b)
        e = stats.norm.cdf((sh - b) * np.sqrt(len(x) - 1) / np.sqrt(vf(sh, sk, ku)))
        ok(f"psr.formula b={b}", close(r["psr"], e), f"{r['psr']} vs {e}")
    ok("psr.n", sg.psr(x, 0.0)["n"] == len(x), "n field")
    rng = np.random.default_rng(4)
    reps, t = 3000, 500
    m = rng.normal(size=(reps, t))
    s = m.mean(1) / m.std(1, ddof=1)
    sk = stats.skew(m, axis=1)
    ku = stats.kurtosis(m, axis=1, fisher=False)
    p = stats.norm.cdf(s * np.sqrt(t - 1) / np.sqrt(vf(s, sk, ku)))
    lib = np.array([sg.psr(m[i], 0.0)["psr"] for i in range(300)])
    ok(
        "psr.vs_vectorised",
        np.allclose(lib, p[:300], atol=1e-9),
        "library vs own vector",
    )
    obs, band = float((p > 0.95).mean()), 3.29 * np.sqrt(0.05 * 0.95 / reps)
    print(f"INFO psr.calibration obs={obs:.4f} exp=0.05 band={band:.4f}")
    ok("psr.calibration", abs(obs - 0.05) <= band, f"{obs} vs 0.05 +-{band}")


def t_mintrl() -> None:
    """Minimum track record against the closed formula."""
    x = np.random.default_rng(5).normal(0.3, 1, 150)
    sh, sk, ku = sg.moments(x)
    for b, a in ((0.0, 0.05), (0.05, 0.05), (0.0, 0.01)):
        r = sg.min_track_record(x, alpha=a, benchmark=b)
        e = 1 + vf(sh, sk, ku) * (stats.norm.ppf(1 - a) / (sh - b)) ** 2
        ok(f"mintrl b={b} a={a}", close(r["needed"], e), f"{r['needed']} vs {e}")
    r = sg.min_track_record(x, benchmark=sh + 0.1)
    ok("mintrl.unreachable", r["needed"] is None, f"{r}")
    r = sg.min_track_record(x)
    ok("mintrl.enough", r["enough"] == (r["have"] >= r["needed"]), f"{r}")


def t_expmax() -> None:
    """expected_max and expected_max_sharpe: formula, Monte Carlo, N=1."""
    ok(
        "expected_max.formula",
        close(pl.expected_max(0.3, 50), 0.3 * np.sqrt(2 * np.log(50))),
        "sqrt(2 ln N)",
    )
    ok("expected_max.n1", pl.expected_max(1.0, 1) == 0.0, f"{pl.expected_max(1.0, 1)}")
    ok(
        "emax_sharpe.n1",
        pl.expected_max_sharpe(1.0, 1) == 0.0,
        f"{pl.expected_max_sharpe(1.0, 1)}",
    )
    rng = np.random.default_rng(6)
    for n, reps in ((10, 20000), (100, 10000), (1000, 2000)):
        lib = pl.expected_max_sharpe(0.7, n)
        ok(
            f"emax_sharpe.formula N={n}",
            close(lib, ref_emax(0.7, n), 1e-6),
            f"{lib} vs {ref_emax(0.7, n)}",
        )
        mc = float((rng.normal(0, 0.7, size=(reps, n)).max(1)).mean())
        gap = lib / mc - 1
        print(f"INFO emax_sharpe N={n} lib={lib:.4f} mc={mc:.4f} gap={gap:+.3%}")
        ok(f"emax_sharpe.mc N={n}", abs(gap) < 0.05, f"gap {gap:+.3%}")
        ok(
            f"expected_max.bound N={n}",
            pl.expected_max(0.7, n) >= lib,
            "sqrt bound above sharper",
        )


def t_dsr() -> None:
    """deflated_sharpe equals PSR at the benchmark, monotone, and calibrated on noise."""
    sr, sig, n, t, sk, ku = 0.35, 0.08, 200, 400, -0.3, 4.5
    r = pl.deflated_sharpe(sr, sig, n, t, sk, ku)
    b = ref_emax(sig, n)
    e = stats.norm.cdf((sr - b) * np.sqrt(t - 1) / np.sqrt(vf(sr, sk, ku)))
    ok("dsr.benchmark", close(r["benchmark"], b, 1e-6), f"{r['benchmark']} vs {b}")
    ok("dsr.value", close(r["dsr"], e, 1e-6), f"{r['dsr']} vs {e}")
    d = [
        pl.deflated_sharpe(sr, sig, k, t, sk, ku)["dsr"]
        for k in (2, 10, 100, 1000, 10000)
    ]
    ok("dsr.falls_with_n_eff", all(a > c for a, c in zip(d, d[1:])), f"{d}")
    d = [pl.deflated_sharpe(sr, sig, n, k, sk, ku)["dsr"] for k in (50, 100, 400, 1600)]
    ok("dsr.rises_with_n_obs", all(a < c for a, c in zip(d, d[1:])), f"{d}")
    rng = np.random.default_rng(7)
    reps, big_n, t = 400, 100, 250
    hit = 0
    for _ in range(reps):
        m = rng.normal(size=(big_n, t))
        s = m.mean(1) / m.std(1, ddof=1)
        i = int(s.argmax())
        _, sk, ku = sg.moments(m[i])
        hit += pl.deflated_sharpe(s[i], s.std(ddof=1), big_n, t, sk, ku)["dsr"] > 0.95
    obs, band = hit / reps, 3.29 * np.sqrt(0.05 * 0.95 / reps)
    print(f"INFO dsr.calibration obs={obs:.4f} exp<=0.05 band={band:.4f}")
    ok("dsr.calibration", obs <= 0.05 + band, f"{obs} > 0.05+{band}")


def t_plateau() -> None:
    """Hand-computed answers for the grid helpers and annual_sharpe."""
    v = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
    ok("above_half_max", close(pl.above_half_max(v), 0.2), f"{pl.above_half_max(v)}")
    ok(
        "plateau_area",
        close(pl.plateau_area(np.array([-1, 0.5, 2, 3.0])), 0.75),
        "area",
    )
    ok(
        "plateau_area.pf",
        close(pl.plateau_area(np.array([0.5, 1.5, 2.0, 0.9]), 1.0), 0.5),
        "breakeven 1",
    )
    ok(
        "plateau_fraction",
        close(pl.plateau_fraction(v, 4.0), 0.4),
        f"{pl.plateau_fraction(v, 4.0)}",
    )
    neg = np.array([-20, -11, -10, -5, 0.0])
    ok(
        "plateau_fraction.neg",
        close(pl.plateau_fraction(neg, -10.0), 0.8),
        f"{pl.plateau_fraction(neg, -10.0)}",
    )
    ok("rank_of", close(pl.rank_of(v, 3.5), 0.6), f"{pl.rank_of(v, 3.5)}")
    ok("rank_of.top", close(pl.rank_of(v, 11.0), 1.0), "beats all")
    ok("shrunk", close(pl.shrunk(v), 3.0), f"{pl.shrunk(v)}")
    closed = np.array(
        ["2024-01-01", "2024-01-03", "2024-01-06"], dtype="datetime64[ns]"
    )
    d = np.array([1, 0, 3, 0, 0, 2.0])
    e = d.mean() / d.std(ddof=1) * np.sqrt(252)
    got = metrics.sharpe(metrics.weekday_pnl(np.array([1.0, 3.0, 2.0]), closed), 252)
    ok("annual_sharpe", close(got, e), f"{got} vs {e}")
    ok(
        "annual_sharpe.nan",
        np.isnan(metrics.sharpe(metrics.weekday_pnl(np.array([1.0]), closed[:1]), 252)),
        "one day -> NaN",
    )


def main() -> None:
    """Run every check; exit 1 on any FAIL or ERROR."""
    for fn in (t_moments, t_psr, t_mintrl, t_expmax, t_dsr, t_plateau):
        fn()
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()

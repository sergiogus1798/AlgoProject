#!/usr/bin/env python3
"""Checks engines.inference.excess against the definitions of Storey's pi0 and the Benjamini-Hochberg bar."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engines.inference import excess as ex  # noqa: E402

BAD: list[str] = []


def ok(name: str, cond: bool, detail: str = "") -> None:
    """Print PASS or FAIL for one check and record failures."""
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}: {detail}")
        BAD.append(name)


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    """Absolute closeness."""
    return abs(a - b) <= tol


def t_excess() -> None:
    """Counts, expectation under the global null, excess and fdr."""
    p = np.array([0.01, 0.02, 0.05, 0.051, 0.2, 0.4, 0.6, 0.8, 0.9, 0.99])
    r = ex.excess(p, 0.05)
    ok("excess.observed_boundary", r["observed"] == 3, f"observed {r['observed']} (p == alpha should pass)")
    ok("excess.expected_all_null", close(r["expected_all_null"], 0.5), f"{r['expected_all_null']}")
    ok("excess.excess", close(r["excess"], 3 - 0.5), f"{r['excess']}")
    ok("excess.n", r["n"] == 10, f"{r['n']}")
    got = r["fdr"]
    cands = {"all_null": 0.5 / 3, "storey": r["expected"] / 3}
    hit = [k for k, v in cands.items() if close(got, min(1.0, v))]
    ok("excess.fdr", bool(hit), f"{got} vs {cands}")
    print(
        f"INFO excess.fdr_reading: fdr equals expected/observed using the {hit} count (docstring ambiguous)"
    )
    ok("excess.expected_storey", close(r["expected"], r["share_null"] * 0.05 * 10), "share_null*alpha*n")
    r = ex.excess(np.array([0.5, 0.6, 0.7, 0.9]), 0.05)
    ok("excess.none_pass", r["observed"] == 0 and r["fdr"] == 0.0 or r["fdr"] != r["fdr"], f"{r}")
    print(f"INFO excess.zero_observed: fdr={r['fdr']} when nothing passes")
    r = ex.excess(np.full(100, 0.04), 0.05)
    ok("excess.fdr_cap", close(r["fdr"], min(1.0, 5 / 100)), f"{r['fdr']}")
    r = ex.excess(np.array([0.04, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]), 0.5)
    ok("excess.fdr_capped_at_1", r["fdr"] <= 1.0, f"{r['fdr']}")
    print(
        f"INFO excess.fdr_cap_case: observed={r['observed']} expected_all_null={r['expected_all_null']} "
        f"fdr={r['fdr']}"
    )


def t_share_null() -> None:
    """Storey's pi0 at lambda = cut: hand case, uniform, mixture, cap."""
    p = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.01, 0.02, 0.03])
    ok("share_null.hand", close(ex.share_null(p), 3 / (0.5 * 10)), f"{ex.share_null(p)}")
    ok("share_null.hand_cut", close(ex.share_null(p, 0.2), 5 / (0.8 * 10)), f"{ex.share_null(p, 0.2)}")
    ok("share_null.cap", close(ex.share_null(np.array([0.6] * 6 + [0.1] * 4)), 1.0), "6/(0.5*10)=1.2 -> 1")
    ok("share_null.zero", close(ex.share_null(np.full(50, 0.01)), 0.0), "no large p -> 0")
    ok(
        "share_null.boundary",
        close(ex.share_null(np.array([0.5, 0.5, 0.1, 0.2])), 0.0),
        f"p == cut is not above it: {ex.share_null(np.array([0.5, 0.5, 0.1, 0.2]))}",
    )
    rng = np.random.default_rng(11)
    n = 20000
    got = ex.share_null(rng.uniform(size=n))
    band = 3.29 / np.sqrt(n)
    print(f"INFO share_null.uniform obs={got:.4f} exp=1.0 band(one-sided)={band:.4f}")
    ok("share_null.uniform", got >= 1 - band, f"{got}")
    m = int(0.7 * n)
    p = np.concatenate([rng.uniform(size=m), rng.uniform(0, 0.01, n - m)])
    got = ex.share_null(p)
    band = 3.29 * np.sqrt(m * 0.25) / (0.5 * n)
    print(f"INFO share_null.mixture obs={got:.4f} exp=0.7 band={band:.4f}")
    ok("share_null.mixture", abs(got - 0.7) <= band, f"{got} vs 0.7 +-{band}")


def t_resolution() -> None:
    """Floor, BH bar, reachability, draws_needed and saturation."""
    n, alpha = 10, 0.05
    for draws in (99, 198, 199, 1000):
        p = np.full(n, 0.5)
        r = ex.resolution(p, alpha, draws)
        ok(f"resolution.floor d={draws}", close(r["floor"], 1 / (draws + 1)), f"{r['floor']}")
        ok(f"resolution.bar d={draws}", close(r["bar"], alpha / n), f"{r['bar']}")
        want = 1 / (draws + 1) <= alpha / n
        ok(f"resolution.reachable d={draws}", r["reachable"] == want, f"{r['reachable']} vs {want}")
    r = ex.resolution(np.full(n, 0.5), alpha, 50)
    ok("resolution.draws_needed", r["draws_needed"] == 199, f"{r['draws_needed']} vs 199")
    r2 = ex.resolution(np.full(n, 0.5), alpha, r["draws_needed"])
    r1 = ex.resolution(np.full(n, 0.5), alpha, r["draws_needed"] - 1)
    ok(
        "resolution.draws_needed_pm1",
        r2["reachable"] and not r1["reachable"],
        f"{r2['reachable']} {r1['reachable']}",
    )
    r = ex.resolution(np.full(n, 0.5), alpha, 1000)
    print(f"INFO resolution.draws_needed_when_already_reachable: {r['draws_needed']} (draws=1000)")
    d = 99
    fl = 1 / (d + 1)
    p = np.array([fl, fl, fl, 2 * fl, 0.3, 0.9])
    ok("resolution.saturated", ex.resolution(p, 0.05, d)["saturated"] == 3, f"{ex.resolution(p, 0.05, d)}")
    ok("resolution.saturated0", ex.resolution(p[3:], 0.05, d)["saturated"] == 0, "none at floor")
    r = ex.resolution(np.full(7, 0.5), 0.1, 30)
    ok("resolution.draws_needed_n7", r["draws_needed"] == 69, f"{r['draws_needed']} vs 69 (7/0.1 - 1)")


def main() -> None:
    """Run every check; exit 1 on any FAIL or ERROR."""
    for fn in (t_excess, t_share_null, t_resolution):
        fn()
    sys.exit(1 if BAD else 0)


if __name__ == "__main__":
    main()

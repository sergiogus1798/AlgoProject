#!/usr/bin/env python3
"""Known-answer test of the weight methods (M4 and M8, PLAN §8.6): every registry entry, equal = 1/K, the rest by hand."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import portfolio.common.construct.search.objective as objective
import portfolio.common.construct.weights as weights
from portfolio_planted import CALENDAR, NAMES, planted_cfg, planted_pool

FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def known_answers() -> None:
    """M8's methods on three exactly uncorrelated members of daily volatility 1, 2 and 4."""
    import pandas as pd
    from portfolio.common.construct.weights import hrp, min_variance, risk_parity
    noise = np.random.default_rng(0).normal(size=(500, 3))
    basis = np.linalg.qr(np.column_stack([np.ones(500), noise]))[0][:, 1:]             # zero mean, orthonormal
    frame = pd.DataFrame(basis / basis.std(axis=0, ddof=1) * [1.0, 2.0, 4.0], columns=["s1", "s2", "s4"])
    got = risk_parity.weights(frame, {})
    check("risk parity = 1/sigma: 4/7, 2/7, 1/7", np.allclose(list(got.values()), [4 / 7, 2 / 7, 1 / 7]))
    check("minimum variance on a known diagonal covariance = 1/variance: 0.8, 0.2",
          np.allclose(min_variance.solve(np.diag([1.0, 4.0])), [0.8, 0.2], atol=1e-6))
    cov, intensity = min_variance.shrunk(frame[["s1", "s2"]].to_numpy())
    quiet = min_variance.weights(frame[["s1", "s2"]], {})["s1"]
    check("Ledoit-Wolf: intensity inside (0, 1), no correlation invented, the quiet member between 1/2 and 0.8",
          0 < intensity < 1 and abs(cov[0, 1]) < 1e-12 and 0.5 < quiet < 0.8)
    check("minimum variance of two members of equal volatility = 1/2 each",
          np.allclose(list(min_variance.weights(frame[["s1", "s2"]] / [1.0, 2.0], {}).values()), 0.5, atol=1e-6))
    check("HRP of two uncorrelated members = 1/variance: 0.8, 0.2",
          np.allclose(list(hrp.weights(frame[["s1", "s2"]], {}).values()), [0.8, 0.2]))
    clones = frame.assign(s1b=frame["s1"] + 0.05 * frame["s2"])
    straight, shuffled = hrp.weights(clones, {}), hrp.weights(clones[["s4", "s1b", "s2", "s1"]], {})
    check("HRP: each weight lands on its own member whatever the column order (AlphaForge's bug)",
          all(np.isclose(straight[c], shuffled[c]) for c in clones) and straight["s4"] == min(straight.values()))
    for name, method in (("risk_parity", risk_parity), ("hrp", hrp)):
        try:
            method.weights(frame.assign(flat=0.0), {})
            check(f"{name}: a member that never moves is refused, nothing substituted", False)
        except ValueError:
            check(f"{name}: a member that never moves is refused, nothing substituted", True)


def main() -> None:
    """Every method on the planted pool's build days; the search's paths are the weighted members."""
    cfg = planted_cfg()
    build = planted_pool().loc[:CALENDAR["build"][1]]
    for name, method in weights.REGISTRY.items():
        for k in (1, 3, len(NAMES)):
            got = method(build.iloc[:, :k], {**cfg, "weights": {"method": name}})
            values = np.array(list(got.values()))
            check(f"{name}, K={k}: one weight per identity given, none negative, summing to 1",
                  list(got) == NAMES[:k] and (values >= 0).all() and np.isclose(values.sum(), 1.0))
    check("equal returns exactly 1/K", weights.equal.weights(build.iloc[:, :4], cfg) == dict.fromkeys(NAMES[:4], 0.25))
    check("the committed method is equal (owner, 2026-09-29)", cfg["weights"]["method"] == "equal")

    known_answers()

    members = np.zeros((3, len(NAMES)), dtype=bool)
    members[0, [0, 1]] = members[1, 4] = members[2, [2, 5, 7, 9]] = True
    share = weights.matrix(build, members, cfg)
    check("matrix: each combination's row is 1/K on its members and 0 elsewhere",
          np.array_equal(share, members / members.sum(axis=1, keepdims=True)))
    unit = build.to_numpy().T
    table = objective.measure(unit, build.index, members, cfg)[0]
    pair = unit[[0, 1]].mean(axis=0)
    check("the search measures the weighted path: {A, B}'s Sharpe is the Sharpe of their mean",
          np.isclose(table["sharpe"][0], pair.mean() / pair.std(ddof=1)))
    source = "".join(p.read_text(encoding="utf-8") for p in Path(weights.__file__).parent.glob("*.py"))
    check("weights/ imports nothing else of the engine (PLAN §3)",
          "portfolio.common" not in source and "from .." not in source)
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()

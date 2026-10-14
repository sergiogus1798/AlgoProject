#!/usr/bin/env python3
"""Our PSR, minimum track record, expected maximum, deflated Sharpe and trial count against
tschm/jsharpe's stored outputs: the arithmetic agrees, the conventions do not, and both are pinned."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.significance import min_track_record, moments, psr
from core.surface import plateau, trials

REFERENCE = Path(__file__).resolve().parent / "fixtures" / "jsharpe" / "reference.json"

SHAPES = ("normal", "left_skew", "right_skew", "fat_tails")
LENGTHS = (60, 250, 1000)
SHARPES = (0.05, 0.15)  # per observation, never annualised
BENCHMARKS = (0.0, 0.03)
TRIALS = (10, 100, 1000)
SIGMA_SR = 0.05  # spread of the trial Sharpes, same unit as SHARPES
ALPHA = 0.05
K_MAX = 40  # studies/optimisation/cscv/config.yaml's cluster_k_max
PANELS = {
    "two_blocks": (20, 20),
    "four_blocks": (10, 10, 10, 10),
    "eight_blocks": (5,) * 8,
    "one_dominant": (30, 5, 5),
    "one_blob": (40,),
}
WEEKS, RHO, SEED = 300, 0.8, 42
EXACT = 1e-9


def series(shape: str, n: int, sharpe: float) -> np.ndarray:
    """A deterministic return series of a given shape whose Sharpe is exact.

    Args:
        shape: One of SHAPES.
        n: Observations.
        sharpe: Per-observation Sharpe the series must have, ddof=1.

    Returns:
        The distribution's own quantiles at n evenly spaced probabilities, rescaled. No random
        draw: the fixture's numbers must not depend on a generator's stream.
    """
    p = (np.arange(n) + 0.5) / n
    x = {
        "normal": stats.norm.ppf(p),
        "left_skew": -stats.lognorm(0.5).ppf(p),
        "right_skew": stats.lognorm(0.5).ppf(p),
        "fat_tails": stats.t(4).ppf(p),
    }[shape]
    return (x - x.mean()) / x.std(ddof=1) + sharpe


def panel(name: str) -> pd.DataFrame:
    """Weekly returns of 40 variants in blocks that earn together.

    Args:
        name: Key of PANELS; its tuple is the size of each block.

    Returns:
        WEEKS rows by 40 columns. Inside a block every pair correlates RHO; across blocks, zero.
    """
    rng = np.random.default_rng(SEED)
    columns = [
        np.sqrt(RHO) * factor[:, None]
        + np.sqrt(1 - RHO) * rng.standard_normal((WEEKS, size))
        for size in PANELS[name]
        for factor in [rng.standard_normal(WEEKS)]
    ]
    return pd.DataFrame(np.hstack(columns))


def worst(pairs: list[tuple[str, float, float]]) -> tuple[str, float, float]:
    """The pair that differs most.

    Args:
        pairs: (label, ours, jsharpe's).

    Returns:
        The one with the largest absolute gap.
    """
    return max(pairs, key=lambda p: abs(p[1] - p[2]))


def compare(cases: list[dict]) -> dict[str, dict[str, list]]:
    """Every quantity of every case, ours next to jsharpe's.

    Args:
        cases: The fixture's `cases`.

    Returns:
        Quantity -> {"aligned": pairs against jsharpe fed our convention, "default": pairs against
        jsharpe called as its README does}. `moments` and `expected_max` have one convention.
    """
    out = {
        q: {"aligned": [], "default": []}
        for q in ("moments", "psr", "mintrl", "expected_max", "dsr")
    }
    for case in cases:
        r = series(case["shape"], case["n"], round(case["sharpe"], 2))
        label = f"{case['shape']} n={case['n']} SR={case['sharpe']:.2f}"
        for ours, key in zip(moments(r), ("sharpe", "skew", "kurtosis")):
            out["moments"]["aligned"].append((f"{label} {key}", ours, case[key]))
        for bench, ref in case["benchmarks"].items():
            got = psr(r, float(bench))["psr"]
            out["psr"]["aligned"].append(
                (f"{label} SR0={bench}", got, ref["psr_aligned"])
            )
            out["psr"]["default"].append((f"{label} SR0={bench}", got, ref["psr"]))
            needed = min_track_record(r, ALPHA, float(bench))["needed"]
            out["mintrl"]["aligned"].append(
                (f"{label} SR0={bench}", needed, ref["mintrl_aligned"])
            )
            out["mintrl"]["default"].append(
                (f"{label} SR0={bench}", needed, ref["mintrl"])
            )
        sharpe, skew, kurtosis = moments(r)
        for k, ref in case["trials"].items():
            got = plateau.deflated_sharpe(
                sharpe, SIGMA_SR, int(k), r.size, skew, kurtosis
            )
            out["expected_max"]["aligned"].append(
                (f"K={k}", got["benchmark"], ref["expected_max"])
            )
            out["dsr"]["aligned"].append(
                (f"{label} K={k}", got["dsr"], ref["dsr_aligned"])
            )
            out["dsr"]["default"].append((f"{label} K={k}", got["dsr"], ref["dsr"]))
    return out


# jsharpe called as its README calls it differs from us in three quantities. Each is a convention,
# not arithmetic. Ours is Bailey & Lopez de Prado 2012/2014: the Sharpe's variance at the OBSERVED
# Sharpe, over n-1, and 1 + ... in the track record. jsharpe's is Lopez de Prado, Lipton &
# Zoonekynd 2025: the variance UNDER THE NULL (at SR0, so at SR0=0 skew and kurtosis drop out),
# over T, no +1. The pair below is the grid's widest gap (ours, jsharpe's); a change on either
# side moves it and fails this test, which is the point: re-read both before re-pinning.
DOCUMENTED = {
    "psr": ("left_skew n=60 SR=0.15 SR0=0.0", 0.850964, 0.877361),
    "mintrl": ("left_skew n=1000 SR=0.05 SR0=0.03", 7355.989556, 7111.739619),
    "dsr": ("right_skew n=60 SR=0.05 K=1000", 0.185235, 0.165677),
}


def conventions(table: dict[str, dict[str, list]]) -> list[str]:
    """Check the arithmetic against jsharpe, and the documented gaps against their pinned pair.

    Args:
        table: What `compare` returned.

    Returns:
        One line per failure.
    """
    failures = []
    for quantity, pairs in table.items():
        label, ours, theirs = worst(pairs["aligned"])
        if abs(ours - theirs) > EXACT * max(1.0, abs(theirs)):
            failures.append(
                f"{quantity}: la aritmética ya no coincide con jsharpe — {label}: "
                f"nuestro {ours!r}, jsharpe {theirs!r}"
            )
        if quantity in DOCUMENTED:
            label, ours, theirs = worst(pairs["default"])
            print(
                f"DISCREPANCIA DOCUMENTADA {quantity} (convención, no aritmética): {label}: "
                f"nuestro {ours:.6f}, jsharpe {theirs:.6f}, diferencia {ours - theirs:+.6f}"
            )
            where, want_ours, want_theirs = DOCUMENTED[quantity]
            if (
                label != where
                or abs(ours - want_ours) > 1e-6
                or abs(theirs - want_theirs) > 1e-6
            ):
                failures.append(
                    f"{quantity}: la discrepancia documentada con jsharpe cambió — era "
                    f"{where}: {want_ours} contra {want_theirs}; ahora {label}: "
                    f"{ours!r} contra {theirs!r}"
                )
    return failures


def unreachable(theirs: float) -> list[str]:
    """A Sharpe below its benchmark: we answer None, jsharpe a finite length.

    Args:
        theirs: jsharpe's minimum track record for SR 0.05 against SR0 0.08.

    Returns:
        One line if `min_track_record` stopped answering None there.
    """
    got = min_track_record(series("normal", 250, 0.05), ALPHA, 0.08)["needed"]
    print(
        f"DISCREPANCIA DOCUMENTADA mintrl inalcanzable: SR=0.05 < SR0=0.08: nuestro {got}, "
        f"jsharpe {theirs:.1f} (eleva al cuadrado la diferencia negativa)"
    )
    return [] if got is None else [f"mintrl: SR<SR0 debía dar None y dio {got!r}"]


# The trial count on panels whose block count is known: name -> (the truth, ours, jsharpe's over
# eight seeds of its k-means). Ours is deterministic; where it misses the truth the miss is pinned.
#   one_dominant: the true split puts 30 of 40 in one cluster, which `independent` refuses (no
#     cluster above half), so it cuts the dominant family until the rule holds: 14, not 3.
#   one_blob: nothing to find; both invent a count (ours 16 at silhouette 0.014, jsharpe 39).
CLUSTERS = {
    "two_blocks": (2, 2, [2] * 8),
    "four_blocks": (4, 4, [4] * 8),
    "eight_blocks": (8, 8, [4, 8, 8, 2, 8, 4, 8, 4]),
    "one_dominant": (3, 14, [3] * 8),
    "one_blob": (1, 16, [39] * 8),
}


def clusters(reference: dict[str, dict]) -> list[str]:
    """The number of independent trials, ours against jsharpe's and against the truth.

    Args:
        reference: The fixture's `clusters`.

    Returns:
        One line per failure.
    """
    failures = []
    for name, (truth, want, theirs) in CLUSTERS.items():
        window = panel(name)
        if abs(window.to_numpy().sum() - reference[name]["checksum"]) > 1e-6:
            failures.append(
                f"clusters {name}: el panel sintético ya no es el de la referencia"
            )
            continue
        got = trials.independent(window, K_MAX)
        stored = reference[name]["number_of_clusters_by_seed"]
        mark = (
            "igual"
            if got["n_clusters"] == truth == min(stored) == max(stored)
            else "DISCREPANCIA DOCUMENTADA"
        )
        print(
            f"clusters {name}: verdad {truth}, nuestro {got['n_clusters']} (silueta "
            f"{got['silhouette']}), jsharpe por semilla {stored}, rango efectivo "
            f"{reference[name]['effective_rank']:.1f} — {mark}"
        )
        if (got["n_clusters"], stored) != (want, theirs):
            failures.append(
                f"clusters {name}: se esperaba nuestro {want} y jsharpe {theirs}, "
                f"salió nuestro {got['n_clusters']} y jsharpe {stored}"
            )
    return failures


def k_max_too_small() -> list[str]:
    """`independent` with no admissible split below k_max: today it raises a clear ValueError instead of answering.

    Returns:
        One line if that stopped being so — the pinned behaviour is a finding, not a contract.
    """
    try:
        got = trials.independent(panel("one_blob"), 10)
    except ValueError as error:
        print(
            f"DISCREPANCIA DOCUMENTADA clusters one_blob con k_max=10: nuestro ValueError "
            f"({error}), jsharpe 2 — ningún corte hasta 10 deja todo grupo en la mitad o menos"
        )
        if "leaves every cluster at half or less" not in str(error):
            return [
                f"clusters: el ValueError con k_max=10 ya no es el mensaje claro: {error}"
            ]
        return []
    return [
        f"clusters: con k_max=10 `independent` ya no falla y da {got}; quita este caso"
    ]


def main() -> None:
    """Run every comparison and exit non-zero on any failure."""
    reference = json.loads(REFERENCE.read_text())
    failures = (
        conventions(compare(reference["cases"]))
        + unreachable(reference["unreachable_mintrl"])
        + clusters(reference["clusters"])
        + k_max_too_small()
    )
    for line in failures:
        print("FALLO", line)
    print(
        f"jsharpe {reference['commit'][:10]}: {len(reference['cases'])} series, "
        f"{len(failures)} fallos"
    )
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

"""The board's numbers per cell — prior, evidence, signal, coverage gap, past, brake — each 0-1."""

from scipy.stats import beta


def signal(multiple: float, cap: float) -> float:
    """The profile's effect in cost multiples, saturating at `cap`."""
    return min(multiple / cap, 1.0)


def gap(attempts: int) -> float:
    """1 where the family was never run in the cell, halving with the first attempt."""
    return 1.0 / (1 + attempts)


def brake(ideas: int, half: float) -> float:
    """What multiplies the points: 1 with no idea spent, 0.5 at `half` ideas."""
    return 1.0 / (1 + ideas / half)


def past(by_family: list[dict], family: str, asset_class: str, strength: float,
         interval: float) -> dict:
    """Survival rate of a family in an asset class, shrunk towards the pooled rate.

    A Beta posterior whose prior is `strength` pseudo-attempts at the rate pooled over every
    family and class: few closed runs barely move it, and a family never tried sits exactly on
    the pooled rate — unknown, not penalised. With nothing closed anywhere every cell reads 0.5.

    Args:
        by_family: `queries.survivors_by_family` rows.
        family, asset_class: The cell's.
        strength: Prior pseudo-attempts.
        interval: Mass of the credible interval, e.g. 0.90.

    Returns:
        `closed`, `with_survivors`, `rate` (posterior mean), `low`, `high`, `pooled`.
    """
    closed = sum(r["closed"] for r in by_family)
    pooled = (sum(r["with_survivors"] for r in by_family) + 1) / (closed + 2)
    mine = next((r for r in by_family
                 if (r["family"], r["asset_class"]) == (family, asset_class)),
                {"closed": 0, "with_survivors": 0})
    a = pooled * strength + mine["with_survivors"]
    b = (1 - pooled) * strength + mine["closed"] - mine["with_survivors"]
    tail = (1 - interval) / 2
    return {"closed": mine["closed"], "with_survivors": mine["with_survivors"],
            "rate": a / (a + b), "low": float(beta.ppf(tail, a, b)),
            "high": float(beta.ppf(1 - tail, a, b)), "pooled": pooled}


def evidence(row: dict, swept: dict | None) -> str:
    """The measured evidence of a cell-family, as a key of the config's `evidence.values`.

    Args:
        row: Its row of the profile's `scores.csv`.
        swept: Its row of the sweep's `best.csv`, or None when the sweep has no entry for it.
    """
    if row["passes"]:
        return "naked"
    if swept and swept["plateau_any"]:
        return "plateau"
    lost = row["significant"] and row["multiple"] < 0.5
    turned = row["p_raw"] >= 0.95 and row["multiple"] <= -1.0
    if lost or turned or (swept is not None and swept["max_multiple"] < 0.5):
        return "against"
    return "weak" if row["significant"] and row["stable"] else "none"


def points(parts: dict, weights: dict) -> float:
    """0-100: the weighted mean of the factors named in `weights`, times the brakes."""
    total = sum(weights.values())
    return (100 * parts["brake"] * parts.get("against", 1.0)
            * sum(weights[k] * parts[k] for k in weights) / total)

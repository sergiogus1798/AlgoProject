"""How good a strategy is once nothing has vetoed it: four sub-scores, then one composite."""

from studies.breakage.mcRetest.inputs import tasks
from studies.breakage.mcRetest.verdict import gates

VERDICTS = ("STRONG", "ACCEPTABLE", "MARGINAL", "FAIL", "INCONCLUSIVE")

# What each sub-score is built from. Printed beside the number, because a score whose
# ingredients are not visible is a number nobody can argue with.
BUILT_FROM = {
    "production": "el percentil 5 de beneficio bajo estrés combinado, su drawdown condicional "
                  "y la proporción de re-ejecuciones que mantuvieron el Sharpe positivo",
    "execution": "la peor de las tres pruebas de ejecución: spread, slippage y distancia mínima",
    "specification": "la peor de las dos de especificación: parámetros y salidas",
    "data": "la perturbación del histórico de precios"}


def curve(value: float, bad: float, good: float) -> float:
    """A straight-line 0-100 mapping between the value that fails and the value that is fine.

    Args:
        value: What was measured.
        bad: The value scoring 0. May be above or below `good`.
        good: The value scoring 100.

    Returns:
        A score, clipped at both ends. Straight-line and stated rather than a curve chosen
        to make the numbers look right: the thresholds are the judgement, and they all live
        in gates.py and the config.
    """
    if value != value:
        return 0.0
    return float(min(100.0, max(0.0, 100.0 * (value - bad) / (good - bad))))


def _kept(result: dict, role: str) -> float:
    """The worst share of the original net profit any task of one role left standing.

    Args:
        result: One strategy's per-task results, keyed by task.
        role: "execution", "specification" or "data".

    Returns:
        The minimum over that role's tasks, or 1.0 when none of them perturbed anything.
        The filter is `perturbed`, not `discriminated`: a grid-sampled task like spread
        produces only 69 distinct outcomes, so no shape test may run on it, but its 5th
        percentile is perfectly meaningful and the gate reads it. Filtering on the stricter
        one here made the execution subscore 100 while the execution gate was vetoing.
    """
    shares = [result[key]["fragility"]["net_p5"]["point"] / result[key]["original_net"]
              for key in result
              if key in tasks.ROLE and tasks.ROLE[key] == role
              and result[key]["original_net"] and result[key]["modes"]["perturbed"]]
    return min(shares) if shares else 1.0


def subscores(result: dict, cfg: dict) -> dict[str, float]:
    """One score per role, on what that role exists to measure.

    Args:
        result: One strategy's per-task results, keyed by task.
        cfg: What inputs.config.load() returned.

    Returns:
        {"production", "execution", "specification", "data": 0-100}. Roles with more than
        one task take the **worst** of their parts and never an average: surviving two
        execution stresses and failing the third is an execution problem, and averaging it
        away is how a fragile system passes. The control task scores nothing -- it is the
        denominator, not a competitor.
    """
    stress = result["stress"]
    g = cfg["gates"]
    return {
        "production": min(
            curve(stress["fragility"]["net_p5"]["point"], 0.0, stress["original_net"] * 0.5),
            curve(stress["fragility"]["drawdown"]["cvar"], g["survival_dd_pct"] * 100, 5.0),
            curve(stress["evidence"]["p_positive"], 0.5, 1.0)),
        "execution": curve(_kept(result, "execution"), g["exec_keep_frac"], 1.0),
        "specification": curve(_kept(result, "specification"), 0.0, 1.0),
        "data": curve(_kept(result, "data"), 0.0, 1.0)}


def verdict(scores: dict, flags: list[dict], cfg: dict) -> dict:
    """The call, and the one constraint that drove it.

    Args:
        scores: What subscores() returned.
        flags: What gates.check() returned.
        cfg: What inputs.config.load() returned.

    Returns:
        The composite, the tier, the binding constraint and the named vetoes. A gating veto
        is FAIL whatever the score. A data veto with no gating veto is INCONCLUSIVE, never
        FAIL: it says the evidence could not settle the question, which is a different
        statement about a different thing.
    """
    weights = cfg["scoring"]["weights"]
    composite = sum(scores[key] * weights[key] for key in weights)
    vetoed = [flag for flag in flags if flag["gate"]]
    blocked = [flag for flag in flags if flag["veto"] in gates.DATA_VETOES]
    tiers = cfg["scoring"]["tiers"]

    if vetoed:
        call = "FAIL"
    elif blocked:
        call = "INCONCLUSIVE"
    else:
        call = ("STRONG" if composite >= tiers[0] else
                "ACCEPTABLE" if composite >= tiers[1] else
                "MARGINAL" if composite >= tiers[2] else "FAIL")
    return {"composite": round(composite, 1), "verdict": call, "subscores": scores,
            "binding": min(scores, key=scores.get),
            "vetoes": sorted({flag["veto"] for flag in vetoed}),
            "blocked_by": sorted({flag["veto"] for flag in blocked})}

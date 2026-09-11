"""How good a strategy is once nothing has vetoed it: five sub-scores, then one composite."""

from strategies.monteCarlo import gates, sweeps

VERDICTS = ("STRONG", "ACCEPTABLE", "MARGINAL", "FAIL", "INCONCLUSIVE")
# What each sub-score is built from. The report prints this beside the number, because a
# score whose ingredients are not visible is a number nobody can argue with.
BUILT_FROM = {
    "A": "inflación del drawdown, margen del percentil 99 frente al techo de cuenta, "
         "y el Ret/DD del percentil 5",
    "B": "beneficio y profit factor del percentil 5, y cuánto pesa la mejor operación",
    "C": "la peor de las cuatro pruebas de ejecución",
    "D": "ventanas que aguantan, el peor bloque de 24 meses, y el tercil de volatilidad alta",
    "E": "la Probabilistic Sharpe Ratio"}


def curve(value: float, bad: float, good: float) -> float:
    """A monotonic 0-100 mapping between the value that fails and the value that is fine.

    Args:
        value: What was measured.
        bad: The value scoring 0. May be above or below `good`.
        good: The value scoring 100.

    Returns:
        A score, clipped at both ends. Straight-line and stated rather than a curve chosen
        to make the numbers look right: the thresholds are the judgement, and they are all
        in gates.py and the config.
    """
    if value != value:
        return 0.0
    return float(min(100.0, max(0.0, 100.0 * (value - bad) / (good - bad))))


def subscores(result: dict, cfg: dict) -> dict[str, float]:
    """One score per family, on the metrics that family exists to measure.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        {"A".."E": 0-100}. Families C and D take the worst of their parts and never an
        average: a strategy that survives three execution stresses and fails the fourth has
        an execution problem, and averaging it away is how a fragile system passes.
    """
    s, d, e = cfg["scoring"], cfg["family_d"], cfg["family_e"]
    a_, b, c = result["A"], result["B"], result["C"]
    ret_dd = result["A"]["runs"][sweeps.HEADLINE]["ret_dd"]["p"][5]
    scores = {
        "A": (curve(a_["inflation"], s["dd_inflation_flag"], 1.0)
              + curve(s["survival_dd_pct"] / a_["dd_pct_99"], 1.0, 3.0)
              + curve(ret_dd, 0.0, 3.0)) / 3,
        "B": (curve(b["net_5"] / result["observed"]["net"], 0.0, 0.5)
              + curve(b["pf_5"], s["min_pf"], 1.5)
              + curve(b["outlier"]["share"], cfg["family_b"]["outlier_frac"], 0.0)) / 3,
        "C": min([curve(c[k]["keep"], cfg["family_c"][limit], 1.0)
                  for k, (_, limit) in gates.C_FLOORS.items()]
                 + [curve(v["pf_5"], s["min_pf"], 1.5)
                    for k, v in c.items() if k not in gates.C_FLOORS]),
        "D": min(curve(gates.passing(result["D"]["overlapping"]), d["window_pass_frac"], 1.0),
                 curve(min((w["pf_5"] for w in result["D"]["nonoverlapping"]
                            if w["pf_5"] == w["pf_5"]), default=float("nan")), 1.0, 1.4),
                 curve(result["D"]["regime"]["buckets"]["high"]["pf_5"], 1.0, 1.4)),
        "E": curve(result["E"]["psr"], e["psr_gate"], e["psr_target"])}
    return {k: round(v, 1) for k, v in scores.items()}


def verdict(result: dict, cfg: dict) -> dict:
    """The headline: the sub-scores, the composite, what fired, and what is binding.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        Sub-scores, weighted composite, the flags, the tier and the binding constraint. The
        composite is PASS-eligible only when no gate fired; otherwise the tier is FAIL, or
        INCONCLUSIVE when what failed was the sample rather than the strategy, and the
        composite travels with it as a reference the reader is told not to trust.
    """
    fired = gates.check(result, cfg)
    parts = subscores(result, cfg)
    w = cfg["scoring"]["weights"]
    composite = round(sum(parts[k] * w[k] for k in parts), 1)
    strong, acceptable, marginal = cfg["scoring"]["tiers"]
    vetoes = [f for f in fired if f["gate"]]
    data_only = vetoes and all(f["family"] == "data" for f in vetoes)
    if vetoes:
        tier = VERDICTS[4] if data_only else VERDICTS[3]
    elif composite >= strong:
        tier = VERDICTS[0]
    elif composite >= acceptable:
        tier = VERDICTS[1]
    elif composite >= marginal:
        tier = VERDICTS[2]
    else:
        tier = VERDICTS[3]
    binding = (vetoes[0] if vetoes else {"family": min(parts, key=parts.get),
                                         "test": "subscore", "value": min(parts.values()),
                                         "limit": float(acceptable), "gate": False})
    return {"subscores": parts, "composite": composite, "tier": tier, "flags": fired,
            "binding": binding, "tiers": gates.tiers(result, cfg)}

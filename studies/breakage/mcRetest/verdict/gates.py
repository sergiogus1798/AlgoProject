"""What disqualifies a strategy. Every threshold in the study lives here and nowhere else."""

from studies.breakage.mcRetest.inputs import tasks

# Every veto this module can raise. render/text.py must carry a sentence for each, and
# report.py asserts the two sets are equal at start-up: a veto that fires with no words
# attached is a verdict nobody can argue with.
VETOES = ("beneficio_no_robusto", "drawdown_insostenible", "colapso_de_regimen",
          "edge_indistinguible_de_cero", "ejecucion_fragil", "sobreajuste_de_parametros",
          "tarea_sin_dispersion", "tabla_de_niveles_corrupta", "reconciliacion_fallida")

# Vetoes that mean "this could not be judged", not "this failed". They block a pass without
# claiming the strategy is bad, and scoring maps them to INCONCLUSIVE.
DATA_VETOES = ("tarea_sin_dispersion", "tabla_de_niveles_corrupta", "reconciliacion_fallida")


def _flag(group: str, test: str, value: float, limit: float, veto: str, gate: bool) -> dict:
    """One failed or flagged check.

    Args:
        group: Which question raised it, or "data".
        test: What was checked.
        value: What it measured.
        limit: What it had to clear.
        veto: Which entry of VETOES it raises.
        gate: True when it disqualifies, False when it only has to be seen.

    Returns:
        The record the report prints. The words that describe it live in render/text.py:
        this module decides, it does not narrate.
    """
    return {"group": group, "test": test, "value": float(value), "limit": float(limit),
            "veto": veto, "gate": gate}


def production(result: dict, cfg: dict) -> list[dict]:
    """The only task that carries outcome thresholds.

    Args:
        result: One strategy's per-task results, keyed by task.
        cfg: What inputs.config.load() returned.

    Returns:
        Every production veto that fired. Only the combined-stress task is judged on its
        outcome, for two reasons that are both structural: it is the only one run on the
        full sample with real out-of-sample trades, and the other seven measure a
        *sensitivity* rather than a result. A drawdown percentile from an in-sample re-run
        is not a number to size an account against.
    """
    g, got = cfg["gates"], result["stress"]
    out = []
    if got["fragility"]["net_p5"]["point"] <= 0:
        out.append(_flag("production", "net_p5", got["fragility"]["net_p5"]["point"], 0.0,
                         "beneficio_no_robusto", True))
    if got["fragility"]["pf_p5"]["point"] <= g["min_pf"]:
        out.append(_flag("production", "pf_p5", got["fragility"]["pf_p5"]["point"],
                         g["min_pf"], "beneficio_no_robusto", True))
    if got["fragility"]["drawdown"]["cvar"] > g["survival_dd_pct"] * 100:
        out.append(_flag("production", "cvar_drawdown", got["fragility"]["drawdown"]["cvar"],
                         g["survival_dd_pct"] * 100, "drawdown_insostenible", True))
    if got["modes"]["trades"]["collapsed"]:
        out.append(_flag("production", "trade_count", got["modes"]["trades"]["median_share"],
                         g["collapse_frac"], "colapso_de_regimen", True))
    if got["evidence"]["p_positive"] < g["psr_gate"] and result["psr"]["psr"] < g["psr_gate"]:
        out.append(_flag("production", "edge", got["evidence"]["p_positive"], g["psr_gate"],
                         "edge_indistinguible_de_cero", True))
    return out


def fragility(result: dict, cfg: dict) -> list[dict]:
    """The two diagnostic failures that disqualify, and the rest that only have to be seen.

    Args:
        result: One strategy's per-task results, keyed by task.
        cfg: What inputs.config.load() returned.

    Returns:
        Every diagnostic flag, gating or not. Execution is judged as a **conjunction over
        its three axes and never an average**: a strategy that survives worse spread and
        worse slippage but dies on minimum distance has an execution problem, and averaging
        it away is how a fragile system passes. The parameter task disqualifies despite
        being in-sample because it is not a level comparison -- it is a strategy whose own
        numbers moved 15% and whose 5th percentile is a loss, and that is disqualifying on
        any sample.
    """
    g, out = cfg["gates"], []
    execution = [key for key in result if key in tasks.ROLE and tasks.ROLE[key] == "execution"]
    kept = [result[key]["fragility"]["net_p5"]["point"] / result[key]["original_net"]
            for key in execution if result[key]["original_net"]]
    if kept and min(kept) < g["exec_keep_frac"]:
        out.append(_flag("execution", "worst_axis", min(kept), g["exec_keep_frac"],
                         "ejecucion_fragil", True))
    if "params" in result and result["params"]["fragility"]["net_p5"]["point"] <= 0:
        out.append(_flag("specification", "params_p5",
                         result["params"]["fragility"]["net_p5"]["point"], 0.0,
                         "sobreajuste_de_parametros", True))
    for key in ("ohlc", "exits"):
        if key in result and result[key]["fragility"]["net_p5"]["point"] <= 0:
            out.append(_flag(tasks.ROLE[key], f"{key}_p5",
                             result[key]["fragility"]["net_p5"]["point"], 0.0,
                             "beneficio_no_robusto", False))
    return out


def data(result: dict, provenance: dict) -> list[dict]:
    """What could not be judged, as distinct from what failed.

    Args:
        result: One strategy's per-task results, keyed by task.
        provenance: The manifest entries for this strategy's runs, keyed by task.

    Returns:
        A flag per task that changed nothing at all, per run whose stored confidence
        table is rank-shifted, and per reconciliation that did not hold. **These block a
        pass without claiming the strategy failed.** A task that perturbed nothing is not
        an approval: measured here, the minimum-distance task moved five of five strategies
        by exactly nothing, because their stops sit far enough from price that a broker
        never refuses one.
    """
    out = []
    for task, got in result.items():
        if task in tasks.ROLE and not got["modes"]["perturbed"]:
            out.append(_flag("data", f"{task}_outcomes", got["modes"]["outcomes"], 0,
                             "tarea_sin_dispersion", False))
    for task, got in provenance.items():
        if not got.get("usable", True):
            out.append(_flag("data", f"{task}_levels", got["stored"], got["declared"],
                             "tabla_de_niveles_corrupta", False))
    return out


def check(result: dict, provenance: dict, cfg: dict) -> list[dict]:
    """Every veto and every flag, for one strategy.

    Args:
        result: One strategy's per-task results, keyed by task.
        provenance: The manifest entries for this strategy's runs, keyed by task.
        cfg: What inputs.config.load() returned.

    Returns:
        The flags, gating ones first. This module reads numbers and computes none of them.
    """
    flags = production(result, cfg) + fragility(result, cfg) + data(result, provenance)
    return sorted(flags, key=lambda flag: not flag["gate"])

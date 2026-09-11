"""What disqualifies a strategy. Every threshold in the study lives here and nowhere else."""

from strategies.monteCarlo import confidence

# A sub-test's floor: which numbers of the Family C entry are read, and against what.
C_FLOORS = {"skip": ("keep", "skip_keep_frac"), "fill_degrade": ("keep", "fill_keep_frac")}


def _flag(family: str, test: str, value: float, limit: float, gate: bool) -> dict:
    """One failed or flagged check.

    Args:
        family: "A" to "E", or "data".
        test: What was checked.
        value: What it measured.
        limit: What it had to clear.
        gate: True when it vetoes the verdict, False when it only has to be seen.

    Returns:
        The record the report prints. The words that describe it live in text.py: this
        module decides, it does not narrate.
    """
    return {"family": family, "test": test, "value": float(value),
            "limit": float(limit), "gate": gate}


def tiers(result: dict, cfg: dict) -> dict:
    """The sample-size tier of every statistic a gate is read from.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        {statistic: tier} plus the worst of them. A verdict is only as good as the least
        supported number under it, so PASS is unavailable when any of these is unreliable.
    """
    n = result["n_trades"]
    oos = result["B"]["samples"].get("OOS", {}).get("n", 0)
    out = {"dd_95": confidence.percentile(n, 95), "dd_99": confidence.percentile(n, 99),
           "net_5": confidence.percentile(n, 5),
           "blocks": (confidence.blocks(n, min(result["blocks"]), cfg["blocks"]["min_blocks"])
                      if result["blocks"] else confidence.TIERS[2]),
           "oos_median": confidence.average(oos)}
    return {**out, "worst": confidence.worst(list(out.values()))}


def _family_c(result: dict, cfg: dict) -> list[dict]:
    """The four execution sub-tests against their floors.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        One flag per sub-test that fell short. Conjunction, never an average: fragility on
        any single axis of execution is disqualifying on its own.
    """
    c, floor = cfg["family_c"], cfg["scoring"]["min_pf"]
    out = []
    for name, got in result["C"].items():
        if name in C_FLOORS:
            key, limit = C_FLOORS[name]
            if got["median_net"] <= 0 or got[key] < c[limit]:
                out.append(_flag("C", name, got[key], c[limit], True))
        elif got["net_5"] <= 0 or got["pf_5"] <= floor:
            out.append(_flag("C", name, got["pf_5"], floor, True))
    return out


def passing(rows: list[dict]) -> float:
    """Share of calendar windows whose 5th-percentile net profit is above zero.

    Args:
        rows: Window rows from run.analyse(), either view.

    Returns:
        A fraction over the windows that had enough trades to be resampled at all.
    """
    usable = [r for r in rows if r["net_5"] == r["net_5"]]
    return len([r for r in usable if r["net_5"] > 0]) / len(usable) if usable else 0.0


def check(result: dict, cfg: dict) -> list[dict]:
    """Every gate and every flag, in reading order.

    Args:
        result: What run.analyse() returned.
        cfg: What config.load() returned.

    Returns:
        The flags that fired. Those with gate=True veto a pass; the rest have to be seen
        and do not. Nothing that fired is left out, whatever the composite says.
    """
    s, b, d, e = cfg["scoring"], cfg["family_b"], cfg["family_d"], cfg["family_e"]
    a_, bb, dd = result["A"], result["B"], result["D"]
    out = []
    if a_["dd_pct_99"] > s["survival_dd_pct"]:
        out.append(_flag("A", "dd_99", a_["dd_pct_99"], s["survival_dd_pct"], True))
    if a_["inflation"] > s["dd_inflation_flag"]:
        out.append(_flag("A", "inflation", a_["inflation"], s["dd_inflation_flag"], True))
    elif a_["inflation"] > s["dd_inflation_watch"]:
        out.append(_flag("A", "inflation_watch", a_["inflation"], s["dd_inflation_watch"],
                         False))
    if bb["net_5"] <= 0:
        out.append(_flag("B", "net_5", bb["net_5"], 0, True))
    if bb["pf_5"] <= s["min_pf"]:
        out.append(_flag("B", "pf_5", bb["pf_5"], s["min_pf"], True))
    if bb["outlier"]["share"] > b["outlier_frac"]:
        out.append(_flag("B", "outlier", bb["outlier"]["share"], b["outlier_frac"], False))
    if bb["oos_ratio"] < b["oos_red_frac"]:
        out.append(_flag("B", "oos_red", bb["oos_ratio"], b["oos_red_frac"], False))
    elif bb["oos_ratio"] < b["oos_amber_frac"]:
        out.append(_flag("B", "oos_amber", bb["oos_ratio"], b["oos_amber_frac"], False))
    out += _family_c(result, cfg)
    high = dd["regime"]["buckets"]["high"]
    if high["median_net"] <= 0:
        out.append(_flag("D", "high_vol", high["median_net"], 0, True))
    dead = [w for w in dd["nonoverlapping"] if w["median_net"] < 0]
    if dead:
        out.append(_flag("D", "dead_block", min(w["median_net"] for w in dead), 0, True))
    share = passing(dd["overlapping"])
    if share < d["window_pass_frac"]:
        out.append(_flag("D", "windows", share, d["window_pass_frac"], False))
    if dd["regime"]["concentration"] > d["regime_concentration"]:
        out.append(_flag("D", "concentration", dd["regime"]["concentration"],
                         d["regime_concentration"], False))
    if result["E"]["psr"] < e["psr_gate"]:
        out.append(_flag("E", "psr", result["E"]["psr"], e["psr_gate"], True))
    elif result["E"]["psr"] < e["psr_target"]:
        out.append(_flag("E", "psr_amber", result["E"]["psr"], e["psr_target"], False))
    if result["cost_check"]["diverges"]:
        out.append(_flag("data", "cost_file", result["cost_check"]["ratio"], 1.0, False))
    if tiers(result, cfg)["worst"] == confidence.TIERS[2]:
        out.append(_flag("data", "sample", result["n_trades"], 0, True))
    return out

"""The rule machine over Monte Carlo paths and risk settings: who passes, when, and which rule fails."""

import numba
import numpy as np

from portfolio.funded.rules.catalog import Plan
from portfolio.funded.rules.machine import (
    _BAL,
    _BEST_TOTAL,
    _MINDAYS,
    _PROFITABLE,
    _STATIC,
    _TRAILING,
    _stage_matrix,
)

RULES = ("daily_loss", "max_loss", "time_limit")  # codes 1, 2, 3 of the kernel


def stage_names(plan: Plan) -> list[str]:
    """The challenge stages of a plan, in order (the funded stage is not a phase to pass)."""
    return [s["stage"] for s in plan["stages"] if s["stage"] != "funded"]


def outcomes(
    paths: dict[str, np.ndarray], plan: Plan, risk: np.ndarray
) -> dict[str, np.ndarray]:
    """Every path through every risk setting, from its day 0.

    The day loop is `portfolio.funded.rules.machine`'s own (`tests/test_portfolio_stageb.py`
    holds it equal to `machine.challenge` path by path); it adds what the machine's sweep
    does not return: the stage reached, the day and the rule.

    Args:
        paths: `mc.paths` output, [n_paths, horizon].
        plan: A `catalog.plan()` dict.
        risk: float64 [C, stages] — per setting and challenge stage, the multiplier of the
            unit-risk paths (risk per trade × account size).

    Returns:
        [C, n_paths] each: `code` (1 pass, 0 fail, -1 open at the horizon), `passed` (stages
        passed), `day` (the day the last stage passed or the rule broke; the last day when
        open) and `rule` (0 none, else 1 + its index in `RULES`).
    """
    base = _stage_matrix(plan, {name: 1.0 for name in stage_names(plan)})
    if np.any(base[:, _MINDAYS] < 0):
        raise NotImplementedError("judge: a challenge stage has no known min_days")
    shape = (risk.shape[0], paths["closed"].shape[0])
    out = {
        "code": np.empty(shape, np.int8),
        "passed": np.empty(shape, np.int8),
        "day": np.empty(shape, np.int16),
        "rule": np.empty(shape, np.int8),
    }
    _kernel(
        paths["closed"],
        paths["float_end"],
        paths["low"],
        paths["high"],
        paths["opened"].astype(np.int64),
        base,
        np.ascontiguousarray(risk, dtype=np.float64),
        float(plan["size"]),
        out["code"],
        out["passed"],
        out["day"],
        out["rule"],
    )
    return out


def figures(got: dict[str, np.ndarray], n_stages: int) -> dict[str, np.ndarray]:
    """What a risk setting reads over its paths, one value per setting.

    Returns:
        `p_pass`, `p_fail`, `p_open` (shares of paths), `p_stage<j>` (share that passed stage
        j, j from 1), `fail_<rule>` (share that broke that rule), `t_median`, `t_p90` (server
        days from the purchase to the pass, **over the paths that passed** — a path still
        open at the horizon is in `p_open`, never in the time).
    """
    code = got["code"]
    out = {
        "p_pass": (code == 1).mean(axis=1),
        "p_fail": (code == 0).mean(axis=1),
        "p_open": (code == -1).mean(axis=1),
    }
    for j in range(n_stages):
        out[f"p_stage{j + 1}"] = (got["passed"] > j).mean(axis=1)
    for index, name in enumerate(RULES):
        out[f"fail_{name}"] = (got["rule"] == index + 1).mean(axis=1)
    took = np.where(code == 1, got["day"] + 1.0, np.nan)
    empty = ~(code == 1).any(axis=1)
    took[empty, 0] = -1.0  # keeps nanpercentile quiet; masked below
    median, p90 = np.nanpercentile(took, [50, 90], axis=1)
    out["t_median"] = np.where(empty, np.nan, median)
    out["t_p90"] = np.where(empty, np.nan, p90)
    return out


@numba.njit(parallel=True, cache=True)
def _kernel(
    closed: np.ndarray,
    float_end: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    opened: np.ndarray,
    stagemat: np.ndarray,
    risk: np.ndarray,
    size: float,
    code: np.ndarray,
    passed_out: np.ndarray,
    day_out: np.ndarray,
    rule_out: np.ndarray,
) -> None:
    """`machine._sweep_kernel`'s day loop from day 0 of each path, per risk setting, with detail."""
    n_paths, n = closed.shape
    n_stages = stagemat.shape[0]
    for p in numba.prange(n_paths):
        for c in range(risk.shape[0]):
            stage_start = 0
            outcome, rule, n_passed, at = 1, 0, 0, n - 1
            for si in range(n_stages):
                (
                    target,
                    dloss,
                    mloss,
                    mode,
                    basis,
                    mindays,
                    mdkind,
                    ppct,
                    cons,
                    ckind,
                    tlimit,
                    _,
                ) = stagemat[si]
                k = risk[c, si]
                baseline = float_end[p, stage_start - 1] if stage_start > 0 else 0.0
                carry = baseline * k
                b = size
                hw = size
                eod = size
                trading_days = 0
                profitable_days = 0
                profit_sum = 0.0
                positive_sum = 0.0
                best_day = -1e300
                d = stage_start
                done = False
                while d < n:
                    e0 = b + (0.0 if d == 0 else float_end[p, d - 1]) * k - carry
                    if dloss <= 0.0:
                        dfloor = -np.inf
                    elif basis == _BAL:
                        dfloor = b - dloss * size
                    else:
                        dfloor = max(b, e0) * (1 - dloss)
                    hw = max(hw, e0 + high[p, d] * k)
                    if mloss <= 0.0:
                        mfloor = -np.inf
                    elif mode == _STATIC:
                        mfloor = size * (1 - mloss)
                    elif mode == _TRAILING:
                        mfloor = min(hw - mloss * size, size)
                    else:
                        mfloor = min(eod - mloss * size, size)
                    if e0 + low[p, d] * k < max(dfloor, mfloor):
                        outcome, at = 0, d
                        rule = 1 if dfloor >= mfloor else 2
                        break
                    day_p = closed[p, d] * k
                    if carry != 0.0 and float_end[p, d] == 0.0:
                        day_p -= carry
                        carry = 0.0
                    b += day_p
                    eod = max(eod, b)
                    if opened[p, d] > 0:
                        trading_days += 1
                    if mdkind == _PROFITABLE and day_p >= ppct * size:
                        profitable_days += 1
                    profit_sum += day_p
                    if day_p > 0:
                        positive_sum += day_p
                    if day_p > best_day:
                        best_day = day_p
                    if b - size >= target * size:
                        days_ok = mindays == 0 or (
                            profitable_days >= mindays
                            if mdkind == _PROFITABLE
                            else trading_days >= mindays
                        )
                        cons_ok = cons == 0.0 or (
                            best_day / profit_sum <= cons
                            if ckind == _BEST_TOTAL
                            else best_day <= cons * positive_sum
                        )
                        if days_ok and cons_ok:
                            done = True
                            at = d
                            break
                    if tlimit > 0 and (d - stage_start + 1) >= tlimit:
                        outcome, rule, at = 0, 3, d
                        break
                    d += 1
                if outcome == 0:
                    break
                if not done:
                    outcome, at = -1, n - 1
                    break
                n_passed += 1
                stage_start = d + 1
            code[c, p] = outcome
            passed_out[c, p] = n_passed
            day_out[c, p] = at
            rule_out[c, p] = rule

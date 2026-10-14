"""A prop-firm challenge as a state machine over server-day equity: pass, fail (and on which rule), or open."""

from collections.abc import Mapping
from typing import Any, TypedDict

import numba
import numpy as np

from portfolio.funded.rules.catalog import Plan
from portfolio.funded.rules.floors import (
    consistency_ok,
    daily_floor,
    days_ok,
    max_floor,
    target_met,
)


class Challenge(TypedDict):
    """How one start day went through the challenge stages: pass, fail or still open, and where."""

    outcome: str
    stage: str
    day: int
    rule: str | None
    stage_days: list[int]
    flags: list[dict]


# stage column layout shared by `sweep`'s numba kernel: keep in sync with `_stage_matrix` below.
_TARGET, _DLOSS, _MLOSS, _MODE, _BASIS, _MINDAYS, _MDKIND, _PPCT, _CONS, _CKIND, _TLIMIT, _RISK = range(12)
# max_loss_mode / daily_basis / min_days_kind / consistency_kind codes
_STATIC, _TRAILING, _EOD_TRAILING = 0, 1, 2
_BAL, _MAXBE = 0, 1
_TRADING, _PROFITABLE = 0, 1
_NONE_K, _BEST_TOTAL, _BEST_POS = 0, 1, 2


def challenge(days: dict[str, np.ndarray], plan: Plan, risk: dict[str, float], start: int,
              horizon: int = 0) -> Challenge:
    """Walk one start day through every challenge stage of a plan — the readable reference.

    Args:
        days: `closed`, `float_end`, `low`, `high`, `opened` — one entry per server day, unit risk.
        plan: A `catalog.plan()` dict.
        risk: Risk multiplier per stage name (`phase1`, `phase2`, `phase3`).
        start: Day index the challenge begins on.
            A stage's `time_limit` is in path days (`catalog.plan` converts the calendar days);
            a target met on the limit day itself passes, in every walker.
        horizon: Trading days the whole challenge (every stage) must pass within, counted from
            `start`; 0 = no limit. Not passed by day `start + horizon - 1` reads "open" — a fail
            found before that day is still a fail, timing does not soften it.

    Returns:
        `outcome` ("pass"/"fail"/"open"), `stage`, `day`, `rule` (`None` unless failed),
        `stage_days` (the day each passed stage ended on), `flags` (from the plan).
    """
    stages = [s for s in plan["stages"] if s["stage"] != "funded"]
    size = plan["size"]
    n = len(days["closed"])
    stage_start = start
    stage_days: list[int] = []
    deadline = start + horizon - 1 if horizon else None

    for stage in stages:
        k = risk[stage["stage"]]
        baseline = days["float_end"][stage_start - 1] if stage_start > 0 else 0.0
        b, hw, eod, carry = size, size, size, baseline * k   # carry: the mark of trades carried in
        trading_days = profitable_days = 0
        profits: list[float] = []
        d = stage_start
        while d < n:
            if deadline is not None and d > deadline:
                return {"outcome": "open", "stage": stage["stage"], "day": d - 1, "rule": None,
                        "stage_days": stage_days, "flags": plan["flags"]}
            e0 = b + (0.0 if d == 0 else days["float_end"][d - 1]) * k - carry
            dfloor = daily_floor(b, e0, size, stage["daily_loss"], stage["daily_basis"])
            hw = max(hw, e0 + days["high"][d] * k)
            mfloor = max_floor(stage["max_loss_mode"], size, stage["max_loss"], hw, eod)
            floor = max(dfloor, mfloor)
            if e0 + days["low"][d] * k < floor:
                rule = "daily_loss" if dfloor >= mfloor else "max_loss"
                return {"outcome": "fail", "stage": stage["stage"], "day": d, "rule": rule,
                        "stage_days": stage_days, "flags": plan["flags"]}
            day_p = days["closed"][d] * k
            if carry != 0.0 and days["float_end"][d] == 0.0:
                # ponytail: the carried mark leaves the balance on the first flat day end, not on
                # the day each carried trade closes — that needs trade spans (EXECUTION.md §D)
                day_p, carry = day_p - carry, 0.0
            b += day_p
            eod = max(eod, b)
            if days["opened"][d] > 0:
                trading_days += 1
            if (stage["min_days_kind"] == "profitable" and stage["profitable_pct"] is not None
                    and day_p >= stage["profitable_pct"] * size):
                profitable_days += 1
            profits.append(day_p)
            if target_met(b, size, stage["target"]):
                stats = {"trading_days": trading_days, "profitable_days": profitable_days}
                if days_ok(stats, stage) and consistency_ok(np.array(profits), stage):
                    stage_days.append(d)
                    break
            if stage["time_limit"] and (d - stage_start + 1) >= stage["time_limit"]:
                return {"outcome": "fail", "stage": stage["stage"], "day": d, "rule": "time_limit",
                        "stage_days": stage_days, "flags": plan["flags"]}
            d += 1
        else:
            return {"outcome": "open", "stage": stage["stage"], "day": n - 1, "rule": None,
                    "stage_days": stage_days, "flags": plan["flags"]}
        stage_start = d + 1

    return {"outcome": "pass", "stage": stages[-1]["stage"], "day": stage_days[-1], "rule": None,
            "stage_days": stage_days, "flags": plan["flags"]}


def _stage_matrix(plan: Mapping[str, Any], risk: dict[str, float]) -> np.ndarray:
    """Challenge stages of a plan, packed into the numeric layout `sweep`'s kernel reads."""
    mode_code = {"static": _STATIC, "trailing": _TRAILING, "eod_trailing": _EOD_TRAILING}
    basis_code = {"balance": _BAL, "max_be": _MAXBE}
    kind_code = {None: _TRADING, "trading": _TRADING, "profitable": _PROFITABLE}
    cons_code = {None: _NONE_K, "best_over_total": _BEST_TOTAL, "best_over_positive_sum": _BEST_POS}
    rows = []
    for s in plan["stages"]:
        if s["stage"] == "funded":
            continue
        rows.append([s["target"], s["daily_loss"], s["max_loss"], mode_code[s["max_loss_mode"]],
                     basis_code[s["daily_basis"]], -1 if s["min_days"] is None else s["min_days"],
                     kind_code[s["min_days_kind"]], s["profitable_pct"] or 0.0, s["consistency"],
                     cons_code[s["consistency_kind"]], s["time_limit"], risk[s["stage"]]])
    return np.array(rows, dtype=np.float64)


def sweep(days: dict[str, np.ndarray], plan: Mapping[str, Any], risk: dict[str, float], starts: np.ndarray,
          horizon: int = 0) -> np.ndarray:
    """`challenge`, from many start days at once — numba, identical to it day for day.

    Args:
        days: As in `challenge`.
        plan: A `catalog.plan()` dict; every `min_days` used must be known (else `challenge` itself
            raises `NotImplementedError`, and so does this).
        risk: Risk multiplier per stage name.
        starts: Start day indices, int64.
        horizon: As in `challenge`; 0 = no limit.

    Returns:
        One outcome code per start: 1 pass, 0 fail, -1 open.
    """
    stagemat = _stage_matrix(plan, risk)
    if np.any(stagemat[:, _MINDAYS] < 0):
        raise NotImplementedError("sweep: a challenge stage has no known min_days")
    return _sweep_kernel(days["closed"], days["float_end"], days["low"], days["high"],
                          days["opened"], stagemat, np.asarray(starts, dtype=np.int64),
                          plan["size"], horizon)


@numba.njit(cache=True)
def _sweep_kernel(closed: np.ndarray, float_end: np.ndarray, low: np.ndarray, high: np.ndarray,
                   opened: np.ndarray, stagemat: np.ndarray, starts: np.ndarray, size: float,
                   horizon: int) -> np.ndarray:
    """`challenge`'s day loop, inlined per `_stage_matrix`'s columns, over every start at once."""
    n = closed.shape[0]
    n_stages = stagemat.shape[0]
    out = np.empty(starts.shape[0], dtype=np.int64)
    for i in range(starts.shape[0]):
        start = starts[i]
        deadline = start + horizon - 1 if horizon else n - 1
        stage_start = start
        outcome = 1
        for si in range(n_stages):
            target, dloss, mloss, mode, basis, mindays, mdkind, ppct, cons, ckind, tlimit, k = \
                stagemat[si]
            baseline = float_end[stage_start - 1] if stage_start > 0 else 0.0
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
            passed = False
            while d < n:
                if d > deadline:
                    outcome = -1
                    break
                e0 = b + (0.0 if d == 0 else float_end[d - 1]) * k - carry
                if dloss <= 0.0:
                    dfloor = -np.inf
                elif basis == _BAL:
                    dfloor = b - dloss * size
                else:
                    dfloor = max(b, e0) * (1 - dloss)
                hw = max(hw, e0 + high[d] * k)
                if mloss <= 0.0:
                    mfloor = -np.inf
                elif mode == _STATIC:
                    mfloor = size * (1 - mloss)
                elif mode == _TRAILING:
                    mfloor = min(hw - mloss * size, size)
                else:
                    mfloor = min(eod - mloss * size, size)
                floor = max(dfloor, mfloor)
                if e0 + low[d] * k < floor:
                    outcome = 0
                    break
                day_p = closed[d] * k
                if carry != 0.0 and float_end[d] == 0.0:
                    day_p -= carry
                    carry = 0.0
                b += day_p
                eod = max(eod, b)
                if opened[d] > 0:
                    trading_days += 1
                if mdkind == _PROFITABLE and day_p >= ppct * size:
                    profitable_days += 1
                profit_sum += day_p
                if day_p > 0:
                    positive_sum += day_p
                if day_p > best_day:
                    best_day = day_p
                if b - size >= target * size:
                    days_ok_ = mindays == 0 or (
                        profitable_days >= mindays if mdkind == _PROFITABLE else trading_days >= mindays)
                    cons_ok = (cons == 0.0 or
                               (best_day / profit_sum <= cons if ckind == _BEST_TOTAL
                                else best_day <= cons * positive_sum))
                    if days_ok_ and cons_ok:
                        passed = True
                        break
                if tlimit > 0 and (d - stage_start + 1) >= tlimit:
                    outcome = 0
                    break
                d += 1
            if outcome == 0:
                break
            if not passed:
                outcome = -1
                break
            stage_start = d + 1
        out[i] = outcome
    return out

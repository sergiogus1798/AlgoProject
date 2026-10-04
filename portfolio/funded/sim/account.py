"""One purchased account from its first day to its end: the challenge, then the funded stage and its payouts — the readable reference."""

from collections.abc import Iterator

import numpy as np

from portfolio.funded.rules import machine
from portfolio.funded.rules.floors import consistency_ok, daily_floor, days_ok, max_floor


def funded(days: dict[str, np.ndarray], plan: dict, k: float, start: int, terms: dict,
           deny: Iterator[bool]) -> dict:
    """The funded stage from `start`: the stage's floors every day, a payout whenever one is due.

    Args:
        days: `closed`, `float_end`, `low`, `high`, `opened` — one entry per server day, unit risk.
        plan: A `plans.terms()` dict; its last stage is `funded`.
        k: Risk multiplier of the funded stage.
        start: First funded day (the day after the challenge passed).
        terms: `cycle` (path days between payouts), `cushion` (fraction of the size left in the
            account at a payout) and `lock` (truthy = after the first payout the max-loss floor
            is the initial balance) are read here.
        deny: Yields, per payout request of this draw, whether the firm denies it.

    Returns:
        `end` (the day a rule broke or a payout was denied; `None` if alive at the path's end),
        `rule`, `payouts` — `(day, gross)` with `gross` the profit withdrawn, before the split.
        A withdrawal lowers the balance; the high-water marks stay unless `lock` moves the
        floor, and minimum days and consistency are counted since the previous payout.
    """
    stage = plan["stages"][-1]
    size, cycle = plan["size"], int(terms["cycle"])
    baseline = days["float_end"][start - 1] if start > 0 else 0.0
    b, hw, eod, carry = size, size, size, baseline * k   # carry: the mark of trades carried in
    stats = {"trading_days": 0, "profitable_days": 0}
    profits: list[float] = []
    payouts: list[tuple[int, float]] = []
    next_pay = start + cycle - 1
    locked = False
    for d in range(start, len(days["closed"])):
        e0 = b + (0.0 if d == 0 else days["float_end"][d - 1]) * k - carry
        dfloor = daily_floor(b, e0, size, stage["daily_loss"], stage["daily_basis"])
        hw = max(hw, e0 + days["high"][d] * k)
        mfloor = size if locked else max_floor(stage["max_loss_mode"], size, stage["max_loss"], hw, eod)
        if e0 + days["low"][d] * k < max(dfloor, mfloor):
            return {"end": d, "rule": "daily_loss" if dfloor >= mfloor else "max_loss",
                    "payouts": payouts}
        day_p = days["closed"][d] * k
        if carry != 0.0 and days["float_end"][d] == 0.0:    # flat: the carried mark leaves the balance
            day_p, carry = day_p - carry, 0.0
        b += day_p
        eod = max(eod, b)
        stats["trading_days"] += int(days["opened"][d] > 0)
        stats["profitable_days"] += int(stage["min_days_kind"] == "profitable"
                                        and day_p >= stage["profitable_pct"] * size)
        profits.append(day_p)
        gross = b - size - terms["cushion"] * size
        if (d >= next_pay and gross > 0 and sum(profits) > 0 and days_ok(stats, stage)
                and consistency_ok(np.array(profits), stage)):
            if next(deny, False):
                return {"end": d, "rule": "denied", "payouts": payouts}
            payouts.append((d, gross))
            b -= gross
            locked = bool(terms["lock"])
            next_pay = d + cycle
            stats = {"trading_days": 0, "profitable_days": 0}
            profits = []
    return {"end": None, "rule": None, "payouts": payouts}


def life(days: dict[str, np.ndarray], plan: dict, risk: dict[str, float], start: int,
         terms: dict, deny: Iterator[bool]) -> dict:
    """One account bought on `start`: every challenge stage with the rule machine, then `funded`.

    Args:
        days, plan, terms, deny: As in `funded`.
        risk: Risk multiplier per stage name (`phase1`…`phase3`, `funded`).
        start: The day the account is bought and starts trading.

    Returns:
        `start`, `end` (`None` = still open or alive at the path's end), `where` ("challenge" or
        "funded"), `stage` and `rule` of the failure, `passed` (challenge stages passed),
        `funded_from` (`None` if never funded), `payouts`.
    """
    passed, first = 0, start
    if len(plan["stages"]) > 1:
        res = machine.challenge(days, plan, risk, start)
        passed = len(res["stage_days"])
        if res["outcome"] != "pass":
            return {"start": start, "end": res["day"] if res["outcome"] == "fail" else None,
                    "where": "challenge", "stage": res["stage"], "rule": res["rule"],
                    "passed": passed, "funded_from": None, "payouts": []}
        first = res["day"] + 1
    live = funded(days, plan, risk["funded"], first, terms, deny)
    return {"start": start, "where": "funded", "stage": "funded", "passed": passed,
            "funded_from": first, **live}

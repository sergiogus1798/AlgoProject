"""The bank walk in numba: accounts bought one after another on each draw's path, cash flows per draw."""

import numba
import numpy as np

from portfolio.funded.rules.machine import (
    _BAL,
    _BEST_TOTAL,
    _PROFITABLE,
    _STATIC,
    _TRAILING,
)

# one output row per draw — `bank.walk` (the reference) fills the same columns
COLS = (
    "paid",
    "received",
    "purchases",
    "payouts",
    "first_payout_day",
    "purchases_to_first",
    "outlay_before_first",
    "funded_accounts",
    "funded_days",
    "accounts_paid",
    "refunds",
    "pass_phase1",
    "pass_phase2",
    "pass_phase3",
    "fail_phase1",
    "fail_phase2",
    "fail_phase3",
    "ch_daily_loss",
    "ch_max_loss",
    "ch_time_limit",
    "fd_daily_loss",
    "fd_max_loss",
    "denied",
    "firm_closed",
    "budget_stop",
)
C = {name: i for i, name in enumerate(COLS)}
# cash terms, packed for the kernel — `bank.terms` builds it
TERMS = (
    "price",
    "share",
    "cycle",
    "refund",
    "cushion",
    "fee",
    "tax",
    "budget",
    "rebuy",
    "lock",
)
(
    _PAID,
    _RECV,
    _BUYS,
    _PAYS,
    _FIRST,
    _TOFIRST,
    _OUTLAY,
    _FACC,
    _FDAYS,
    _APAID,
    _REFUNDS,
) = range(11)
_PASS, _FAIL, _CH_RULE, _FD_RULE = (
    C["pass_phase1"],
    C["fail_phase1"],
    C["ch_daily_loss"],
    C["fd_daily_loss"],
)
_DENIED, _CLOSED, _BUDGET = C["denied"], C["firm_closed"], C["budget_stop"]


@numba.njit(cache=True)
def _eligible(
    mindays: float,
    mdkind: float,
    profitable: int,
    trading: int,
    cons: float,
    ckind: float,
    best: float,
    psum: float,
    pos: float,
) -> bool:
    """Minimum days and consistency over the days counted so far (the machine's two checks)."""
    if mindays != 0 and (profitable if mdkind == _PROFITABLE else trading) < mindays:
        return False
    if cons == 0.0:
        return True
    return best / psum <= cons if ckind == _BEST_TOTAL else best <= cons * pos


@numba.njit(cache=True, parallel=True)
def run(
    closed: np.ndarray,
    float_end: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    opened: np.ndarray,
    stagemat: np.ndarray,
    size: float,
    terms: np.ndarray,
    close_day: np.ndarray,
    deny: np.ndarray,
    track: np.ndarray,
) -> np.ndarray:
    """Walk every draw: buy, challenge stages, funded stage with payouts, re-buy, until path or cash ends.

    Args:
        closed, float_end, low, high: float64 [n_paths, horizon], unit risk (server-day table D).
        opened: int32 [n_paths, horizon].
        stagemat: `machine._stage_matrix` layout, the challenge stages then the funded stage last.
        size: The account's starting balance.
        terms: `TERMS`, money in one currency; `cycle` in path days; `lock` 1 = after an account's
            first payout its max-loss floor is the initial balance.
        close_day: Per draw, the day index the firm closes on (>= horizon = never).
        deny: bool [n_paths, W] — whether the draw's k-th payout request is denied.
        track: int32 [n_paths, A, 3], filled with (start, end, code) of the first A accounts;
            code 0 failed in the challenge, 1 failed funded, 2 denied, 3 still alive at the end.

    Returns:
        float64 [n_paths, len(COLS)].
    """
    price, share, cycle, refund, cushion, fee, tax, budget, rebuy, lock = terms
    n_paths, horizon = closed.shape
    n_ch = stagemat.shape[0] - 1
    out = np.zeros((n_paths, len(COLS)))
    for p in numba.prange(n_paths):
        row = out[p]
        row[_FIRST] = -1.0
        n = min(horizon, close_day[p])
        if close_day[p] < horizon:
            row[_CLOSED] = 1.0
        pay_idx = 0
        account = 0
        d = 0
        while d < n:
            if account > 0 and rebuy == 0.0:
                break
            if price > budget + row[_RECV] - row[_PAID] + 1e-9:
                row[_BUDGET] = 1.0
                break
            row[_PAID] += price
            row[_BUYS] += 1.0
            if row[_FIRST] < 0:
                row[_OUTLAY] += price
            start = d
            end = -1
            code = 3
            funded = False
            got_paid = False
            for si in range(n_ch + 1):
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
                    k,
                ) = stagemat[si]
                live = si == n_ch
                if live:
                    funded = True
                    row[_FACC] += 1.0
                stage_start = d
                next_pay = stage_start + int(cycle) - 1
                baseline = float_end[p, d - 1] if d > 0 else 0.0
                carry = baseline * k
                b = size
                hw = size
                eod = size
                trading = 0
                profitable = 0
                psum = 0.0
                pos = 0.0
                best = -1e300
                passed = False
                locked = False
                while d < n:
                    e0 = b + (0.0 if d == 0 else float_end[p, d - 1]) * k - carry
                    if dloss <= 0.0:
                        dfloor = -np.inf
                    elif basis == _BAL:
                        dfloor = b - dloss * size
                    else:
                        dfloor = max(b, e0) * (1 - dloss)
                    hw = max(hw, e0 + high[p, d] * k)
                    if locked:
                        mfloor = size
                    elif mloss <= 0.0:
                        mfloor = -np.inf
                    elif mode == _STATIC:
                        mfloor = size * (1 - mloss)
                    elif mode == _TRAILING:
                        mfloor = min(hw - mloss * size, size)
                    else:
                        mfloor = min(eod - mloss * size, size)
                    if e0 + low[p, d] * k < max(dfloor, mfloor):
                        end = d
                        row[
                            (_FD_RULE if live else _CH_RULE)
                            + (0 if dfloor >= mfloor else 1)
                        ] += 1.0
                        break
                    day_p = closed[p, d] * k
                    if carry != 0.0 and float_end[p, d] == 0.0:
                        day_p -= carry
                        carry = 0.0
                    b += day_p
                    eod = max(eod, b)
                    if opened[p, d] > 0:
                        trading += 1
                    if mdkind == _PROFITABLE and day_p >= ppct * size:
                        profitable += 1
                    psum += day_p
                    if day_p > 0:
                        pos += day_p
                    if day_p > best:
                        best = day_p
                    if live:
                        gross = b - size - cushion * size
                        if (
                            d >= next_pay
                            and gross > 0
                            and psum > 0
                            and _eligible(
                                mindays,
                                mdkind,
                                profitable,
                                trading,
                                cons,
                                ckind,
                                best,
                                psum,
                                pos,
                            )
                        ):
                            denied = pay_idx < deny.shape[1] and deny[p, pay_idx]
                            pay_idx += 1
                            if denied:
                                row[_DENIED] += 1.0
                                end = d
                                code = 2
                                break
                            row[_RECV] += gross * share * (1 - fee) * (1 - tax)
                            row[_PAYS] += 1.0
                            if row[_FIRST] < 0:
                                row[_FIRST] = d
                                row[_TOFIRST] = row[_BUYS]
                            if not got_paid:
                                got_paid = True
                                row[_APAID] += 1.0
                                if refund > 0:
                                    row[_RECV] += price
                                    row[_REFUNDS] += 1.0
                            b -= gross
                            locked = lock > 0
                            next_pay = d + int(cycle)
                            trading = 0
                            profitable = 0
                            psum = 0.0
                            pos = 0.0
                            best = -1e300
                    elif b - size >= target * size and _eligible(
                        mindays,
                        mdkind,
                        profitable,
                        trading,
                        cons,
                        ckind,
                        best,
                        psum,
                        pos,
                    ):
                        passed = True
                        row[_PASS + si] += 1.0
                        break
                    elif tlimit > 0 and (d - stage_start + 1) >= tlimit:
                        end = d
                        row[_CH_RULE + 2] += 1.0
                        break
                    d += 1
                if live:
                    row[_FDAYS] += (end if end >= 0 else n - 1) - stage_start + 1
                if not passed:
                    if end >= 0 and not live:
                        row[_FAIL + si] += 1.0
                    break
                d += 1
            if end >= 0 and code == 3:
                code = 1 if funded else 0
            if account < track.shape[1]:
                track[p, account, 0] = start
                track[p, account, 1] = end if end >= 0 else n - 1
                track[p, account, 2] = code
            account += 1
            if end < 0:
                break
            d = end + 1
    return out

"""The bank's cash over one path set: accounts one after another per draw — the reference walk, and the numba run."""

import numba
import numpy as np

from portfolio.funded.rules import machine
from portfolio.funded.sim import account, kernel
from portfolio.funded.sim.account import Life
from portfolio.funded.sim.plans import Cash, Terms

ARRAYS = ("closed", "float_end", "low", "high", "opened")
_CH_RULES = ("daily_loss", "max_loss", "time_limit")


def hazards(n_paths: int, horizon: int, p_denied: float, p_closes_year: float,
            days_per_year: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Per draw, the day the firm closes and which payout requests it denies.

    Args:
        p_denied: Probability one payout request is denied (the account ends there).
        p_closes_year: Probability the firm closes within a year; the draw ends that day.
        days_per_year: Path days in a year.

    Returns:
        `close_day` int64 [n_paths] (`horizon` = never) and `deny` bool [n_paths, horizon].
    """
    daily = 1 - (1 - p_closes_year) ** (1 / days_per_year)
    close_day = np.full(n_paths, horizon, dtype=np.int64)
    if daily > 0:
        close_day = np.minimum(rng.geometric(daily, n_paths) - 1, horizon)
    return close_day, rng.random((n_paths, horizon)) < p_denied


def walk(days: dict[str, np.ndarray], plan: Terms, risk: dict[str, float], terms: Cash,
         close_day: int, deny: np.ndarray) -> tuple[np.ndarray, list[Life]]:
    """One draw, account after account, in plain Python — what `simulate` must equal.

    Args:
        days: One path: `ARRAYS`, one entry per server day, unit risk.
        plan: A `plans.terms()` dict (challenge stages then `funded`).
        risk: Risk multiplier per stage name.
        terms: `kernel.TERMS` as a dict, money in one currency.
        close_day: Day index the firm closes on (>= the path's length = never).
        deny: This draw's row of `hazards`' `deny`.

    Returns:
        The draw's `kernel.COLS` row, and every account's `account.life` dict in purchase order
        (the next one starts the day after the previous ended).
    """
    horizon = len(days["closed"])
    n = min(horizon, int(close_day))
    days = {name: days[name][:n] for name in ARRAYS}
    row = {c: 0.0 for c in kernel.COLS}
    row["first_payout_day"] = -1.0
    row["firm_closed"] = float(close_day < horizon)
    denials = iter(deny)
    accounts: list[Life] = []
    d = 0
    while d < n and (not accounts or terms["rebuy"]):
        if terms["price"] > terms["budget"] + row["received"] - row["paid"] + 1e-9:
            row["budget_stop"] = 1.0
            break
        row["paid"] += terms["price"]
        row["purchases"] += 1
        if row["first_payout_day"] < 0:
            row["outlay_before_first"] += terms["price"]
        acc = account.life(days, plan, risk, d, terms, denials)
        accounts.append(acc)
        for i in range(acc["passed"]):
            row[f"pass_phase{i + 1}"] += 1
        if acc["funded_from"] is not None:
            row["funded_accounts"] += 1
            row["funded_days"] += (n - 1 if acc["end"] is None else acc["end"]) - acc["funded_from"] + 1
        for day, gross in acc["payouts"]:
            row["received"] += gross * terms["share"] * (1 - terms["fee"]) * (1 - terms["tax"])
            row["payouts"] += 1
            if row["first_payout_day"] < 0:
                row["first_payout_day"] = day
                row["purchases_to_first"] = row["purchases"]
        if acc["payouts"]:
            row["accounts_paid"] += 1
            if terms["refund"]:
                row["received"] += terms["price"]
                row["refunds"] += 1
        if acc["end"] is None:
            break
        if acc["rule"] == "denied":
            row["denied"] += 1
        elif acc["where"] == "funded":
            row[f"fd_{acc['rule']}"] += 1
        else:
            row[f"fail_{acc['stage']}"] += 1
            row[f"ch_{acc['rule']}"] += 1
        d = acc["end"] + 1
    return np.array([row[c] for c in kernel.COLS]), accounts


def pack(terms: Cash) -> np.ndarray:
    """A terms dict as the float vector the kernel reads, in `kernel.TERMS` order."""
    return np.array([float(terms[name]) for name in kernel.TERMS])


def stage_matrix(plan: Terms, risk: dict[str, float]) -> np.ndarray:
    """The rule machine's packed stages with the funded stage appended as the last row.

    `machine._stage_matrix` skips a stage called "funded", so the funded one goes in renamed.
    """
    stages = [*plan["stages"][:-1], {**plan["stages"][-1], "stage": "live"}]
    mat = machine._stage_matrix({"stages": stages}, {**risk, "live": risk["funded"]})
    if np.any(mat[:, machine._MINDAYS] < 0):
        raise NotImplementedError(f"{plan['plan_key']}: a stage has no known min_days")
    return mat


def simulate(paths: dict[str, np.ndarray], plan: Terms, risk: dict[str, float], terms: Cash,
             close_day: np.ndarray, deny: np.ndarray, track: int = 0,
             threads: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Every draw of a path set through the bank walk.

    Args:
        paths: `ARRAYS`, each [n_paths, horizon], unit risk.
        plan, risk, terms: As in `walk`.
        close_day, deny: `hazards`' two arrays.
        track: How many accounts per draw to log (start day, end day, code).
        threads: numba threads.

    Returns:
        float64 [n_paths, len(kernel.COLS)] and int32 [n_paths, track, 3] (−1 where no account).
    """
    numba.set_num_threads(min(threads, numba.config.NUMBA_NUM_THREADS))  # pyright: ignore[reportPrivateImportUsage, reportAttributeAccessIssue]  # numba stubs omit config.NUMBA_NUM_THREADS
    log = np.full((paths["closed"].shape[0], track, 3), -1, dtype=np.int32)
    out = kernel.run(paths["closed"], paths["float_end"], paths["low"], paths["high"],
                     paths["opened"], stage_matrix(plan, risk), float(plan["size"]), pack(terms),
                     close_day, deny, log)
    return out, log

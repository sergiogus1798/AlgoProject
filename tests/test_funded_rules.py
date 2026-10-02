"""Known-answer tests for portfolio.funded.rules: one tick breaks each floor, its twin only touches it."""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.funded.rules import catalog, machine

FAILED = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """Print one result and remember its name if it failed."""
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(name)


def _days(n: int) -> dict:
    """A flat, zero-everywhere path of `n` server days."""
    return {"closed": np.zeros(n), "float_end": np.zeros(n), "low": np.zeros(n),
            "high": np.zeros(n), "opened": np.zeros(n, dtype=np.int64)}


def _stage(**kw) -> dict:
    """A lenient stage dict (no rule binds unless overridden), for isolating one rule at a time."""
    base = dict(stage="phase1", target=1.0, daily_loss=0.99, max_loss=0.99, max_loss_mode="static",
                daily_basis="balance", min_days=0, min_days_kind="trading", profitable_pct=None,
                consistency=0.0, consistency_kind=None, time_limit=0, news_ok=True, weekend_ok=True)
    base.update(kw)
    return base


def run(days: dict, stages: list[dict], risk: dict | None = None, size: float = 10000.0,
        start: int = 0, horizon: int = 0) -> dict:
    """`machine.challenge` over a hand-built plan of `stages`, default risk 1.0 per stage."""
    risk = risk or {"phase1": 1.0, "phase2": 1.0, "phase3": 1.0}
    plan = {"plan_key": "test:x:10000:USD", "firm": "test", "family": "x", "size": size,
            "price": 0, "price_ccy": "USD", "stages": stages, "flags": []}
    return machine.challenge(days, plan, risk, start, horizon)


# 1. daily loss, FTMO balance basis
d = _days(1); d["low"][0] = -500.01
r = run(d, [_stage(daily_loss=0.05, daily_basis="balance")])
check("daily loss FTMO: breaks by one tick", r["outcome"] == "fail" and r["rule"] == "daily_loss", r)
d = _days(1); d["low"][0] = -500.00
r = run(d, [_stage(daily_loss=0.05, daily_basis="balance")])
check("daily loss FTMO: touches without breaking", r["outcome"] == "open", r)

# 2. daily loss, Hantec max(B,E) basis: overnight floating raises the next day's base
d = _days(2); d["float_end"][0] = 2000.0; d["low"][1] = -480.01
r = run(d, [_stage(daily_loss=0.04, daily_basis="max_be")])
check("daily loss Hantec (max_be): breaks by one tick",
      r["outcome"] == "fail" and r["day"] == 1 and r["rule"] == "daily_loss", r)
d = _days(2); d["float_end"][0] = 2000.0; d["low"][1] = -480.00
r = run(d, [_stage(daily_loss=0.04, daily_basis="max_be")])
check("daily loss Hantec (max_be): touches without breaking", r["outcome"] == "open", r)

# 3. static max loss
d = _days(1); d["low"][0] = -1000.01
r = run(d, [_stage(max_loss=0.10, max_loss_mode="static")])
check("static max loss: breaks by one tick", r["outcome"] == "fail" and r["rule"] == "max_loss", r)
d = _days(1); d["low"][0] = -1000.00
r = run(d, [_stage(max_loss=0.10, max_loss_mode="static")])
check("static max loss: touches without breaking", r["outcome"] == "open", r)

# 4. Hantec trailing: hw from the intraday high, locks at size after +6%
d = _days(2); d["high"][0] = 300.0; d["low"][1] = -300.01
r = run(d, [_stage(max_loss=0.06, max_loss_mode="trailing")])
check("Hantec trailing: breaks by one tick",
      r["outcome"] == "fail" and r["day"] == 1 and r["rule"] == "max_loss", r)
d = _days(2); d["high"][0] = 300.0; d["low"][1] = -300.00
r = run(d, [_stage(max_loss=0.06, max_loss_mode="trailing")])
check("Hantec trailing: touches without breaking", r["outcome"] == "open", r)
d = _days(1); d["high"][0] = 700.0; d["low"][0] = -0.01  # hw = 10700 >= size*1.06 -> locks at size
r = run(d, [_stage(max_loss=0.06, max_loss_mode="trailing")])
check("Hantec trailing: locked at size after +6%, breaks by one tick",
      r["outcome"] == "fail" and r["rule"] == "max_loss", r)
d = _days(1); d["high"][0] = 700.0; d["low"][0] = 0.0
r = run(d, [_stage(max_loss=0.06, max_loss_mode="trailing")])
check("Hantec trailing: locked at size after +6%, touches without breaking", r["outcome"] == "open", r)

# 5. FTMO eod trailing: trails the highest end-of-day balance
d = _days(2); d["closed"][0] = 1000.0; d["low"][1] = -1000.01
r = run(d, [_stage(max_loss=0.10, max_loss_mode="eod_trailing")])
check("FTMO eod trailing: breaks by one tick",
      r["outcome"] == "fail" and r["day"] == 1 and r["rule"] == "max_loss", r)
d = _days(2); d["closed"][0] = 1000.0; d["low"][1] = -1000.00
r = run(d, [_stage(max_loss=0.10, max_loss_mode="eod_trailing")])
check("FTMO eod trailing: touches without breaking", r["outcome"] == "open", r)

# 6. target with open floating: not met on equity alone
d = _days(2); d["high"][0] = 2000.0; d["closed"][1] = 500.0  # intraday floating way past target
r = run(d, [_stage(target=0.05)])
check("target: floating alone does not pass, closed P&L does", r["outcome"] == "pass" and r["day"] == 1, r)

# 7. minimum trading days
d = _days(2); d["closed"][0] = 500.0; d["opened"][0] = 1; d["opened"][1] = 1
r = run(d, [_stage(target=0.05, min_days=2, min_days_kind="trading")])
check("min trading days: target alone insufficient, day count completes it",
      r["outcome"] == "pass" and r["day"] == 1, r)
d = _days(1); d["closed"][0] = 500.0; d["opened"][0] = 1
r = run(d, [_stage(target=0.05, min_days=2, min_days_kind="trading")])
check("min trading days: one day short stays open", r["outcome"] == "open", r)

# 8. profitable days (Hantec Enhanced)
d = _days(3)
d["closed"][0] = 500.0   # profitable, but only 1 of 2 needed
d["closed"][1] = 0.0     # target still met, not profitable
d["closed"][2] = 60.0    # profitable day #2
r = run(d, [_stage(target=0.05, min_days=2, min_days_kind="profitable", profitable_pct=0.005)])
check("profitable days: needs a second profitable day even once target is met",
      r["outcome"] == "pass" and r["day"] == 2, r)

# 9. both consistency rules
d = _days(3); d["closed"] = np.array([260.0, 260.0, 280.0])
r = run(d, [_stage(target=0.08, consistency=0.35, consistency_kind="best_over_total")])
check("consistency best_over_total: exactly at 35% passes", r["outcome"] == "pass" and r["day"] == 2, r)
d = _days(3); d["closed"] = np.array([260.0, 260.0, 280.01])
r = run(d, [_stage(target=0.08, consistency=0.35, consistency_kind="best_over_total")])
check("consistency best_over_total: one tick over 35% stays open", r["outcome"] == "open", r)
d = _days(3); d["closed"] = np.array([-100.0, 350.0, 350.0])
r = run(d, [_stage(target=0.05, consistency=0.50, consistency_kind="best_over_positive_sum")])
check("consistency best_over_positive_sum: exactly at 50% passes",
      r["outcome"] == "pass" and r["day"] == 2, r)
d = _days(3); d["closed"] = np.array([-100.0, 350.0, 350.01])
r = run(d, [_stage(target=0.05, consistency=0.50, consistency_kind="best_over_positive_sum")])
check("consistency best_over_positive_sum: one tick over 50% stays open", r["outcome"] == "open", r)

# 10. phase2 starts fresh
d = _days(3); d["closed"] = np.array([200.0, 320.0, 200.0])
stages = [_stage(stage="phase1", target=0.01), _stage(stage="phase2", target=0.05)]
r = run(d, stages, risk={"phase1": 1.0, "phase2": 1.0})
check("phase2 starts fresh: passes on day 2, not day 1 (no carried balance)",
      r["outcome"] == "pass" and r["stage"] == "phase2" and r["stage_days"] == [0, 2], r)

# 11. horizon: a pass in the window passes, a late one stays open, a fail fails regardless, and horizon=0 is unbounded
d = _days(6); d["closed"][4] = 500.0
r = run(d, [_stage(target=0.05)], start=0, horizon=5)
check("horizon: pass on the deadline day (start + horizon - 1) still passes",
      r["outcome"] == "pass" and r["day"] == 4, r)
d = _days(6); d["closed"][5] = 500.0; r = run(d, [_stage(target=0.05)], start=0, horizon=5)
check("horizon: pass one day past the deadline reads open, not pass", r["outcome"] == "open", r)
d = _days(6); d["low"][5] = -1000.01
r = run(d, [_stage(max_loss=0.10, max_loss_mode="static")], start=0, horizon=5)
check("horizon: a fail past the deadline day is still open", r["outcome"] == "open", r)
d = _days(6); d["low"][2] = -1000.01
r = run(d, [_stage(max_loss=0.10, max_loss_mode="static")], start=0, horizon=5)
check("horizon: a fail inside the window is a real fail, not softened by it",
      r["outcome"] == "fail" and r["day"] == 2, r)
d = _days(4); d["closed"][0] = 200.0; d["closed"][2] = 400.0
stages = [_stage(stage="phase1", target=0.01), _stage(stage="phase2", target=0.05)]
r = run(d, stages, risk={"phase1": 1.0, "phase2": 1.0}, start=0, horizon=3)
check("horizon: counts from the challenge's own start across every stage", r["outcome"] == "open", r)
d = _days(3)   # lenient stage, neither passes nor fails: "open" from running out of days, not the deadline
r = run(d, [_stage()], start=0, horizon=0)
check("horizon=0 is unbounded: no deadline is ever hit", r["outcome"] == "open", r)

# catalogue checks against the real read-only database
plan = catalog.plan("hantec:express:10000:USD")
flags = {f["rule_key"]: f for f in plan["flags"]}
check("catalogue: hantec daily_loss_basis unconfirmed is flagged",
      flags.get("daily_loss_basis", {}).get("status") == "unconfirmed", plan["flags"])

plan = catalog.plan("hantec:endurance:10000:USD")
flags = {f["rule_key"]: f for f in plan["flags"]}
phase1 = next(s for s in plan["stages"] if s["stage"] == "phase1")
check("catalogue: Endurance carries the min_days conflict, resolved to the curated 3",
      flags.get("min_days", {}).get("status") == "conflict" and phase1["min_days"] == 3, plan["flags"])

plan = catalog.plan("hantec:enhancedx:10000:USD")
flags = {f["rule_key"]: f for f in plan["flags"]}
phase1 = next(s for s in plan["stages"] if s["stage"] == "phase1")
check("catalogue: EnhancedX carries the consistency conflict, resolved to the curated 35%",
      flags.get("consistency_formula", {}).get("status") == "conflict"
      and abs(phase1["consistency"] - 0.35) < 1e-9, plan["flags"])

universe = catalog.plans(10000, "USD")
check("catalogue: universe is the 11 active-firm plans at or under 10k USD", sorted(universe) == sorted([
    "ftmo:1step:10000:USD", "ftmo:2step:10000:USD",
    "hantec:endurance:5000:USD", "hantec:endurance:10000:USD",
    "hantec:enhanced:5000:USD", "hantec:enhanced:10000:USD",
    "hantec:enhancedx:5000:USD", "hantec:enhancedx:10000:USD",
    "hantec:express:2000:USD", "hantec:express:5000:USD", "hantec:express:10000:USD"]), universe)

# sweep == challenge on random paths, several plans, many start days
rng = np.random.default_rng(0)
CATALOGUE_PLANS = ["hantec:express:10000:USD", "hantec:enhanced:10000:USD",
                    "hantec:enhancedx:10000:USD", "hantec:endurance:10000:USD", "ftmo:2step:10000:USD"]
CODE = {"pass": 1, "fail": 0, "open": -1}
for plan_key in CATALOGUE_PLANS:
    p = catalog.plan(plan_key)
    risk = {"phase1": 0.4, "phase2": 0.4, "phase3": 0.4}
    n = 400
    days = {"closed": rng.normal(15, 60, n), "float_end": rng.normal(0, 80, n),
            "opened": rng.integers(0, 3, n), "low": -np.abs(rng.normal(60, 90, n)),
            "high": np.abs(rng.normal(60, 90, n))}
    starts = rng.integers(0, n - 1, 200)
    swept = machine.sweep(days, p, risk, starts)
    mismatches = sum(CODE[machine.challenge(days, p, risk, int(s))["outcome"]] != swept[i]
                      for i, s in enumerate(starts))
    check(f"sweep == challenge on 200 random paths ({plan_key})", mismatches == 0, f"{mismatches} mismatches")

# sweep == challenge with a horizon, several plans, many start days
for plan_key in CATALOGUE_PLANS:
    p = catalog.plan(plan_key)
    risk = {"phase1": 0.4, "phase2": 0.4, "phase3": 0.4}
    n = 400
    days = {"closed": rng.normal(15, 60, n), "float_end": rng.normal(0, 80, n),
            "opened": rng.integers(0, 3, n), "low": -np.abs(rng.normal(60, 90, n)),
            "high": np.abs(rng.normal(60, 90, n))}
    starts = rng.integers(0, n - 1, 200)
    horizon = 60
    swept = machine.sweep(days, p, risk, starts, horizon)
    mismatches = sum(CODE[machine.challenge(days, p, risk, int(s), horizon)["outcome"]] != swept[i]
                      for i, s in enumerate(starts))
    check(f"sweep == challenge with horizon=60 on 200 random paths ({plan_key})",
          mismatches == 0, f"{mismatches} mismatches")

# ftmo:1step (FTMO FAQ, confirmed 2026-09-30): no minimum days, but the best-day rule (50 % of
# the positive days) means the 10 % target cannot pass on one day and passes on two days of 5 %.
p = catalog.plan("ftmo:1step:10000:USD")
check("ftmo:1step min_days is 0 and carries no conflict",
      p["stages"][0]["min_days"] == 0 and all(f["rule_key"] != "min_days" for f in p["flags"]))
d = _days(3); d["closed"][0] = 1000.0
r = machine.challenge(d, p, {"phase1": 1.0}, 0)
check("ftmo:1step one day of +10 % does not pass (best day 100 % > 50 %)", r["outcome"] == "open", f"{r}")
d = _days(3); d["closed"][0] = 500.0; d["closed"][1] = 500.0; r = machine.challenge(d, p, {"phase1": 1.0}, 0)
check("ftmo:1step two days of +5 % pass on the second", r["outcome"] == "pass" and r["day"] == 1, f"{r}")

# sweep timing: 2,500 start days x 2,500 days
p = catalog.plan("hantec:enhanced:10000:USD")
n = 2500
days = {"closed": rng.normal(15, 60, n), "float_end": rng.normal(0, 80, n),
        "opened": rng.integers(0, 3, n), "low": -np.abs(rng.normal(60, 90, n)),
        "high": np.abs(rng.normal(60, 90, n))}
starts = np.arange(2500) % (n - 1)
machine.sweep(days, p, {"phase1": 0.4, "phase2": 0.4}, starts[:10])  # warm up numba
t0 = time.perf_counter()
machine.sweep(days, p, {"phase1": 0.4, "phase2": 0.4}, starts)
print(f"sweep timing: 2,500 starts x 2,500 days = {time.perf_counter() - t0:.3f} s")

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
if __name__ == "__main__":     # guarded (T1/R, 2026-09-30): a bare exit crashed `pytest tests/`
    sys.exit(1 if FAILED else 0)

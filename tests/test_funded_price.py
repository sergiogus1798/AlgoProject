"""Encargo 33 §7.1: the catalogue's price is Hantec's JS formula, and it is the fee the bank simulation charges."""

import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.paths import funding_dir
from portfolio.funded.rules import catalog
from portfolio.funded.sim import bank, plans

FAILED = []


def check(name: str, ok: bool, detail: object = "") -> None:
    """Print one result and remember its name if it failed."""
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if not ok else ""))
    if not ok:
        FAILED.append(name)


db = sqlite3.connect(f"file:{funding_dir() / 'funding.sqlite'}?mode=ro", uri=True)
db.row_factory = sqlite3.Row

# 1. purchase-challenge-v2.js calculateTotalPrice(): add-on price = plan.price * pct / 100, summed on
#    the base, never compounded (knowhow/costs/prop-firm-catalogue-hantec.md) — every row of `combos`
base = {r["plan_key"]: r["price"] for r in db.execute("SELECT plan_key, price FROM plans WHERE valid_to IS NULL")}
pct = {(r["plan_key"], r["option_key"]): r["price_pct"] for r in db.execute(
    "SELECT plan_key, option_key, price_pct FROM options WHERE valid_to IS NULL AND price_pct IS NOT NULL")}
rows = db.execute("SELECT plan_key, options, price FROM combos WHERE firm = 'hantec'").fetchall()
wrong = [(r["plan_key"], r["options"], r["price"]) for r in rows
         if abs(r["price"] - round(base[r["plan_key"]] * (1 + sum(
             pct[r["plan_key"], o] for o in r["options"].split(",") if o) / 100), 2)) > 1e-9]
check(f"every Hantec add-on combination ({len(rows)}) is priced base + sum(base * pct / 100)", not wrong and len(rows) > 500, wrong[:5])
price = {(r["plan_key"], r["options"]): r["price"] for r in db.execute("SELECT plan_key, options, price FROM combos")}
check("by hand: Express 10k is 99 $; + max loss (+30 %) 128.70; + max loss + target (+30 +25 %) 153.45, not 160.88",
      (price["hantec:express:10000:USD", ""], price["hantec:express:10000:USD", "MAX_DRAWDOWN"]) == (99.0, 128.7)
      and abs(price["hantec:express:10000:USD", "MAX_DRAWDOWN,PROFIT_TARGET"] - 153.45) < 1e-9,
      price["hantec:express:10000:USD", "MAX_DRAWDOWN,PROFIT_TARGET"])
check("by hand (encargo 33 §3.5.5): the 95 % split on Express 25k costs 59.70 $ more",
      abs(price["hantec:express:25000:USD", "PROFIT_SHARE_FLEXIBLE"] - price["hantec:express:25000:USD", ""] - 59.70) < 1e-9)
check("a bare plan's combination costs the plan's list price, every firm",
      all(abs(price[k, ""] - v) < 1e-9 for k, v in base.items() if (k, "") in price))

# 2. that price is the fee the simulation charges: terms -> cash -> every purchase of a draw
GAPS = {"hantec_fee_refund": False, "hantec_endurance_payout_days": 14,
        "hantec_express_floor_after_payout": "stays", "ftmo_1step_floor_after_payout": "stays"}
OWNER = dict(eurusd=1.25, payout_cushion=0.0, payout_fee=0.0, tax_rate=0.0, budget_eur=1000)
universe = catalog.plans(10000, "USD")
mismatch, fees = [], []
for key in universe:
    for options in plans.addon_sets(key, 2)[0]:
        plan = plans.terms(key, options, GAPS)
        cash = plans.cash(plan, OWNER, 260, "same_plan")
        fx = 1.25 if plan["price_ccy"] == "EUR" else 1.0
        if plan["price"] != price[key, options] or abs(cash["price"] - price[key, options] * fx) > 1e-9:
            mismatch.append((key, options, plan["price"], cash["price"]))
        fees.append((plan, cash))
check(f"the simulation's fee is the catalogue's price for every universe plan and add-on set ({len(fees)}), EUR at the given rate",
      not mismatch and len(fees) > len(universe), mismatch[:5])
doomed = {"closed": np.zeros((1, 6)), "float_end": np.zeros((1, 6)), "low": np.full((1, 6), -1.0),
          "high": np.zeros((1, 6)), "opened": np.ones((1, 6), dtype=np.int32)}       # -100 % a day: every account fails on its first
paid = []
for plan, cash in fees[::7]:
    out = bank.simulate(doomed, plan, {s["stage"]: plan["size"] for s in plan["stages"]}, cash,
                        np.array([10**9]), np.zeros((1, 6), dtype=bool), threads=1)[0][0]
    bought = min(6, int(cash["budget"] // cash["price"]))
    paid.append(abs(out[0] - bought * cash["price"]) < 1e-6 and out[2] == bought)
check(f"a draw that fails every day pays exactly that fee at every purchase the cash allows ({len(paid)} plans)", all(paid), paid)

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
if __name__ == "__main__":
    sys.exit(1 if FAILED else 0)

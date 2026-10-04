"""Known-answer tests for the bank run: the budget is a hard stop, the measures, the catalogue's terms, the table, the ledger row, the refusal."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ledger.study as study
from portfolio.funded.catalog import combos
from portfolio.funded.rules import catalog
from portfolio.funded.sim import bank, inputs, measures, plans, run, table
from portfolio.funded.sim.kernel import C, COLS

FAILED = []
NEVER = 10**9


def check(name: str, ok: bool, detail: object = "") -> None:
    """Print one result and remember its name if it failed."""
    print(f"{'OK  ' if ok else 'FAIL'} {name}" + (f" — {detail}" if not ok else ""))
    if not ok:
        FAILED.append(name)


def stage(name: str, **kw) -> dict:
    """A lenient stage (no rule binds unless overridden)."""
    base = dict(stage=name, target=0.10, daily_loss=0.99, max_loss=0.10, max_loss_mode="static",
                daily_basis="balance", min_days=0, min_days_kind="trading", profitable_pct=None,
                consistency=0.0, consistency_kind=None, time_limit=0, news_ok=True, weekend_ok=True)
    return {**base, **kw}


PLAN = {"plan_key": "test:x:10000:USD", "size": 10000.0, "flags": [],
        "stages": [stage("phase1"), stage("funded", target=0.0)]}
RISK = {"phase1": 1.0, "funded": 1.0}
TERMS = dict(price=99.0, share=0.8, cycle=5, refund=1.0, cushion=0.0, fee=0.0, tax=0.0, budget=1e9, rebuy=1.0, lock=0.0)


def draw(closed: list[float], low: dict[int, float], **terms: float) -> dict:
    """One path through the kernel and the reference (checked equal); the row as a dict."""
    c = np.array(closed, dtype=float)
    lo = np.minimum(c, 0.0)
    for day, value in low.items():
        lo[day] = value
    days = {"closed": c, "float_end": np.zeros(len(c)), "low": lo, "high": np.maximum(c, 0.0),
            "opened": np.ones(len(c), dtype=np.int32)}
    deny = np.zeros(len(c), dtype=bool)
    ref = bank.walk(days, PLAN, RISK, {**TERMS, **terms}, NEVER, deny)[0]
    out = bank.simulate({k: v[None, :] for k, v in days.items()}, PLAN, RISK, {**TERMS, **terms},
                        np.array([NEVER]), deny[None, :], threads=1)[0][0]
    check("  kernel == reference on this path", np.allclose(out, ref, atol=1e-9), (out, ref))
    return dict(zip(COLS, out))


# 1. the budget is a hard stop: every account fails on its first day
doomed = dict(closed=[0] * 10, low={d: -1000.01 for d in range(10)})
row = draw(**doomed, budget=250.0)
check("budget 250, price 99: two purchases, never a third (paid 198 <= 250), and the stop is flagged",
      (row["purchases"], row["paid"], row["budget_stop"]) == (2, 198.0, 1), row)
row = draw(**doomed, budget=98.99)
check("a budget one cent short of the price buys nothing", (row["purchases"], row["paid"]) == (0, 0.0), row)
row = draw(**doomed, budget=99.0)
check("a budget of exactly the price buys once", (row["purchases"], row["budget_stop"]) == (1, 1), row)
row = draw(**doomed, rebuy=0.0)
check("rebuy = none: one account and no more", (row["purchases"], row["budget_stop"]) == (1, 0), row)
row = draw([1000] + [100] * 5 + [0, 0, 0], {6: -1000.01}, budget=99.0)
check("payouts refill the cash: budget 99, paid 400 + 99 back, the account breaks, the next is bought",
      (row["purchases"], row["received"], row["paid"], row["budget_stop"]) == (2, 499.0, 198.0, 0), row)

# 2. measures on a matrix written by hand: 4 draws
m = np.zeros((4, len(COLS)))
m[:, C["paid"]] = [100, 200, 300, 400]
m[:, C["received"]] = [600, 0, 500, 0]
m[:, C["purchases"]] = [1, 2, 3, 4]
m[:, C["first_payout_day"]] = [10, -1, 30, -1]
m[:, C["purchases_to_first"]] = [1, 0, 3, 0]
m[:, C["outlay_before_first"]] = [100, 200, 300, 400]
m[:, C["payouts"]] = [3, 0, 1, 0]
m[:, C["funded_accounts"]] = [1, 1, 1, 1]
m[:, C["funded_days"]] = [100, 20, 60, 20]
m[:, C["pass_phase1"]] = [1, 1, 1, 1]
m[:, C["fail_phase1"]] = [0, 1, 2, 3]
m[:, C["ch_max_loss"]] = [0, 1, 2, 2]
m[:, C["ch_daily_loss"]] = [0, 0, 0, 1]
m[:, C["fd_max_loss"]] = [0, 1, 1, 1]
s = measures.summary(m, horizon=520, days_per_year=260)
check("EV = mean net = 25; per purchase 100/10; per dollar 100/1000; per month 25 / 24 months",
      (s["ev"], s["ev_per_purchase"], s["ev_per_dollar"]) == (25.0, 10.0, 0.1)
      and abs(s["ev_per_month"] - 25 / 24) < 1e-12, s)
half = measures.Z90 * np.std([500, -200, 200, -400], ddof=1) / 2
check("the 90 % interval is mean +- 1.645 sd / sqrt(n)", abs(s["ev_hi"] - 25 - half) < 1e-9 and abs(s["ev_lo"] - 25 + half) < 1e-9)
check("P(phase 1) 4/10, P(first payout) 2/4, purchases to it (1 + 3)/2, payouts per funded 4/4, life 50 d",
      (s["p_phase1"], s["p_first_payout"], s["purchases_to_first"], s["payouts_per_funded"], s["funded_life_days"])
      == (0.4, 0.5, 2.0, 1.0, 50.0), s)
check("cash drawdown: median 250, p90 370, p99 397 of [100, 200, 300, 400]",
      np.allclose([s["outlay_p50"], s["outlay_p90"], s["outlay_p99"]], [250, 370, 397]), s)
check("the rule that fails most: the challenge's max loss, 5 of 9",
      s["worst_rule"] == "pérdida máxima (challenge)" and abs(s["worst_rule_share"] - 5 / 9) < 1e-12, s)

# 3. the catalogue's terms (read-only): gaps are named, add-ons move the rules, EUR prices convert
GAPS = {"hantec_fee_refund": False, "hantec_endurance_payout_days": 14,
        "hantec_express_floor_after_payout": "initial", "ftmo_1step_floor_after_payout": "stays"}
try:
    plans.terms("hantec:endurance:10000:USD", "", {})
    check("a plan with catalogue gaps is refused", False)
except plans.Gap as gap:
    check("Hantec Endurance names its one gap: the payout frequency (the fee refund is now confirmed)",
          set(gap.missing) == {"hantec_endurance_payout_days"}, gap.missing)
base = plans.terms("hantec:express:10000:USD", "", GAPS)
more = plans.terms("hantec:express:10000:USD", "MAX_DRAWDOWN", GAPS)
check("MAX_DRAWDOWN adds 2 points to every stage's max loss and 30 % to the price",
      all(abs(b["max_loss"] + 0.02 - a["max_loss"]) < 1e-12 for a, b in zip(more["stages"], base["stages"]))
      and abs(more["price"] - 1.3 * base["price"]) < 0.005, (more["price"], base["price"]))
check("the owner's refund reading is flagged, and so are the simulation's own assumptions",
      {"funded_floor_after_payout", "funded_payout_eligibility", "funded_first_payout",
       "daily_loss_basis"} <= {f["rule_key"] for f in base["flags"]} and base["refund"] is False and base["lock"] is True)
sets, skipped = plans.addon_sets("hantec:express:10000:USD", 2)
check("add-on sets: the bare plan first, pairs included, news and on-demand payout skipped as price-only",
      sets[0] == "" and "MAX_DRAWDOWN,PROFIT_TARGET" in sets and "NEWS_TRADING" in skipped
      and "FIRST_PAYOUT_ON_DEMAND" in skipped and not any("NEWS" in s for s in sets), (sets, skipped))
ftmo = plans.terms("ftmo:2step:10000:USD", "", GAPS)
owner = dict(eurusd=1.25, payout_cushion=0.0, payout_fee=0.0, tax_rate=0.0, budget_eur=1000, rebuy="same_plan")
cash = plans.cash(ftmo, owner, 260)
check("FTMO: a EUR price in USD at the given rate, a 14-day cycle is 10 path days, 1,000 EUR is 1,250 USD",
      abs(cash["price"] - 1.25 * ftmo["price"]) < 1e-9 and (cash["cycle"], cash["budget"], cash["rebuy"]) == (10, 1250.0, 1.0)
      and ftmo["price_ccy"] == "EUR", cash)
check("FTMO 2-step: the prudent reading (no refund per account, Council 2026-10-04) is what the studies read, flagged unconfirmed; a static floor asks nothing",
      ftmo["refund"] is False and {"fee_refund", "fee_refund_scope"} <= {f["rule_key"] for f in ftmo["flags"]}
      and ftmo["lock"] is False and "funded_floor_after_payout" not in {f["rule_key"] for f in ftmo["flags"]})
_st = [{"stage": k, "profit_target_pct": t} for k, t in (("phase1", 10.0), ("phase2", 5.0), ("funded", 0))]
_row = combos._row({"plan_key": "x", "price": 100.0, "price_ccy": "USD", "firm": "hantec", "family": "enhanced",
                    "size": 1e4, "eas_allowed": 1}, [{**s, **{c: None for c in ("daily_loss_pct", "max_loss_pct", "max_loss_mode", "min_days", "consistency_pct", "reward_share_pct", "payout_days", "news_ok", "weekend_ok")}} for s in _st],
                   ({"option_key": "PROFIT_TARGET", "effect": "-2%", "price_pct": 25},))
check("Hantec's Profit Target add-on lowers phase 1 only (prudent reading, support pending)",
      (_row["p1_target_pct"], _row["p2_target_pct"]) == (8.0, 5.0), _row)
try:
    plans.terms("hantec:express:10000:USD", "", {**GAPS, "hantec_express_floor_after_payout": "maybe"})
    check("an unreadable floor reading is refused", False)
except plans.Gap as gap:
    check("an unreadable floor reading is refused", "hantec_express_floor_after_payout" in gap.missing)
check("risk grid: 2 levels, 2 challenge phases + funded = 8 combinations",
      len(plans.risk_grid(ftmo, [0.005, 0.01], [0.005, 0.01])) == 8)

# 4. the whole run on a synthetic path set, in a temp folder; then the same counted in a temp ledger
rng = np.random.default_rng(4)
n, horizon = 300, 400
trade = rng.random((n, horizon)) < 0.6
closed = rng.normal(0.10, 1.0, (n, horizon)) * trade
paths = {"closed": closed, "float_end": np.zeros((n, horizon)), "low": np.minimum(closed, 0),
         "high": np.maximum(closed, 0), "opened": trade.astype(np.int32)}
meta = {"unit_risk": 1.0, "days_per_year": 260.0, "synthetic": True, "label": "test"}
SET = ["owner.eurusd=1.2", "owner.rebuy=same_plan", "owner.haircuts=[0, 0.5, 1]", "owner.haircut_decides=0.5",
       "owner.payout_cushion=0.02", "owner.tax_rate=0", "owner.payout_fee=0", "owner.p_payout_denied=0",
       "owner.p_firm_closes_year=0", "gaps.hantec_fee_refund=false", "gaps.hantec_endurance_payout_days=14",
       "gaps.hantec_express_floor_after_payout=initial", "gaps.ftmo_1step_floor_after_payout=stays",
       "risk.challenge=[0.005, 0.01]", "risk.funded=[0.005, 0.01]"]
cfg = inputs.load(SET)
check("a complete policy is not refused", inputs.refuse(cfg) == [] and table.variants(cfg)[1] == [])
universe = catalog.plans(10000, "USD")
with tempfile.TemporaryDirectory() as tmp:
    done = run.run(paths, meta, cfg, Path(tmp) / "a", seed=1)
    frame = pd.read_parquet(Path(tmp) / "a" / "table.parquet")
    manifest = json.loads((Path(tmp) / "a" / "manifest.json").read_text())
    check("one row per universe plan, ordered by EV at the deciding haircut",
          sorted(frame["plan"]) == sorted(universe) and frame["ev"].is_monotonic_decreasing, frame["plan"].tolist())
    expected = sum(len(plans.risk_grid(v, [0.005, 0.01], [0.005, 0.01])) for v in done["variants"])
    check("every configuration scored is in search.parquet", len(pd.read_parquet(Path(tmp) / "a" / "search.parquet"))
          == expected == manifest["configurations"], expected)
    check("the EUR/USD rate, the seed and the path set are written beside the result; synthetic = no ledger row",
          (manifest["eurusd"], manifest["seed"], manifest["ledger"], manifest["paths"]["synthetic"]) == (1.2, 1, None, True))
    row = frame.iloc[0]
    check("the row's EV at the deciding h is its ev_h50, and the advantage is EV minus the monkey's",
          row["ev"] == row["ev_h50"] and abs(row["advantage"] - (row["ev"] - row["ev_monkey"])) < 1e-9)
    check("with a planted edge the curve falls as h grows, on every plan",
          bool((frame["ev_h0"] > frame["ev_h50"]).all() and (frame["ev_h50"] > frame["ev_h100"]).all()))
    addons = pd.DataFrame(done["addons"]).merge(frame[["plan", "ev"]], on="plan", suffixes=("", "_base"))
    check("an add-on's delta is its EV minus the bare plan's", np.allclose(addons["delta_ev"], addons["ev"] - addons["ev_base"]))
    check("the result is a valid study-contract dict carrying every flag as a warning",
          done["result"]["module"] == "portfolio.funded.sim" and len(done["result"]["warnings"]) == len(done["flags"]))
    again = run.run(paths, meta, cfg, Path(tmp) / "b", seed=1)
    check("the same seed and paths give the same table", pd.DataFrame(again["rows"]).equals(pd.DataFrame(done["rows"])))
    real_path = study.path
    study.path = lambda s: Path(tmp) / f"{s}.jsonl"
    try:
        run.run(paths, {**meta, "synthetic": False}, cfg, Path(tmp) / "c", seed=1,
                ledger={"study": "PORTFOLIO_test_construct", "symbol": "TESTSYM", "segment": "oos2"})
        rows = study.read("PORTFOLIO_test_construct")
    finally:
        study.path = real_path
    check("a real path set writes one ledger row counting every configuration (temp ledger)",
          len(rows) == 1 and rows.iloc[0]["n_scored"] == expected and rows.iloc[0]["n_out"] == len(universe)
          and rows.iloc[0]["score_unit"] == "ev_bank_usd", rows.to_dict("records"))

# 5. the command refuses, naming the input, when the owner's policy is missing
for missing in ("owner.rebuy", "owner.haircuts", "owner.payout_cushion",
                "gaps.hantec_express_floor_after_payout"):
    args = [a for s_ in SET if not s_.startswith(missing) for a in ("--set", s_)]
    res = subprocess.run([sys.executable, "-m", "portfolio.funded.sim.run", "--paths", "x.npz", *args],
                         cwd=ROOT, capture_output=True, text=True)
    check(f"without {missing} the command refuses and names it",
          res.returncode != 0 and "No simulo" in res.stderr and missing in res.stderr, res.stderr[-300:])
bad = inputs.load([s_.replace("haircut_decides=0.5", "haircut_decides=0.4") for s_ in SET])
check("a deciding haircut outside the list is refused", any("haircut_decides" in line for line in inputs.refuse(bad)))

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
if __name__ == "__main__":
    sys.exit(1 if FAILED else 0)

"""Known-answer tests for the funding decision: the bank's EV by hand on a one-phase plan, the zero-edge option, the gates of the choice, the deal's ΔEV, the command."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from portfolio.funded.deals import worth
from portfolio.funded.decide import choose, tables
from portfolio.funded.sim import bank, inputs, measures, run
from portfolio.funded.sim.kernel import C

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
TERMS = dict(price=99.0, share=0.8, cycle=5, refund=1.0, cushion=0.0, fee=0.02, tax=0.2, budget=1e9, rebuy=0.0, lock=0.0)

# 1. EV by hand. 1,000 draws, 300 pass the one phase on day 0 (+1,000 = the target), 700 breach the
#    max loss that day. Every path then closes +500 on day 1 and nothing after: a funded account is
#    paid 500 gross once (day 5, the first cycle) and lives on; a re-bought one never passes nor fails.
n, horizon, p = 1000, 12, 0.3
closed = np.zeros((n, horizon))
closed[:300, 0], closed[:, 1] = 1000.0, 500.0
low = np.minimum(closed, 0.0)
low[300:, 0] = -1000.01
paths = {"closed": closed, "float_end": np.zeros((n, horizon)), "low": low, "high": np.maximum(closed, 0.0),
         "opened": np.ones((n, horizon), dtype=np.int32)}
quiet = np.full(n, NEVER), np.zeros((n, horizon), dtype=bool)


def sim(**terms: float) -> np.ndarray:
    """The draws under the test terms with some replaced."""
    return bank.simulate(paths, PLAN, RISK, {**TERMS, **terms}, *quiet, threads=1)[0]


payout = 0.8 * 500 * (1 - 0.02) * (1 - 0.2)                     # 313.6 reaches the bank per funded account
one = sim()
check("rebuy = none: EV = -fee + P(pass) x (payout + refunded fee) = -99 + 0.3 x 412.6 = 24.78",
      abs(measures.ev(one) - (-99 + p * (payout + 99))) < 1e-9, measures.ev(one))
check("rebuy = none: P(first payout) is P(pass), and the worst draw loses the fee exactly",
      (measures.summary(one, horizon, 260)["p_first_payout"], measures.net(one).min()) == (p, -99.0))
many = sim(rebuy=1.0)
check("rebuy = same_plan: the 70 % that failed pay a second fee for nothing: EV = 24.78 - 0.7 x 99 = -44.52",
      abs(measures.ev(many) - (-99 + p * (payout + 99) - (1 - p) * 99)) < 1e-9, measures.ev(many))
check("no refund: EV = -99 + 0.3 x 313.6 = -4.92", abs(measures.ev(sim(refund=0.0)) - (-99 + p * payout)) < 1e-9)

# 2. a deal: the cheaper fee moves the EV by the saving on every purchase that is not refunded —
#    worth's linear reading against the simulation at the deal's price
entry = {"own": True, "table": {"folder": Path("t"), "manifest": {"paths": {"source": {"relaxed": None}},
                                                                 "config": {"owner": {"haircut_decides": 0.5}}}},
         "rows": [{**measures.summary(out, horizon, 260), "rebuy": name} for name, out in (("none", one), ("same_plan", many))]}
judged = worth.with_edge([{"plan": "test:x:10000:USD", "list": 99.0, "now": 49.5}, {"plan": "other", "list": 9.0, "now": 9.0}],
                         {"test:x:10000:USD": entry})
resim = {"none": measures.ev(sim(price=49.5)), "same_plan": measures.ev(sim(price=49.5, rebuy=1.0))}
check("worth: at half price the EV is the re-simulated one under both policies (59.43 and 24.78), and a plan without a table is left out",
      len(judged) == 2 and all(abs(j["ev_now"] - resim[j["rebuy"]]) < 1e-9 for j in judged)
      and abs(resim["none"] - 59.43) < 1e-9, (judged, resim))
check("worth: no bank table at all says, in so many words, that only the zero-edge floor judged",
      "SÓLO el suelo sin edge" in worth._edge_lines([], None)[0])
check("worth: a deal that turns a negative EV positive is called out",
      any("LA OFERTA LO CAMBIA" in line for line in worth._edge_lines(
          [{**j, "ev_list": -5.0, "ev_now": 3.0} for j in judged], None)))

# 3. the zero-edge option (optional stopping): a funded account on a fair +-100 walk, paid whenever it
#    is in profit, is breached below -1,000 (at -1,100) — what it withdraws before that averages 1,100:
#    a costless zero-edge trader takes the firm's loss allowance, so EV(h = 1) > 0 is not a bug by itself
rng = np.random.default_rng(7)
m, long_ = 4000, 3000
steps = rng.choice([-100.0, 100.0], size=(m, long_))
walks = {"closed": steps, "float_end": np.zeros((m, long_)), "low": np.minimum(steps, 0), "high": np.maximum(steps, 0),
         "opened": np.ones((m, long_), dtype=np.int32)}
option = {**PLAN, "stages": [stage("phase1", target=0.01, max_loss=0.99), stage("funded", target=0.0)]}
out = bank.simulate(walks, option, RISK, {**TERMS, "share": 1.0, "cycle": 1, "refund": 0.0, "fee": 0.0, "tax": 0.0},
                    np.full(m, NEVER), np.zeros((m, long_), dtype=bool))[0]
took = out[:, C["received"]]
check(f"zero edge, no costs: a funded account withdraws its max-loss allowance on average (1,100; read {took.mean():.0f} ± {took.std() / m ** 0.5:.0f})",
      abs(took.mean() - 1100) < 4 * took.std() / m ** 0.5, (took.mean(), out[:, C["fd_max_loss"]].mean()))
check("…and nearly every one of them has been breached by then (the average is not a truncated one)",
      out[:, C["fd_max_loss"]].mean() > 0.95, out[:, C["fd_max_loss"]].mean())


# 4. the choice (encargo 33 §3.5): each gate binds in order, the best eligible EV wins, ties are said
def row(plan: str, ev: float, **kw) -> dict:
    """A table row as the choice reads it: positive EV above its monkey, inside the budget."""
    base = dict(plan=plan, rebuy="none", ev=ev, ev_se=1.0, ev_monkey=ev - 5, outlay_p90=99.0, budget_usd=1100.0,
                ev_h0=ev + 10, ev_h50=ev, ev_h100=ev - 10)
    return {**base, **kw}


def table(plan: str, **source) -> dict:
    """A bank table whose path set came from the portfolio chosen for `plan`, verdict passed."""
    return {"manifest": {"paths": {"source": {"plan": plan, "verdict_pass": True, "verdict_label": "PASA",
                                              "edge_oos": 0.1, "members": ["a"], **source}}}}


OWNER = {"haircuts": [0, 0.5, 1], "haircut_decides": 0.5}
book = {"A": {"own": True, "table": table("A"), "rows": [row("A", 30.0), row("A", 50.0, rebuy="same_plan", outlay_p90=1200.0)]},
        "B": {"own": False, "table": table("A"), "rows": [row("B", 90.0)]},
        "C": {"own": True, "table": table("C", verdict_pass=None, verdict_label="SIN CRITERIO"), "rows": [row("C", 80.0)]},
        "D": {"own": True, "table": table("D", edge_oos=-0.2), "rows": [row("D", 70.0)]},
        "E": {"own": True, "table": table("E"), "rows": [row("E", -3.0)]},
        "F": {"own": True, "table": table("F"), "rows": [row("F", 20.0, ev_monkey=25.0)]},
        "G": {"own": True, "table": table("G"), "rows": [row("G", 29.0)]}}
got = choose.decide(book, OWNER, ignore_verdict=False)
why = {(r["plan"], r["rebuy"]): r["reason"] for r in got["rows"]}
check("the highest EV that passes every gate is chosen — not B (another plan's portfolio), C (no verdict), D (negative OOS edge) nor A/same_plan (p90 outlay over the cash)",
      (got["chosen"]["plan"], got["chosen"]["rebuy"]) == ("A", "none"), got["chosen"])
check("each refusal names its gate, in the order asked",
      "otro plan" in why["B", "none"] and "veredicto" in why["C", "none"] and "edge fuera de muestra" in why["D", "none"]
      and "supera la caja" in why["A", "same_plan"] and "no es positivo" in why["E", "none"] and "mono" in why["F", "none"], why)
check("a runner-up inside twice the Monte Carlo error of the gap is a tie, and said (30 against 29, e.t. 1 each)",
      got["runner_up"]["plan"] == "G" and got["tie"] is True)
check("the place at every haircut is written, best first", got["rows"][0]["plan"] == "B" and got["rows"][0]["rank_h50"] == 1)
check("a verdict that is None is not a pass: ignoring it is the only way C is chosen",
      choose.decide(book, OWNER, ignore_verdict=True)["chosen"]["plan"] == "C")
none = choose.decide({k: book[k] for k in "EF"}, OWNER, False)
check("nothing eligible: nothing is chosen", none["chosen"] is None and none["tie"] is False)

# 5. the tables on disk and the command, on a synthetic path set in a temp folder
rng = np.random.default_rng(4)
trade = rng.random((200, 300)) < 0.6
pnl = rng.normal(0.10, 1.0, (200, 300)) * trade
synthetic = {"closed": pnl, "float_end": np.zeros_like(pnl), "low": np.minimum(pnl, 0), "high": np.maximum(pnl, 0),
             "opened": trade.astype(np.int32)}
meta = {"unit_risk": 1.0, "days_per_year": 260.0, "synthetic": True, "label": "test", "source": None}
SET = ["owner.eurusd=1.2", "owner.payout_cushion=0", "owner.tax_rate=0", "owner.payout_fee=0", "owner.p_payout_denied=0",
       "owner.p_firm_closes_year=0", "gaps.hantec_fee_refund=false", "gaps.hantec_endurance_payout_days=14",
       "gaps.hantec_express_floor_after_payout=stays", "gaps.ftmo_1step_floor_after_payout=stays",
       "universe.max_size=2000", "addons.max_set=0", "risk.challenge=[0.005]", "risk.funded=[0.005]"]
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    run.run(synthetic, meta, inputs.load([x.replace("max_size=2000", "max_size=5000") for x in SET]),
            tmp / "20260101_000000_a", seed=1)                      # the older table covers more plans than the newer
    run.run(synthetic, meta, inputs.load([x.replace("tax_rate=0", "tax_rate=0.3") for x in SET]), tmp / "20260102_000000_b", seed=1)
    check("a synthetic table is never «the latest table of a plan»", tables.runs(tmp) == [])
    old, new = tables.read(tmp / "20260101_000000_a"), tables.read(tmp / "20260102_000000_b")
    old["manifest"]["paths"]["source"] = {"plan": "hantec:express:2000:USD"}
    picked = tables.per_plan([new, old])["hantec:express:2000:USD"]
    check("per plan, the table of the plan's own portfolio beats a newer one drawn from another's",
          picked["own"] and picked["table"] is old and len(picked["rows"]) == 2)
    cmd = [sys.executable, "-m", "portfolio.funded.decide.run", "--out", str(tmp / "d.json")]
    res = subprocess.run([*cmd, "--bank", str(tmp / "20260101_000000_a")], cwd=ROOT, capture_output=True, text=True)
    decision = json.loads((tmp / "d.json").read_text())
    check("the command prints «DECISIÓN: ninguno» on a table whose portfolio is nobody's, marks it AJUSTADO and lists the open readings",
          res.returncode == 0 and "DECISIÓN: ninguno" in res.stdout and "AJUSTADO" in res.stdout
          and "Lecturas abiertas" in res.stdout and decision["chosen"] is None and decision["adjusted"], res.stdout[-400:] + res.stderr[-400:])
    res = subprocess.run([*cmd, "--bank", str(tmp / "20260101_000000_a"), "--bank", str(tmp / "20260102_000000_b")],
                         cwd=ROOT, capture_output=True, text=True)
    check("two tables that each speak for a plan, simulated under different owner values, are not compared: the command refuses",
          res.returncode != 0 and "No decido" in res.stderr, res.stderr[-300:])
    run.run(synthetic, meta, inputs.load([*SET, "owner.haircut_decides=0.25"]), tmp / "20260103_000000_c", seed=1)
    res = subprocess.run([*cmd, "--bank", str(tmp / "20260103_000000_c")], cwd=ROOT, capture_output=True, text=True)
    check("a table ranked at another haircut than the owner's is stale: the command refuses",
          res.returncode != 0 and "decisiones vigentes" in res.stderr, res.stderr[-300:])

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
if __name__ == "__main__":
    sys.exit(1 if FAILED else 0)

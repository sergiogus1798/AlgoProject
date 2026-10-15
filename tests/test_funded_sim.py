"""Known-answer tests for portfolio.funded.sim: one account's cash to the cent, barrier odds, the haircut, kernel == reference."""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.funded.sim import bank, haircut, measures, monkey
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
    base = dict(
        stage=name,
        target=0.10,
        daily_loss=0.99,
        max_loss=0.10,
        max_loss_mode="static",
        daily_basis="balance",
        min_days=0,
        min_days_kind="trading",
        profitable_pct=None,
        consistency=0.0,
        consistency_kind=None,
        time_limit=0,
        news_ok=True,
        weekend_ok=True,
    )
    return {**base, **kw}


def plan(*stages: dict) -> dict:
    """A 10,000 account with the given stages, the last one `funded`."""
    return {
        "plan_key": "test:x:10000:USD",
        "size": 10000.0,
        "stages": list(stages),
        "flags": [],
    }


def terms(**kw) -> dict:
    """Cash terms: price 99, 80 % split, payout every 5 days, refund, no frictions, a deep pocket."""
    return {
        **dict(
            price=99.0,
            share=0.8,
            cycle=5,
            refund=1.0,
            cushion=0.0,
            fee=0.0,
            budget=1e9,
            rebuy=1.0,
            lock=0.0,
        ),
        **kw,
    }


def one(closed: list[float], low: dict[int, float] | None = None) -> dict:
    """One path from a list of daily closed P&L; `low` overrides a day's worst equity."""
    c = np.array(closed, dtype=float)
    lo = np.minimum(c, 0.0)
    for day, value in (low or {}).items():
        lo[day] = value
    return {
        "closed": c,
        "float_end": np.zeros(len(c)),
        "low": lo,
        "high": np.maximum(c, 0.0),
        "opened": np.ones(len(c), dtype=np.int32),
    }


def both(
    days: dict, plan_: dict, terms_: dict, risk: dict | None = None
) -> tuple[dict, np.ndarray, list]:
    """The reference row, checked equal to the kernel's, with the kernel's account log."""
    risk = risk or {"phase1": 1.0, "phase2": 1.0, "phase3": 1.0, "funded": 1.0}
    deny = np.zeros(len(days["closed"]), dtype=bool)
    ref, accounts = bank.walk(days, plan_, risk, terms_, NEVER, deny)
    out, log = bank.simulate(
        {k: v[None, :] for k, v in days.items()},
        plan_,
        risk,
        terms_,
        np.array([NEVER]),
        deny[None, :],
        track=4,
        threads=1,
    )
    check(
        "  kernel == reference on this path",
        np.allclose(out[0], ref, atol=1e-9),
        (out[0], ref),
    )
    return dict(zip(C, ref)), log[0], accounts


RISK = {"phase1": 1.0, "phase2": 1.0, "phase3": 1.0, "funded": 1.0}
ONE_STEP = plan(stage("phase1"), stage("funded", target=0.0))

# 1. passes on day 1, is paid twice, breaks on day 12; the next account is bought on day 13
path = one([600, 400] + [100] * 5 + [50] * 5 + [0] * 4, low={12: -1000.01})
row, log, accounts = both(path, ONE_STEP, terms(fee=0.02))
check("cash to the cent: paid 2 x 99.00", abs(row["paid"] - 198.00) < 1e-9, row["paid"])
check(
    "cash to the cent: received 400 and 200 x 0.98, plus the 99 refund",
    abs(row["received"] - (392.00 + 196.00 + 99.00)) < 1e-9,
    row["received"],
)
check(
    "first payout on day 6, after one purchase costing 99",
    (row["first_payout_day"], row["purchases_to_first"], row["outlay_before_first"])
    == (6, 1, 99.0),
    row,
)
check(
    "one funded account, 11 funded days, two payouts, one refund, broken by the funded max loss",
    (
        row["funded_accounts"],
        row["funded_days"],
        row["payouts"],
        row["refunds"],
        row["fd_max_loss"],
    )
    == (1, 11, 2, 1, 1),
    row,
)
check(
    "the second account starts the day after the first ended (12 -> 13)",
    log[0].tolist() == [0, 12, 1]
    and log[1].tolist() == [13, 15, 3]
    and accounts[1]["start"] == 13,
    log,
)
touch = both(
    one([600, 400] + [100] * 5 + [50] * 5 + [0] * 4, low={12: -1000.00}),
    ONE_STEP,
    terms(),
)[0]
check(
    "the twin that only touches the funded floor keeps its account",
    touch["purchases"] == 1,
    touch,
)

# 2. fails n = 3 times, then passes and is paid: the outlay before the first payout is n + 1 prices
path = one([0, 0, 0, 1000] + [100] * 5, low={0: -1000.01, 1: -1000.01, 2: -1000.01})
row, log, _ = both(path, ONE_STEP, terms())
check(
    "three failures then a payout: outlay 4 x 99, 4 purchases to the first payout",
    (
        row["outlay_before_first"],
        row["purchases_to_first"],
        row["fail_phase1"],
        row["ch_max_loss"],
    )
    == (396.0, 4, 3, 3),
    row,
)
check(
    "each failed account's successor starts the next day",
    log[:, 0].tolist() == [0, 1, 2, 3],
    log,
)

# 3. the trailing trap: withdrawing everything after +6 % leaves the balance on the locked floor
EXPRESS = plan(stage("funded", target=0.0, max_loss=0.06, max_loss_mode="trailing"))
row = both(one([700, 0, 0], low={1: -0.01}), EXPRESS, terms(cycle=1))[0]
check(
    "trailing locked at the start: a withdrawal of everything dies on the next tick",
    (row["payouts"], row["fd_max_loss"], row["received"]) == (1, 1, 560.0 + 99.0),
    row,
)
row = both(one([700, 0, 0], low={1: -200.00}), EXPRESS, terms(cycle=1, cushion=0.02))[0]
check(
    "a 2 % cushion pays 500 x 0.8 and survives a 200 give-back",
    (row["payouts"], row["fd_max_loss"], row["received"]) == (1, 0, 400.0 + 99.0),
    row,
)
row = both(one([700, 0, 0], low={1: -200.01}), EXPRESS, terms(cycle=1, cushion=0.02))[0]
check("...and breaks one tick below it", row["fd_max_loss"] == 1, row)

row = both(one([300, 0, 0], low={1: -0.01}), EXPRESS, terms(cycle=1, lock=1.0))[0]
check(
    "floor fixed at the initial balance by the first withdrawal: +3 % withdrawn in full dies on the next tick",
    (row["payouts"], row["fd_max_loss"]) == (1, 1),
    row,
)
row = both(one([300, 0, 0], low={1: -0.01}), EXPRESS, terms(cycle=1, lock=0.0))[0]
check(
    "...and under the other reading (the floor stays at 10,300 - 600) it lives",
    row["fd_max_loss"] == 0,
    row,
)

# 4. payout eligibility: 3 profitable days per cycle, and a denied payout ends the account
FUSSY = plan(
    stage(
        "funded",
        target=0.0,
        min_days=3,
        min_days_kind="profitable",
        profitable_pct=0.005,
    )
)
row = both(one([300, 0, 0, 0, 0, 60, 60, 0]), FUSSY, terms(refund=0.0))[0]
check(
    "no payout until the cycle holds 3 profitable days (day 6: 420 x 0.8)",
    (row["payouts"], row["first_payout_day"], row["received"]) == (1, 6, 336.0),
    row,
)
days = one([300] * 6)
ref = bank.walk(
    days,
    plan(stage("funded", target=0.0)),
    RISK,
    terms(),
    NEVER,
    np.array([True] + [False] * 5),
)[0]
check(
    "a denied payout pays nothing, ends the account and the next one is bought",
    (ref[C["denied"]], ref[C["purchases"]], ref[C["refunds"]]) == (1, 2, 0),
    ref,
)

# 5. zero-edge symmetric walk, target +10 steps, breach strictly below -6 steps (so at -7):
#    P(pass) = 7 / 17 by the gambler's ruin (the continuous +10/-6 of encargo 33 §3.5.1 is 6/16)
rng = np.random.default_rng(33)
n, horizon = 4000, 1200
steps = rng.choice([-100.0, 100.0], size=(n, horizon))
walks = {
    "closed": steps,
    "float_end": np.zeros((n, horizon)),
    "low": np.minimum(steps, 0),
    "high": np.maximum(steps, 0),
    "opened": np.ones((n, horizon), dtype=np.int32),
}
barrier = plan(
    stage("phase1", max_loss=0.06), stage("funded", target=0.0, max_loss=0.99)
)
quiet = np.full(n, NEVER), np.zeros((n, horizon), dtype=bool)
out, _ = bank.simulate(walks, barrier, RISK, terms(price=1.0, cycle=NEVER), *quiet)
passed, failed = out[:, C["pass_phase1"]].sum(), out[:, C["fail_phase1"]].sum()
p = passed / (passed + failed)
check(
    f"P(pass) = 7/17 = 0.4118 within Monte Carlo error (read {p:.4f}, {int(passed + failed)} attempts)",
    abs(p - 7 / 17) < 4 * np.sqrt(7 / 17 * 10 / 17 / (passed + failed)),
    p,
)
done = out[:, C["pass_phase1"]] > 0
buys = out[done, C["purchases"]].mean()
check(
    f"expected purchases to a pass = 1/P = 2.43 (read {buys:.3f})",
    abs(buys - 17 / 7) < 4 * np.sqrt(10 / 17) / (7 / 17) / np.sqrt(done.sum()),
    buys,
)
check(
    "measures.summary reads the same P",
    abs(measures.summary(out, horizon, 260)["p_phase1"] - p) < 1e-12,
)

# 6. the haircut: h = 1 leaves no edge, and the bank then earns what it earns on zero-edge paths
noise = rng.normal(0, 60, (3000, 500)) * (rng.random((3000, 500)) < 0.7)


def spread(closed: np.ndarray) -> dict:
    """A path set whose intraday low/high are the day's close (no excursion beyond it)."""
    return {
        "closed": closed,
        "float_end": np.zeros(closed.shape),
        "low": np.minimum(closed, 0),
        "high": np.maximum(closed, 0),
        "opened": (closed != 0).astype(np.int32),
    }


edged = spread(noise + 12.0 * (noise != 0))
cut = haircut.apply(edged, 1.0)
check(
    "edge() reads the planted 12 per closing day",
    abs(haircut.edge(edged) - 12.0) < 1.5,
    haircut.edge(edged),
)
check(
    "h = 1 leaves an edge of exactly 0, h = 0 the same object, h = 0.5 half",
    abs(haircut.edge(cut)) < 1e-9
    and haircut.apply(edged, 0) is edged
    and abs(haircut.edge(haircut.apply(edged, 0.5)) - haircut.edge(edged) / 2) < 1e-9,
)
check(
    "the monkey's demean model is the h = 1 path set",
    np.array_equal(monkey.zero_edge(edged, "demean")["closed"], cut["closed"]),
)
fresh = spread(rng.normal(0, 60, (3000, 500)) * (rng.random((3000, 500)) < 0.7))
hz = np.full(3000, NEVER), np.zeros((3000, 500), dtype=bool)
lottery = plan(
    stage("phase1", max_loss=0.06, max_loss_mode="trailing"),
    stage("funded", target=0.0, max_loss=0.06, max_loss_mode="trailing"),
)
evs = {
    name: measures.net(bank.simulate(data, lottery, RISK, terms(cushion=0.02), *hz)[0])
    for name, data in (("edge", edged), ("cut", cut), ("zero", fresh))
}
se = np.sqrt(evs["cut"].var() / 3000 + evs["zero"].var() / 3000)
check(
    f"EV at h = 1 equals the zero-edge EV within error ({evs['cut'].mean():.1f} vs {evs['zero'].mean():.1f}, "
    f"se {se:.1f}) and the planted edge is worth more ({evs['edge'].mean():.1f})",
    abs(evs["cut"].mean() - evs["zero"].mean()) < 4 * se
    and evs["edge"].mean() > evs["cut"].mean() + 4 * se,
)
check(
    "break-even h: [30, 10, -10] at h [0, .5, 1] crosses at 0.75; an all-positive curve has none",
    haircut.breakeven([0, 0.5, 1], [30, 10, -10]) == 0.75
    and haircut.breakeven([0, 1], [5, 1]) is None,
)

# 7. the numba kernel equals the plain-Python reference on 200 random paths, hazards on
n, horizon = 200, 600
closed = rng.normal(0.08, 1.0, (n, horizon)) * (rng.random((n, horizon)) < 0.7)
rand = {
    "closed": closed,
    "float_end": rng.normal(0, 0.3, (n, horizon)) * (rng.random((n, horizon)) < 0.3),
    "low": np.minimum(closed, 0) - np.abs(rng.normal(0, 0.4, (n, horizon))),
    "high": np.maximum(closed, 0) + np.abs(rng.normal(0, 0.4, (n, horizon))),
    "opened": (closed != 0).astype(np.int32),
}
shapes = {
    "trailing 1-step": plan(
        stage(
            "phase1",
            max_loss=0.06,
            max_loss_mode="trailing",
            daily_loss=0.05,
            daily_basis="max_be",
        ),
        stage(
            "funded",
            target=0.0,
            max_loss=0.06,
            max_loss_mode="trailing",
            daily_loss=0.05,
            daily_basis="max_be",
        ),
    ),
    "static 2-step, 4 days": plan(
        stage("phase1", min_days=4, daily_loss=0.05),
        stage("phase2", target=0.05, min_days=4),
        stage("funded", target=0.0, min_days=4, daily_loss=0.05),
    ),
    "eod trailing, best day": plan(
        stage(
            "phase1",
            daily_loss=0.03,
            max_loss_mode="eod_trailing",
            consistency=0.5,
            consistency_kind="best_over_positive_sum",
        ),
        stage(
            "funded",
            target=0.0,
            daily_loss=0.03,
            max_loss_mode="eod_trailing",
            consistency=0.5,
            consistency_kind="best_over_positive_sum",
        ),
    ),
    "3-step, consistency, time limit": plan(
        stage(
            "phase1",
            target=0.08,
            max_loss=0.08,
            consistency=0.35,
            consistency_kind="best_over_total",
            time_limit=120,
        ),
        stage(
            "phase2",
            target=0.04,
            min_days=3,
            min_days_kind="profitable",
            profitable_pct=0.005,
        ),
        stage("phase3", target=0.03),
        stage(
            "funded",
            target=0.0,
            consistency=0.35,
            consistency_kind="best_over_total",
            min_days=3,
            min_days_kind="profitable",
            profitable_pct=0.005,
        ),
    ),
}
risk = {"phase1": 60.0, "phase2": 40.0, "phase3": 50.0, "funded": 45.0}
close_day, deny = bank.hazards(n, horizon, 0.15, 0.30, 260, np.random.default_rng(5))
for name, shape in shapes.items():
    for policy in (
        terms(budget=600.0, fee=0.02),
        terms(budget=600.0, cushion=0.02),
        terms(rebuy=0.0, lock=1.0),
    ):
        out, _ = bank.simulate(rand, shape, risk, policy, close_day, deny, threads=4)
        ref = np.array(
            [
                bank.walk(
                    {k: v[i] for k, v in rand.items()},
                    shape,
                    risk,
                    policy,
                    close_day[i],
                    deny[i],
                )[0]
                for i in range(n)
            ]
        )
        check(
            f"kernel == reference, 200 paths: {name}, cushion {policy['cushion']}, rebuy {policy['rebuy']:g} "
            f"({int(out[:, C['purchases']].sum())} purchases, {int(out[:, C['payouts']].sum())} payouts)",
            np.allclose(out, ref, atol=1e-8),
            np.abs(out - ref).max(),
        )

# 8. reproducible under a seed
a, b = (
    bank.hazards(n, horizon, 0.15, 0.30, 260, np.random.default_rng(s)) for s in (5, 6)
)
check(
    "hazards: the same seed repeats, another seed does not",
    np.array_equal(a[0], close_day)
    and np.array_equal(a[1], deny)
    and not np.array_equal(b[1], deny),
)
again, _ = bank.simulate(rand, shape, risk, policy, close_day, deny, threads=2)
check(
    "simulate: the same inputs give the same matrix, whatever the threads",
    np.array_equal(again, out),
)

t0 = time.perf_counter()
bank.simulate(walks, barrier, RISK, terms(price=1.0, cycle=NEVER), *quiet, threads=8)
print(
    f"timing: 4,000 draws x 1,200 days = {1000 * (time.perf_counter() - t0):.1f} ms per configuration"
)

print(f"\n{len(FAILED)} failed" if FAILED else "\nall checks passed")
if __name__ == "__main__":
    sys.exit(1 if FAILED else 0)

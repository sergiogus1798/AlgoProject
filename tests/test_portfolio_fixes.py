"""Known-answer regressions of the portfolio/ calculation review (scratch/cleanup/calc-portfolio.md, findings 1-6)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.common.construct.equity import excursions
from portfolio.common.construct.mc import judge
from portfolio.common.construct.search import genetic
from portfolio.common.monteCarlo.model import stress
from portfolio.common.monteCarlo.simulate import kernel as mckernel
from portfolio.common.monteCarlo.simulate import metrics
from portfolio.funded.rules import machine
from portfolio.funded.sim import account, bank
from portfolio.funded.sim.kernel import C

RISK = {"phase1": 1.0, "phase2": 1.0, "phase3": 1.0, "funded": 1.0}
TERMS = dict(
    price=99.0,
    share=0.8,
    cycle=14,
    refund=0.0,
    cushion=0.0,
    fee=0.0,
    budget=1e9,
    rebuy=1.0,
    lock=0.0,
)


def _days(n: int) -> dict:
    """A flat path of `n` server days."""
    return {
        "closed": np.zeros(n),
        "float_end": np.zeros(n),
        "low": np.zeros(n),
        "high": np.zeros(n),
        "opened": np.ones(n, dtype=np.int64),
    }


def _stage(name: str = "phase1", **kw) -> dict:
    """A lenient stage: no rule binds unless overridden."""
    base = dict(
        stage=name,
        target=1.0,
        daily_loss=0.99,
        max_loss=0.99,
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


def _plan(*stages: dict) -> dict:
    """A 100,000 plan of the given stages."""
    return {
        "plan_key": "t:x:100000:USD",
        "firm": "t",
        "family": "x",
        "size": 100000.0,
        "price": 0,
        "price_ccy": "USD",
        "stages": list(stages),
        "flags": [],
    }


def _all_ways(days: dict, plan: dict) -> dict:
    """The challenge from day 0 by the five walkers: 1 pass, 0 fail, -1 open — and they must agree.

    The reference, the sweep and the judge walk the challenge; `account.life` and the bank's
    kernel walk it with a lenient funded stage behind.
    """
    ref = machine.challenge(days, plan, RISK, 0)
    sweep = machine._sweep_kernel(
        days["closed"],
        days["float_end"],
        days["low"],
        days["high"],
        days["opened"],
        machine._stage_matrix(plan, RISK),
        np.array([0], dtype=np.int64),
        plan["size"],
        0,
    )[0]
    paths = {k: v[None, :] for k, v in days.items()}
    code = judge.outcomes(paths, plan, np.ones((1, len(judge.stage_names(plan)))))[
        "code"
    ][0, 0]
    full, once = _plan(*plan["stages"], _stage("funded")), {**TERMS, "rebuy": 0.0}
    life = account.life(days, full, RISK, 0, once, iter(()))
    lived = 1 if life["where"] == "funded" else -1 if life["end"] is None else 0
    row, _ = bank.simulate(
        paths,
        full,
        RISK,
        once,
        np.array([10**9]),
        np.zeros((1, len(days["closed"])), dtype=bool),
        threads=1,
    )
    last = C["pass_phase1"] + len(plan["stages"]) - 1
    banked = (
        1
        if row[0, last]
        else 0
        if row[0, C["fail_phase1"] : C["fail_phase1"] + 3].sum()
        else -1
    )
    got = {"ref": ref["outcome"], "sweep": int(sweep), "judge": int(code)}
    assert lived == banked == got["sweep"] == got["judge"], (got, lived, banked)
    assert got["ref"] == {1: "pass", 0: "fail", -1: "open"}[got["sweep"]], got
    return got


def _open_carry(mark: float, **phase2) -> tuple[dict, dict]:
    """Phase 1 ends day 0 holding `mark` floating; the trade stays at that mark and closes on day 6."""
    d = _days(10)
    d["float_end"][:6], d["closed"][6] = mark, mark
    return d, _plan(_stage("phase1", target=0.0), _stage("phase2", **phase2))


def _carried(**phase2) -> tuple[dict, dict]:
    """Phase 1 ends day 0 holding +3,000 floating; the trade closes on day 1 at that same price."""
    d = _days(8)
    d["float_end"][0], d["closed"][1] = 3000.0, 3000.0
    return d, _plan(_stage("phase1", target=0.0), _stage("phase2", **phase2))


def test_daily_loss_zero_is_no_rule() -> None:
    """Finding 1: a daily-loss limit of 0 is no floor, in the reference and every kernel."""
    d = _days(1)
    d["low"][0] = -1.0
    for basis in ("max_be", "balance"):
        got = _all_ways(d, _plan(_stage(daily_loss=0.0, daily_basis=basis)))
        assert got == {"ref": "open", "sweep": -1, "judge": -1}, (basis, got)


def test_daily_loss_zero_funded_account_lives_and_pays() -> None:
    """Finding 1: the 5,000 instant plan, +20 a day with a 1 USD dip, lives and pays twice."""
    d = _days(30)
    d["closed"][:], d["high"][:], d["low"][:] = 20.0, 20.0, -1.0
    plan = {
        **_plan(_stage("funded", target=0.0, daily_loss=0.0, daily_basis="max_be")),
        "plan_key": "t:x:5000:USD",
        "size": 5000.0,
    }
    live = account.funded(d, plan, 1.0, 0, TERMS, iter(()))
    assert live["end"] is None and len(live["payouts"]) == 2, live
    row, _ = bank.simulate(
        {k: v[None, :] for k, v in d.items()},
        plan,
        RISK,
        TERMS,
        np.array([10**9]),
        np.zeros((1, 30), dtype=bool),
        threads=1,
    )
    assert row[0, C["fd_daily_loss"]] == 0 and row[0, C["payouts"]] == 2, row[0]


def test_carried_trade_does_not_count_toward_the_target() -> None:
    """Finding 3a: 7,000 earned inside the stage is not a 10 % target."""
    d, plan = _carried(target=0.10)
    d["closed"][2] = 7000.0  # real profit since the stage began: 7,000 < 10 %
    assert _all_ways(d, plan) == {"ref": "open", "sweep": -1, "judge": -1}


def test_carried_trade_does_not_shift_the_daily_floor() -> None:
    """Finding 3b: a 2,500 dip on a flat account is inside the 5 % floor."""
    d, plan = _carried(daily_loss=0.05)
    d["low"][4] = -2500.0  # a flat account: real room 5,000
    assert _all_ways(d, plan) == {"ref": "open", "sweep": -1, "judge": -1}
    row, _ = bank.simulate(
        {k: v[None, :] for k, v in d.items()},
        _plan(plan["stages"][0], plan["stages"][1], _stage("funded")),
        RISK,
        TERMS,
        np.array([10**9]),
        np.zeros((1, 8), dtype=bool),
        threads=1,
    )
    assert row[0, C["ch_daily_loss"]] == 0, row[0]


def test_carried_trade_in_the_funded_stage() -> None:
    """Finding 3: the funded walker books a carried trade the same way."""
    d = _days(8)
    d["float_end"][0], d["closed"][1] = 3000.0, 3000.0
    d["low"][4] = -2500.0
    stage = _stage("funded", daily_loss=0.05)
    live = account.funded(d, _plan(stage), 1.0, 1, TERMS, iter(()))
    assert live["end"] is None, live


def test_open_carried_loser_is_not_profit() -> None:
    """Finding 3, while the trade is open: a carried loser of 6,000 earns nothing toward a 5 % target."""
    d, plan = _open_carry(-6000.0, target=0.05)
    assert _all_ways(d, plan) == {"ref": "open", "sweep": -1, "judge": -1}


def test_open_carried_loser_leaves_no_phantom_high_water() -> None:
    """Finding 3: the end-of-day high-water stays at the size, so a 3,500 dip is inside a 6 % trail."""
    d, plan = _open_carry(-3000.0, max_loss=0.06, max_loss_mode="eod_trailing")
    d["low"][8] = -3500.0  # after the trade closed, on a flat account
    assert _all_ways(d, plan) == {"ref": "open", "sweep": -1, "judge": -1}


def test_open_carried_winner_does_not_lower_the_daily_floor() -> None:
    """Finding 3: with a carried winner open the balance is the size: a 6,000 dip breaks 5 %."""
    d, plan = _open_carry(3000.0, daily_loss=0.05)
    d["low"][3] = -6000.0  # equity 94,000 against a floor of 95,000
    assert _all_ways(d, plan) == {"ref": "fail", "sweep": 0, "judge": 0}
    assert machine.challenge(d, plan, RISK, 0)["rule"] == "daily_loss"


def test_open_carried_loser_pays_only_what_was_earned() -> None:
    """Finding 3: funded with a carried loser of 6,000 open and 10 closed, the payout is 10."""
    d = _days(10)
    d["float_end"][:6], d["closed"][6], d["closed"][2] = -6000.0, -6000.0, 10.0
    terms = {**TERMS, "cycle": 2, "rebuy": 0.0}
    live = account.funded(d, _plan(_stage("funded")), 1.0, 1, terms, iter(()))
    assert live["end"] is None and live["payouts"] == [(2, 10.0)], live
    plan = _plan(_stage("phase1", target=0.0), _stage("funded"))
    assert account.life(d, plan, RISK, 0, terms, iter(()))["payouts"] == [(2, 10.0)]
    row, _ = bank.simulate(
        {k: v[None, :] for k, v in d.items()},
        plan,
        RISK,
        terms,
        np.array([10**9]),
        np.zeros((1, 10), dtype=bool),
        threads=1,
    )
    assert row[0, C["payouts"]] == 1 and abs(row[0, C["received"]] - 8.0) < 1e-9, row[0]


def test_genetic_never_lets_nan_win() -> None:
    """Finding 2: infeasible (NaN) combinations neither win nor stop the search."""
    graph = ~np.eye(6, dtype=bool)

    def score(combos: np.ndarray) -> np.ndarray:
        """NaN where member 0 is in (infeasible), else the combination's size."""
        return np.array([np.nan if row[0] else float(row.sum()) for row in combos])

    cfg = dict(
        population=8,
        generations=40,
        elite=0.1,
        tournament=3,
        crossover=0.7,
        mutation=0.3,
        stagnation=10,
    )
    seeds = [np.array([0, 1]), np.array([1, 2]), np.array([2, 3])]
    got = genetic.run(graph, score, seeds, cfg, np.random.default_rng(1))
    assert got["best"]["score"] == np.nanmax(np.concatenate([got["score"]])) > 2
    assert got["generations_run"] > cfg["stagnation"]


def test_spread_widen_is_neutral_at_one() -> None:
    """Finding 4: a spread multiplier of 1 changes nothing; 2 adds one spread."""
    s = {"pnl": np.array([100.0, -50.0]), "spread": np.array([10.0, 10.0])}
    cfg = {"spread_scale": [1.0, 1.0]}
    assert np.array_equal(
        stress.spread_widen(s, 1, np.random.default_rng(0), cfg)[0], s["pnl"]
    )
    cfg = {"spread_scale": [2.0, 2.0]}
    assert np.array_equal(
        stress.spread_widen(s, 1, np.random.default_rng(0), cfg)[0], [90.0, -60.0]
    )


def test_drawdown_counts_the_starting_equity_as_first_peak() -> None:
    """Finding 5: pnl -100, -100, +50 has drawdown 200 (2 %), metrics and kernel alike."""
    pnl = np.array([-100.0, -100.0, 50.0])
    got = metrics.observed(pnl, 10000.0)
    assert got["dd"] == 200.0 and abs(got["dd_pct"] - 0.02) < 1e-12, got
    out = np.empty((1, len(metrics.NAMES)))
    mckernel.gathered(pnl, np.array([[0, 1, 2]]), 10000.0, out)
    assert out[0, 2] == 200.0 and abs(out[0, 3] - 0.02) < 1e-12, out


def test_excursions_trade_inside_one_bar() -> None:
    """Finding 6: a trade opened and closed in one M1 bar reads its own bar."""
    bars = pd.DataFrame(
        {"High": [10.0, 11.0], "Low": [9.0, 10.0]},
        index=pd.to_datetime(["2024-01-01 00:00", "2024-01-01 00:01"]),
    )
    tr = pd.DataFrame(
        {
            "Open time": pd.to_datetime(["2024-01-01 00:01:05"]),
            "Close time": pd.to_datetime(["2024-01-01 00:01:40"]),
            "Type": ["Buy"],
            "Size": [1.0],
            "Open price": [10.5],
        }
    )
    got = excursions.rebuild(tr, bars, 100.0)
    assert (
        abs(got["mae"][0] - (-0.5 * 100.0)) < 1e-9
        and abs(got["mfe"][0] - 0.5 * 100.0) < 1e-9
    ), got


def test_catalog_refuses_an_unknown_loss_limit(monkeypatch: object) -> None:
    """Finding 1: a NULL loss limit is refused, never read as 0."""
    import sqlite3

    from portfolio.funded.rules import catalog

    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE plans(plan_key, firm, family, size, price, price_ccy, valid_to);
        CREATE TABLE stages(plan_key, stage, profit_target_pct, daily_loss_pct, max_loss_pct, max_loss_mode,
                            min_days, time_limit_days, consistency_pct, news_ok, weekend_ok, valid_to);
        CREATE TABLE rules(rule_key, value, status, text, firm, family, valid_to);
        INSERT INTO plans VALUES('f:x:1000:USD','f','x',1000,10,'USD',NULL);
        INSERT INTO stages VALUES('f:x:1000:USD','funded',NULL,NULL,6,'static',0,NULL,NULL,1,1,NULL);""")
    monkeypatch.setattr(catalog, "_connect", lambda: db)
    try:
        catalog.plan("f:x:1000:USD")
    except NotImplementedError:
        return
    raise AssertionError("a NULL daily loss was read as 0")

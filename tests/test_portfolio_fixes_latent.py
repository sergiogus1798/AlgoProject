"""Known-answer regressions of CALC_REVIEW.md m33-m36: time limit in path days, months cut by day, the re-drawn winner, guarded ratios."""

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# first: test_portfolio_stageb plants the data root, which must precede every project import
from test_portfolio_stageb import BUILD, complete, small_cfg  # noqa: E402
from portfolio.common.construct import funded_b, universe  # noqa: E402
from portfolio.common.construct.equity import matrix
from portfolio.common.construct.inputs import config as construct_config
from portfolio.common.construct.search import stageb, stageb_run
from portfolio.common.monteCarlo.inputs import config as mc_config
from portfolio.common.monteCarlo.simulate import family_d
from portfolio.common.monteCarlo.verdict import scoring
from portfolio.funded.rules import catalog, machine
from portfolio.funded.sim import haircut
from test_portfolio_fixes import RISK, _all_ways, _days, _plan, _stage
from test_portfolio_mc_paths import bar_world, lenient_plan


def test_time_limit_is_converted_to_path_days(monkeypatch: pytest.MonkeyPatch) -> None:
    """m33: 30 calendar days on a 5-day week (260 a year) fail on trading day 21, not 30."""
    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE plans(plan_key, firm, family, size, price, price_ccy, valid_to);
        CREATE TABLE stages(plan_key, stage, profit_target_pct, daily_loss_pct, max_loss_pct, max_loss_mode,
                            min_days, time_limit_days, consistency_pct, news_ok, weekend_ok, valid_to);
        CREATE TABLE rules(rule_key, value, status, text, firm, family, valid_to);
        INSERT INTO plans VALUES('f:x:100000:USD','f','x',100000,10,'USD',NULL);
        INSERT INTO stages VALUES('f:x:100000:USD','phase1',8,5,10,'static',0,30,0,1,1,NULL);""")
    monkeypatch.setattr(catalog, "_connect", lambda: db)
    with pytest.raises(NotImplementedError):  # calendar days are never read one for one
        catalog.plan("f:x:100000:USD")
    stage = catalog.plan("f:x:100000:USD", 260)["stages"][0]
    assert stage["time_limit"] == 21, stage
    got = machine.challenge(_days(60), _plan(stage), RISK, 0)
    assert (got["rule"], got["day"] + 1) == ("time_limit", 21), got
    assert _all_ways(_days(60), _plan(stage)) == {"ref": "fail", "sweep": 0, "judge": 0}


def test_target_met_on_the_limit_day_passes_in_every_walker() -> None:
    """m33: the target is read before the limit — met on the limit day it passes, a day later it fails."""
    for hit, want in (
        (2, {"ref": "pass", "sweep": 1, "judge": 1}),
        (3, {"ref": "fail", "sweep": 0, "judge": 0}),
    ):
        d = _days(10)
        d["closed"][hit] = 2000.0
        assert _all_ways(d, _plan(_stage(target=0.01, time_limit=3))) == want, hit


def test_build_months_hold_no_day_after_the_build(tmp_path: Path) -> None:
    """m34: a build ending on the 15th — a 1,000 spike on the 20th moves no monthly measure (1e-12)."""
    days = pd.bdate_range("2021-01-01", "2024-03-29")
    rng = np.random.default_rng(0)
    daily = pd.DataFrame(
        {"A": rng.normal(size=len(days)), "B": rng.normal(size=len(days))}, index=days
    )
    spiked = daily.copy()
    spiked.loc["2024-02-20"] = [1000.0, 1000.0]
    cfg = construct_config.load()
    values = []
    for frame in (daily, spiked):
        data = {
            "daily": frame,
            "monthly": matrix.monthly(frame),
            "manifest": {"calendar": {"build": ["2021-01-01", "2024-02-15"]}},
        }
        universe.screen(data, cfg, tmp_path)
        pairs = pd.read_parquet(tmp_path / "pairs.parquet").set_index("measure")[
            "value"
        ]
        values.append(pairs[["pearson_monthly", "spearman_monthly"]].to_numpy())
    assert np.abs(values[0] - values[1]).max() < 1e-12, values
    with pytest.raises(TypeError):  # a month label cannot be cut at a day
        matrix.segment(matrix.monthly(daily), {"build": (days[0], days[-1])}, "build")


def test_stage_b_reports_the_winner_on_fresh_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """m35: on clones (one true P(pass)) the reported figure matches an independent re-draw within 0.008."""
    cfg = small_cfg(shortlist_size=8, max_shared=1.0)
    plan = lenient_plan(target=0.04, max_loss=0.10, phases=2, daily_loss=0.05)
    world = complete(
        bar_world(41, 6, "2021-01-04", "2022-01-01", clones=True),
        plan,
        cfg,
        {"build": BUILD},
    )
    data = funded_b._prepare(world, world["identities"], BUILD, cfg)
    monkeypatch.setattr(funded_b, "_prepare", lambda *a: data)
    selector, reported, again = [], [], []
    for seed in range(30):
        w = funded_b.build(world, cfg, np.random.default_rng(seed))["stage_b"]["winner"]
        selector.append(w["p"])
        reported.append(w["p_fresh"])
        again.append(
            stageb.stability(
                data,
                stageb_run.rows_of(data, w["members"]),
                plan,
                cfg,
                stageb_run.risk_of(w, plan),
                np.random.default_rng(10_000 + seed),
            )["mean"]
        )
    selector, reported, again = map(np.array, (selector, reported, again))
    assert abs((reported - again).mean()) < 0.008, (
        reported - again
    ).mean()  # ~3 MC standard errors
    assert (selector - again).mean() > 0.015, (
        selector - again
    ).mean()  # what `p` alone would report


def test_haircut_refuses_a_path_set_that_never_closes() -> None:
    """m36: no closed day is no edge to cut — an error, never NaN over every path."""
    flat = {k: v[None, :] for k, v in _days(5).items()}
    with pytest.raises(ValueError):
        haircut.apply(flat, 0.5)


def test_scores_of_a_loser_and_of_no_drawdown() -> None:
    """m36: net -1,000 with net_5 -2,000 scores B's kept-profit term 0; a zero drawdown is the widest margin."""
    cfg = mc_config.load()
    s = cfg["scoring"]
    result = {
        "observed": {"net": -1000.0},
        "A": {
            "inflation": s["dd_inflation_flag"],
            "dd_pct_99": 0.0,
            "runs": {mc_config.HEADLINE: {"ret_dd": {"p": {5: 0.0}}}},
        },
        "B": {
            "net_5": -2000.0,
            "pf_5": s["min_pf"],
            "outlier": {"share": cfg["family_b"]["outlier_frac"]},
        },
        "C": {"skip": {"keep": 1.0}, "fill_degrade": {"keep": 1.0}},
        "D": {
            "overlapping": [{"net_5": 1.0}],
            "nonoverlapping": [{"pf_5": 1.4}],
            "regime": {"buckets": {"high": {"pf_5": 1.4}}},
        },
        "E": {"psr": cfg["family_e"]["psr_target"]},
    }
    got = scoring.subscores(result, cfg)
    assert got["B"] == 0.0 and abs(got["A"] - 100 / 3) < 0.06, got


def test_concentration_needs_a_profit() -> None:
    """m36: one tercile's share of a profit; with a total of zero or below there is none to share."""
    assert family_d.concentration([50.0, 30.0, 20.0], 100.0) == 0.5
    assert np.isnan(family_d.concentration([30.0, -50.0, -100.0], -120.0))
    assert np.isnan(family_d.concentration([10.0, -5.0, -5.0], 0.0))

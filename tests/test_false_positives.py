#!/usr/bin/env python3
"""Known answers for the monkeys-through-the-chain control: on a price that climbs in a straight
line a monkey that keeps its donor's holds and sizes earns exactly what the donor earned; a
hand-built population walks criteria.yaml's steps to a funnel counted by hand; and on a random
walk the null population crosses R3 a little under the normal's 5 % and a planted Sharpe of 0.15
on 196 trades a little under its 67 %; once a cost is charged the null population crosses less
and the planted one the same 62 %, because the edge is planted NET of costs; and the study end
to end on six synthetic donors."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fanout
from engines.nulls import inputs as null_inputs
from pipeline.autopilot import judge
from studies.screening.falsePositives import chain, inputs as fp_inputs, many, model
from studies.screening.gate import inputs as gate_inputs
from studies.screening.analysis import resample as RESAMPLE

VALUE, COST, STEP = 100.0, 5.0, 0.01     # $ per point per lot, $ per trade, price per bar
FREE = {"point_value": VALUE, "tick_size": 1e-6, "spread": 0.0, "slippage": 0.0,
        "commission_method": "SizeBased", "commission": 0.0, "swap_long": 0.0,
        "swap_short": 0.0, "triple": 2, "rollover": 0}
R3, N_OOS = "gate.scorecard.drift_excess_t", 196


def ramp() -> pd.DataFrame:
    """Hourly bars from 2010 to 2015 whose open climbs STEP a bar."""
    index = pd.date_range("2010-01-04", "2015-12-31", freq="h")
    index = index[index.dayofweek < 5]
    open_ = 1000.0 + STEP * np.arange(len(index))
    return pd.DataFrame({"Open": open_, "High": open_ + 0.004, "Low": open_ - 0.004,
                         "Close": open_ + 0.002}, index=index)


def walk() -> pd.DataFrame:
    """The same grid on a driftless Gaussian walk: no entry rule has an edge on it."""
    bars, rng = ramp(), np.random.default_rng(11)
    open_ = 5000.0 + np.cumsum(rng.normal(0.0, 1.0, len(bars)))
    close = np.r_[open_[1:], open_[-1]]
    return bars.assign(Open=open_, Close=close, High=np.maximum(open_, close) + 0.3,
                       Low=np.minimum(open_, close) - 0.3)


def donor(bars: pd.DataFrame, n_oos: int = 150, longest: int = 40, seed: int = 3) -> pd.DataFrame:
    """A long strategy filled at the open: 300 trades in sample (2010-2012), n_oos out
    (2013-2015), each held under `longest` bars."""
    rng, parts = np.random.default_rng(seed), []
    for sample, n, first, last in (("IS", 300, "2010", "2012"), ("OOS", n_oos, "2013", "2015")):
        lo, hi = bars.index.slice_indexer(first, last).indices(len(bars))[:2]
        entry = np.sort(rng.choice(np.arange(lo + 50, hi - 50), n, replace=False))
        hold, size = rng.integers(1, longest, n), rng.uniform(0.5, 2.0, n).round(2)
        open_px, close_px = bars["Open"].to_numpy()[entry], bars["Open"].to_numpy()[entry + hold]
        parts.append(pd.DataFrame({
            "identity": f"donor{seed}" if seed != 3 else "donor", "sample": sample, "Type": "Buy", "Size": size,
            "Open time": bars.index[entry], "Close time": bars.index[entry + hold],
            "Open price": open_px, "Close price": close_px,
            "Profit/Loss": VALUE * size * (close_px - open_px) - COST, "MAE ($)": 0.0}))
    return pd.concat(parts, ignore_index=True)


def test_the_donor_monkeys_stream_is_not_the_resampling_stream() -> None:
    """numpy pads [seed, k] to [seed, k, 0]: without the tag a pinned seed would hand level 3a/b's draws to the donors."""
    from engines.nulls import simulate
    mine = np.random.default_rng([1, simulate._stable("k"), model.TAG, 0]).random(4)
    assert model.TAG != simulate.TAG and not np.array_equal(mine, RESAMPLE.stream(1, "k").random(4))


def test_a_timing_monkey_on_a_straight_line_earns_what_its_donor_earned() -> None:
    """Price gains STEP per bar whenever it is entered, so moving a trade changes nothing: every
    monkey's net is the donor's, per sample. Its worst price while held is the first bar's low,
    0.004 under the entry."""
    bars, own = ramp(), donor(ramp())
    drawn, corr = model.monkeys(own, bars, null_inputs.config(["nulls.seed=1"]),
                                {"rung": "timing", "sizing": "donor", "per_donor": 7}, "donor")
    assert corr > 0.9999
    assert drawn["identity"].nunique() == 7 and len(drawn) == 7 * len(own)
    assert not drawn["Open time"].isin(own["Open time"]).all()          # they did move
    for sample in model.SAMPLES:
        mine = drawn[drawn["sample"] == sample]
        real = own.loc[own["sample"] == sample, "Profit/Loss"].sum()
        assert np.allclose(mine.groupby("identity")["Profit/Loss"].sum(), real, atol=1e-6)
        inside = own[own["sample"] == sample]
        assert mine["Open time"].min() >= inside["Open time"].min()
        assert mine["Close time"].max() <= inside["Close time"].max()
    assert np.allclose(drawn["MAE ($)"], -VALUE * drawn["Size"] * 0.004, atol=1e-6)


def staged(bars: pd.DataFrame, costs: dict) -> tuple[dict, dict]:
    """What a staged harvest shares with its monkeys, and the gate's config at few draws."""
    real = {"bars": bars, "split": "2013-01-01", "end": "2015-12-31", "costs": costs,
            "costs_build": costs,
            "market": {"point_value": VALUE, "risk": 500.0, "years": {"IS": 3.0, "OOS": 3.0},
                       "windows": {"IS": ("2010", "2012"), "OOS": ("2013", "2015")}}}
    cfg = gate_inputs.config(["monkey.draws=100", "homogeneity.permutations=100",
                              "drawdown.sequences=100"])
    for block in ("monkey", "homogeneity", "drawdown"):
        cfg[block]["seed"] = 5
    return real, cfg


def crossing(costs: dict, monkeys: int, longest: int = 6) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The whole chain, cascade off, over one donor's `free` monkeys on the random walk: the
    null population's facts and the same monkeys' with a Sharpe of 0.15 planted."""
    bars = walk()
    own = donor(bars, N_OOS, longest)
    drawn, corr = model.monkeys(own, bars, null_inputs.config(["nulls.seed=1"]),
                                {"rung": "free", "sizing": "atr", "per_donor": monkeys}, "donor")
    assert corr > 0.9999
    real, cfg = staged(bars, costs)
    harvest = chain.as_harvest(drawn, real)
    return chain.facts8(harvest, cfg), chain.facts8(harvest, cfg, 0.15)


def test_r3_lets_through_the_line_s_own_rate_and_keeps_a_planted_edge() -> None:
    """No costs (the repricer charges nothing, so net is gross), trades short and sparse. The
    convention: the gate's t (R3) of the oos1 excess, pass at >= 1.65. The plain t would
    clear 1.65 at the normal's 4.95 %, and with a Sharpe of 0.15 per trade on 196 trades, which
    lifts it by 0.15 x 14 = 2.1, at P(z >= -0.45) = 67 %. The gate's t is that one at the AR(1)
    effective n, which only ever shrinks it, over the skewness-and-kurtosis error: 🔬 4.1 % and
    62 % here, the lift 2.02. The edge reaches every later reader: the net of oos1 (level 0),
    the monkey's z, which rises by the whole 2.1, and the one-bar delay, which keeps it (🔬
    holds of 1 to 5 bars: median retention 0.81, 2.6 % Fail)."""
    fanout.CORES = min(fanout.CORES, 4)
    null, edge = crossing(FREE, 1000)
    scored = "gate.scorecard."
    assert len(null) == 1000 and (null[scored + "sanidad_value"] == N_OOS).all()
    assert 0.025 <= (null[R3] >= 1.65).mean() <= 0.06
    assert 0.59 <= (edge[R3] >= 1.65).mean() <= 0.69
    assert 1.9 < (edge[R3] - null[R3]).mean() < 0.15 * N_OOS ** 0.5
    assert abs((edge[scored + "z_mono"] - null[scored + "z_mono"]).mean() - 2.1) < 0.1
    assert (edge[scored + "estaticas_value"] > null[scored + "estaticas_value"]).all()
    kept, slower = edge[scored + "retraso_ret_min"], edge[scored + "retraso_t_delta"]
    assert 0.6 < kept.median() < 1.1 and ((kept < 0.25) & (slower > 1.65)).mean() < 0.05
    assert slower.median() < 1.0        # original minus moved carries no plant (9.2 if it did)
    for fact in ("z_frec", "t_b", "q_p", "dd_p", "mae_p95_r", "t_sin_3_mejores"):
        assert null[scored + fact].notna().all(), fact


def test_a_planted_edge_is_net_of_costs_and_the_null_monkey_still_pays() -> None:
    """A spread worth 0.83 of t is charged. The null population pays it and crosses R3 less (🔬
    0.9 % of 1,000, against 4.1 % free). The planted one is a NET Sharpe of 0.15 (owner,
    2026-10-07): each trade gains 0.15 x sd of the excess plus the monkey's mean cost, so its
    gate's t is the free run's — 🔬 mean 1.96 and 62.0 % over 1.65 on 1,000 monkeys, 62.1 % free
    — and the lift over the paying null is the edge's 2.01 plus the cost's 0.78. 400 monkeys
    here: the share's binomial sd is 2.4 points, the bounds are three of them."""
    fanout.CORES = min(fanout.CORES, 4)
    null, edge = crossing({**FREE, "spread": 0.1}, 400)
    assert (null[R3] >= 1.65).mean() < 0.03 and -1.0 < null[R3].mean() < -0.65
    assert 0.55 <= (edge[R3] >= 1.65).mean() <= 0.69
    assert 1.85 < edge[R3].mean() < 0.15 * N_OOS ** 0.5
    assert 2.6 < (edge[R3] - null[R3]).mean() < 3.0


def test_every_population_walks_the_real_criteria_side_by_side() -> None:
    """Six donors, four drawn, ten monkeys each: the null population, the three planted ones on
    the same monkeys, and the real one, each with its funnel row and its counts per rule of the
    autopilot's own step 8. The more edge is planted the more clear R3, and what the donor
    hands down is said in `nota`."""
    fanout.CORES = min(fanout.CORES, 4)
    bars = walk()
    base, cfg = staged(bars, FREE)
    real = chain.as_harvest(pd.concat([donor(bars, N_OOS, 6, seed) for seed in range(20, 26)],
                                      ignore_index=True), base)
    got = many.run({"real": real, "gate_cfg": cfg, "nullcfg": null_inputs.config(["nulls.seed=1"]),
                    "steps": yaml.safe_load(judge.CRITERIA.read_text(encoding="utf-8"))["steps"],
                    "tags": {"H1"}, "batches": 1, "source": {"seed": 1, "frozen": False}},
                   fp_inputs.config(["population.per_level=40", "monkeys.per_donor=10"]))
    first = got["funnel"][got["funnel"]["step"] == "8"].set_index("nivel")
    assert first["n_in"].to_dict() == {"nula": 40, "0.05": 40, "0.10": 40, "0.15": 40, "reales": 6}
    assert (first["applied"] == first["rules"]).all() and not got["skipped"]
    rules = got["rules"][got["rules"]["applied"]]
    r3 = rules[rules["label"].str.startswith("z del mono")].set_index("nivel")["pass"]
    assert r3["nula"] <= r3["0.05"] <= r3["0.10"] <= r3["0.15"] and r3["0.15"] >= 20
    assert (rules[["pass", "limbo", "fail"]].sum(axis=1) == rules["n_in"]).all()
    assert set(got["facts"].index.get_level_values("nivel")) == set(first.index)
    wide = many.shares(got["rules"], list(first.index), "pass")
    assert list(wide.columns) == ["regla", *first.index] and len(wide) == rules["label"].nunique()


def test_the_funnel_of_a_hand_built_population() -> None:
    """Five strategies, two steps. Step 8: `t` fails e (0.5), leaves d in limbo (1.8), and c has
    no `n` fact, which is limbo; the rule on a fact nobody computed is not applied. Step 10 has a
    rule and no facts at all: everyone alive goes on. So 5 → 4 (2 pass, 2 limbo) → 4."""
    facts = pd.DataFrame({"t": [3.0, 2.5, 2.6, 1.8, 0.5], "n": [40, 50, np.nan, 60, 70]},
                         index=list("abcde"))
    steps = {"8": {"segment": "oos1", "rules": [
                 {"fact": "t", "pass": ">= 2.33", "limbo": ">= 1.65",
                  "by": {"H4": {"pass": ">= 2.9"}}},
                 {"fact": "n", "pass": ">= 35"},
                 {"fact": "nobody.computed.this", "pass": "> 0"}]},
             "10": {"rules": [{"fact": "elsewhere", "pass": "> 0"}]},
             "16": {"rules": []}}
    funnel, rules = chain.walk({"8": facts}, list(facts.index), steps, {"H1"})
    assert funnel[["n_in", "pass", "limbo", "n_out", "rules", "applied"]].to_numpy().tolist() == [
        [5, 2, 2, 4, 3, 2], [4, 4, 0, 4, 1, 0], [4, 4, 0, 4, 0, 0]]
    alone = rules.set_index(rules["rule"].map(lambda r: json.loads(r)["fact"]))
    assert alone.loc["t", ["pass", "limbo", "fail"]].tolist() == [3, 1, 1]
    assert alone.loc["n", ["pass", "limbo", "fail"]].tolist() == [4, 1, 0]
    assert (~rules["applied"]).sum() == 2
    assert alone.loc[["t", "n"], "died"].tolist() == [1, 0]      # in order: e falls at `t`
    # `by` is the project's: on H4 the pass line is 2.9, so only a passes and b, c fall to limbo.
    funnel, _ = chain.walk({"8": facts}, list(facts.index), steps, {"H4"})
    assert funnel.loc[0, ["pass", "limbo", "n_out"]].tolist() == [1, 3, 4]


if __name__ == "__main__":
    test_a_timing_monkey_on_a_straight_line_earns_what_its_donor_earned()
    test_the_funnel_of_a_hand_built_population()
    test_every_population_walks_the_real_criteria_side_by_side()
    test_r3_lets_through_the_line_s_own_rate_and_keeps_a_planted_edge()
    test_a_planted_edge_is_net_of_costs_and_the_null_monkey_still_pays()
    print("ok")

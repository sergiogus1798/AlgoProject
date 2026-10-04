#!/usr/bin/env python3
"""Known answers for the monkeys-through-the-chain control: on a price that climbs in a straight
line a monkey that keeps its donor's holds and sizes earns exactly what the donor earned, and a
hand-built population walks criteria.yaml's steps to a funnel counted by hand."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.nulls import inputs as null_inputs
from studies.screening.falsePositives import chain, model
from studies.screening.gate import inputs as gate_inputs

VALUE, COST, STEP = 100.0, 5.0, 0.01     # $ per point per lot, $ per trade, price per bar


def ramp() -> pd.DataFrame:
    """Hourly bars from 2010 to 2015 whose open climbs STEP a bar."""
    index = pd.date_range("2010-01-04", "2015-12-31", freq="h")
    index = index[index.dayofweek < 5]
    open_ = 1000.0 + STEP * np.arange(len(index))
    return pd.DataFrame({"Open": open_, "High": open_ + 0.004, "Low": open_ - 0.004,
                         "Close": open_ + 0.002}, index=index)


def donor(bars: pd.DataFrame) -> pd.DataFrame:
    """A long strategy filled at the open: 300 trades in sample (2010-2012), 150 out (2013-2015)."""
    rng, parts = np.random.default_rng(3), []
    for sample, n, first, last in (("IS", 300, "2010", "2012"), ("OOS", 150, "2013", "2015")):
        lo, hi = bars.index.slice_indexer(first, last).indices(len(bars))[:2]
        entry = np.sort(rng.choice(np.arange(lo, hi - 50), n, replace=False))
        hold, size = rng.integers(1, 40, n), rng.uniform(0.5, 2.0, n).round(2)
        open_px, close_px = bars["Open"].to_numpy()[entry], bars["Open"].to_numpy()[entry + hold]
        parts.append(pd.DataFrame({
            "identity": "donor", "sample": sample, "Type": "Buy", "Size": size,
            "Open time": bars.index[entry], "Close time": bars.index[entry + hold],
            "Open price": open_px, "Close price": close_px,
            "Profit/Loss": VALUE * size * (close_px - open_px) - COST, "MAE ($)": 0.0}))
    return pd.concat(parts, ignore_index=True)


def test_a_timing_monkey_on_a_straight_line_earns_what_its_donor_earned() -> None:
    """Price gains STEP per bar whenever it is entered, so moving a trade changes nothing: every
    monkey's net is the donor's, per sample, and through the gate's own `estaticas` too. Its
    worst price while held is the first bar's low, 0.004 under the entry."""
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

    real = {"bars": bars, "split": "2013-01-01", "end": "2015-12-31",
            "market": {"point_value": VALUE, "risk": 500.0, "years": {"IS": 3.0, "OOS": 3.0},
                       "windows": {"IS": ("2010", "2012"), "OOS": ("2013", "2015")}}}
    facts = chain.facts8(chain.as_harvest(drawn, real), gate_inputs.config([]))
    net = own.loc[own["sample"] == "OOS", "Profit/Loss"].sum()
    assert np.allclose(facts["gate.scorecard.estaticas_value"], net, atol=1e-6)
    assert (facts[chain.TRADES_OOS] == 150).all()
    assert (facts["gate.scorecard.oos_trades_per_year"] == 50).all()
    assert np.allclose(facts["gate.scorecard.oos_net_per_year_r"], net / 3 / 500, atol=1e-9)


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
    # `by` is the project's: on H4 the pass line is 2.9, so only a passes and b, c fall to limbo.
    funnel, _ = chain.walk({"8": facts}, list(facts.index), steps, {"H4"})
    assert funnel.loc[0, ["pass", "limbo", "n_out"]].tolist() == [1, 3, 4]


if __name__ == "__main__":
    test_a_timing_monkey_on_a_straight_line_earns_what_its_donor_earned()
    test_the_funnel_of_a_hand_built_population()
    print("ok")

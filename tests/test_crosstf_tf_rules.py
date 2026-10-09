#!/usr/bin/env python3
"""Every row of the tables of §5 and §6 of the step-12 proposal (encargo 47, part K): T0's
reasons, T1, T2a and T2b per sibling, the verdict per mother with two, one and no comparable
neighbour, T3's brake, T4, the population floor, a batch without a cost card, and the seam the
build trades arrive through."""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.transfer.crossTF import inputs as study_inputs
from studies.transfer.crossTF.tf import inputs, rules, run, table

TF = study_inputs.config([])["tf"]
S = pd.Series


def test_t0_reasons() -> None:
    """unverified, then clamped, then a rounding shift over 0.25; 0.25 itself is comparable."""
    made = pd.DataFrame({"unverified": [1, 0, 0, 0, np.nan], "clamped": [1, 1, 0, 0, np.nan],
                         "rounding_shift": [.9, .9, .26, .25, np.nan]})
    assert list(rules.comparable(made, 0.25)) == ["unverified", "clamped", "rounding_shift", "", ""]
    assert list(rules.few(S([29, 30, np.nan]), 30)) == ["few_trades", "", "few_trades"]


def test_sibling_states() -> None:
    """The three per-sibling tables of §5, edge by edge; no data is limbo."""
    assert list(rules.t1(S([0, -1.5, 1.51, -3.5, 3.51, np.nan]), TF["frequency"])) \
        == ["pass", "pass", "limbo", "limbo", "fail", "limbo"]
    assert list(rules.t2a(S([.5, .49, .01, 0, -1, 0, np.nan]), S([9, 9, 9, 1.64, 1.64, 1.65, 9]),
                          TF["retention"])) == ["pass", "limbo", "limbo", "limbo", "limbo", "fail", "limbo"]
    assert list(rules.t2b(S([1.65, 1.64, .01, 0, -2, np.nan]), TF["build"])) \
        == ["pass", "limbo", "limbo", "fail", "fail", "limbo"]


def test_z_frec_by_hand() -> None:
    """ln(90/100) against a population centre of -0.05, phi 2: (ln .9 + .05) / sqrt(2 (1/90 + 1/100))."""
    z = rules.z_frec(S([100.0]), S([90.0]), S([2.0]), S([-0.05]))[0]
    assert abs(z - (np.log(.9) + .05) / np.sqrt(2 * (1 / 90 + 1 / 100))) < 1e-12
    values, pair = S([1., 2, 3, 4, 9, 7]), S(["H1"] * 5 + ["M15"])
    assert list(rules.centre(values, pair, 5).fillna(-1)) == [3, 3, 3, 3, 3, -1]
    assert list(rules.percentile(values, pair, 5).fillna(-1)) == [.2, .4, .6, .8, 1, -1]


def rows(*near: tuple, far: tuple | None = None) -> pd.DataFrame:
    """A mother's siblings: each (t1, t2a, t2b, ret, why) — why "" when measured."""
    out = [{"role": "neighbour", "timeframe": f"N{i}", "t1": a, "t2a": b, "t2b": c, "ret": r,
            "t1_why": w, "t2a_why": w, "t2b_why": w} for i, (a, b, c, r, w) in enumerate(near)]
    if far:
        out.append({"role": "far", "timeframe": "H4", "t1": "pass", "t2a": far[0], "t2b": "pass",
                    "ret": 0.0, "t1_why": far[1], "t2a_why": far[1], "t2b_why": far[1]})
    return pd.DataFrame(out)


def state(*near: tuple, far: tuple | None = None, expected: int = 2) -> dict:
    """§6 over those rows."""
    return rules.mother(rows(*near, far=far), expected, TF["retention"]["low"])


def test_mother_table() -> None:
    """§6, row by row."""
    ok, bad = ("pass", "pass", "pass", .8, ""), ("pass", "fail", "pass", -1.0, "")
    assert state(ok, ok)["state"] == "pass"
    assert state(("fail", "pass", "pass", .8, ""), ok)["state"] == "fail"            # T1, any neighbour
    assert state(("limbo", "pass", "pass", .8, ""), ok)["state"] == "limbo"
    both = state(bad, bad)
    assert (both["t2a"], both["phase1"], both["state"], both["why"]) == ("fail", "fail", "fail",
                                                                         "isolated_peak_oos1")
    assert state(bad, ("pass", "limbo", "pass", .24, ""))["t2a"] == "fail"           # the other under 0.25
    assert state(bad, ("pass", "limbo", "pass", .25, ""))["t2a"] == "limbo"          # holds on one side
    assert state(bad, ok)["state"] == "limbo"
    zero = ("pass", "pass", "fail", .8, "")
    assert state(zero, zero)["state"] == "fail" and state(zero, zero)["why"] == "isolated_peak_build"
    assert state(zero, ok)["state"] == "limbo" and state(zero, zero)["phase1"] == "pass"
    assert state(ok, ("pass", "pass", "limbo", .8, ""))["state"] == "limbo"


def test_far_only_brakes() -> None:
    """T3: a comparable far sibling failing T2a lowers a pass to limbo, and does nothing else."""
    ok, bad = ("pass", "pass", "pass", .8, ""), ("pass", "fail", "pass", -1.0, "")
    got = state(ok, ok, far=("fail", ""))
    assert (got["t3"], got["phase1"], got["state"], got["why"]) == ("limbo", "limbo", "limbo", "far_brakes")
    assert state(ok, ok, far=("fail", "clamped"))["state"] == "pass"                  # not comparable
    assert state(ok, ok, far=("limbo", ""))["state"] == "pass"
    assert state(bad, bad, far=("fail", ""))["state"] == "fail"


def test_fewer_comparable_neighbours() -> None:
    """One comparable neighbour caps at limbo; none is limbo; T1 still fails on the one there
    is. The lone neighbour failing T2a or T2b is the undecided reading: limbo, and named."""
    ok, out = ("pass", "pass", "pass", .8, ""), ("limbo", "limbo", "limbo", np.nan, "clamped")
    one = state(ok, out)
    assert one["state"] == "limbo" and "N1:clamped" in one["why"]
    assert state(out, out)["state"] == "limbo" and state(ok)["state"] == "limbo"
    assert "neighbours=1/2" in state(ok)["why"]
    assert state(("fail", "pass", "pass", .8, ""), out)["state"] == "fail"
    lone = state(("pass", "fail", "fail", -1.0, ""), out)
    assert lone["state"] == "limbo" and "t2a_lone_fail" in lone["why"] and "t2b_lone_fail" in lone["why"]
    assert state(ok, ok, expected=0)["state"] == "limbo"                              # a timeframe with no neighbours


def test_overlap() -> None:
    """T4: entries under one mother bar from one of hers, either side; exactly one bar is not."""
    hers = np.array(["2020-01-01T10:00", "2020-01-02T10:00"], "datetime64[s]")
    mine = np.array(["2020-01-01T10:29", "2020-01-01T09:31", "2020-01-01T10:30", "2020-01-03"], "datetime64[s]")
    assert rules.overlap(hers, mine, 1800) == 0.5
    assert np.isnan(rules.overlap(hers[:0], mine, 1800))


def measured() -> pd.DataFrame:
    """Six mothers' H1 siblings measured, all alike, and one M15 sibling on her own."""
    made = pd.DataFrame({"mother": [f"S{i}" for i in range(6)] + ["S0"], "timeframe": ["H1"] * 6 + ["M15"],
                         "ratio": 2.0, "rounding_shift": 0.0, "clamped": 0.0, "unverified": 0.0})
    t = table.blank(made.assign(sibling=made["mother"] + "_" + made["timeframe"]))
    return t.assign(n_oos1=100., n_mother_oos1=110., e_oos1=.1, e_mother_oos1=.2, z_delta=1.0,
                    n_build=200., n_mother_build=220., e_build=.1, e_mother_build=.3, z_build=2.0, phi=2.0)


def test_judge() -> None:
    """The table judged: columns as declared, T1 centred on the batch, the population floor,
    fewer than 30 trades, a mother with no edge, no build, and a batch with no cost card."""
    got = table.judge(measured(), TF, "M30")
    assert list(got.columns) == table.SIBLINGS
    h1, m15 = got.iloc[0], got.iloc[6]
    assert (h1["role"], h1["ret"], h1["t2a"], h1["t2b"], h1["z_frec"], h1["t1"]) == ("neighbour", .5, "pass", "pass", 0, "pass")
    assert abs(h1["ret_build"] - 1 / 3) < 1e-12 and 0 < h1["ret_build_pct"] <= 1
    assert (m15["t1_why"], m15["t1"]) == ("population_below_min", "limbo") and np.isnan(m15["ret_build_pct"])
    low = table.judge(measured().assign(n_oos1=29.), TF, "M30").iloc[0]
    assert (low["t2a_why"], low["t2a"], low["t2b_why"]) == ("few_trades", "limbo", "")
    flat = table.judge(measured().assign(e_mother_oos1=0.), TF, "M30").iloc[0]
    assert flat["t2a_why"] == "mother_e_not_positive" and np.isnan(flat["ret"])
    odd = table.judge(measured().assign(rounding_shift=.3), TF, "M30").iloc[0]
    assert (odd["t0"], odd["t1_why"], odd["t2a_why"], odd["t2b_why"]) == ("rounding_shift",) * 4
    none = table.judge(measured().assign(n_build=np.nan, z_build=np.nan), TF, "M30").iloc[0]
    assert (none["t1_why"], none["t2b_why"], none["t2a"]) == ("no_build_data", "no_build_data", "pass")
    assert table.judge(measured(), TF, "H1").iloc[0]["role"] == "note"      # H1 is no neighbour of an H1 mother
    both = run.read(measured().drop(columns=table.MEASURED), {}, {}, None, None, {}, TF, "M30",
                    {"S0": "abc"}, "no_cost_card")
    assert (both["siblings"][["t1_why", "t2a_why", "t2b_why"]] == "no_cost_card").all(axis=None)
    assert both["siblings"][table.MEASURED].isna().all(axis=None)           # a reason, never a 0
    assert (both["mothers"]["state"] == "limbo").all() and list(both["mothers"].columns) == table.MOTHERS
    assert both["mothers"]["identity"][0] == "abc" and set(both["mothers"]["state"]) <= set(rules.RANK)


def test_build_seam() -> None:
    """A batch without phase 2 gives no build trades, not an exception; one with it is read from
    the databanks `blocks.json` names, the mothers from the harvest by identity."""
    with tempfile.TemporaryDirectory() as tmp:
        batch, raw = Path(tmp) / "batch", Path(tmp) / "raw" / "Test_P"
        export = raw / "CrossTF" / "2026-10-07" / "trades.parquet"
        batch.mkdir()
        made = pd.DataFrame({"sibling": ["S0_H1", "S0_H4"], "timeframe": ["H1", "H4"]})
        assert inputs.build_banks(batch) == {} and inputs.build(export, batch, {}, made) is None
        (batch / "blocks.json").write_text(json.dumps({"blocks": ["M30", "H1"]}))
        assert inputs.build(export, batch, {}, made) is None                        # a project made before phase 2
        (batch / "blocks.json").write_text(json.dumps({"build_databanks": {"H1": "CrossTF H1 Build"}}))
        assert inputs.build(export, batch, {}, made) is None                        # named, not exported yet
        day = raw / "CrossTF_H1_Build" / "2026-10-06"
        day.mkdir(parents=True)
        # SQX retests every strategy in every phase-2 databank: only the sibling of that timeframe counts
        trades = pd.DataFrame({"strategy": pd.Categorical(["S0_H1", "S0_H4", "S0"]), "Open time": pd.Timestamp("2015-01-05"),
                               "Close time": pd.Timestamp("2015-01-06"), "Type": "Buy", "block": 0})
        trades.to_parquet(day / "trades.parquet")
        got = inputs.build(export, batch, {}, made)
        assert list(got.columns) == inputs.KEEP and list(got["strategy"]) == ["S0_H1"]


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("ok: T0-T4, el veredicto por madre y la costura del build")

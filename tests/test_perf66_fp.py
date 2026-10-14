#!/usr/bin/env python3
"""Encargo 66 §2 and §3.1: the false-positive control does the same maths in a fraction of the work.
The oracle is the control as it was (every pass alone, every rung, nothing cached): the shared
passes give its facts bit for bit, except the three rung columns nobody judges, which are empty;
the funnel and the rules, which are what the owner reads, do not move; the answer does not depend
on the number of workers; level 3c's real-gate rows keep the histogram and drop the raw draws."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_false_positives as base  # noqa: E402
from core import fanout  # noqa: E402
from core.study import draws  # noqa: E402
from engines.nulls import inputs as null_inputs  # noqa: E402
from pipeline.autopilot import judge  # noqa: E402
from studies.screening.analysis import delay  # noqa: E402
from studies.screening.falsePositives import chain, inputs as fp_inputs, many  # noqa: E402
from studies.screening.gate import cascade, inputs as gate_inputs, level1a, level2, level3ab, level3c, measures  # noqa: E402
from studies.screening.gate.levels import LEVELS  # noqa: E402

EDGES = (0.0, 0.05, 0.10, 0.15)
SCORED = "gate.scorecard."
UNJUDGED = [SCORED + f"z_mono_{rung}" for rung in ("timing_sizing", "timing_holds", "free")]


def inputs() -> dict:
    """Six synthetic donors, the real population, at 100 draws and a fixed seed."""
    bars = base.walk()
    real, cfg = base.staged(bars, base.FREE)
    real = chain.as_harvest(pd.concat([base.donor(bars, base.N_OOS, 6, seed) for seed in range(20, 26)],
                                      ignore_index=True), real)
    return {"real": real, "gate_cfg": cfg, "nullcfg": null_inputs.config(["nulls.seed=1"]),
            "steps": yaml.safe_load(judge.CRITERIA.read_text(encoding="utf-8"))["steps"],
            "tags": {"H1"}, "batches": 1, "source": {"seed": 1, "frozen": False}}


def old_facts8(data: dict, cfg: dict, edge: float) -> pd.DataFrame:
    """chain.facts8 before encargo 66: one pass alone, every rung, nothing taken from another pass."""
    everyone = cascade.population(data).index
    scores = pd.DataFrame(index=everyone)
    with tempfile.TemporaryDirectory() as tmp:
        data = {**data, "out": Path(tmp)}
        for _, module in LEVELS:
            if module is level3ab:
                data["build"] = gate_inputs.build_pnl(data, everyone)
            got = module.run(data, everyone, cfg)
            if edge and module is level1a:
                got, share = chain._plant(data, scores, edge, cfg)
            if edge and module is level2:
                got = chain._delayed(data, got, everyone, cfg, share, None)
            scores = scores.join(got.reindex(everyone).astype(float))
    return scores.join(measures.table(data).astype(float)).add_prefix(cascade.PREFIX)


@pytest.fixture
def workers(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> int:
    """Set the fan-out core count to the parameter."""
    monkeypatch.setattr(fanout, "CORES", request.param)
    return request.param


@pytest.mark.parametrize(("workers", "order"), [(1, EDGES), (2, EDGES[::-1]), (4, EDGES)], indirect=["workers"])
def test_shared_passes_give_the_old_facts_funnel_and_rules(workers: int, order: tuple) -> None:
    """2A-2E on four passes: facts bit for bit but the unjudged rungs, funnel and rules whole."""
    given = inputs()
    harvest = chain.as_harvest(many.population(given, fp_inputs.config(
        ["population.per_level=40", "monkeys.per_donor=10"]))[0], given["real"])
    got = chain.facts_edges(harvest, given["gate_cfg"], order)
    for edge in EDGES:
        old, new = old_facts8(harvest, given["gate_cfg"], edge), got[edge]
        assert new[UNJUDGED].isna().all(axis=None) and old[UNJUDGED].notna().all(axis=None)
        pd.testing.assert_frame_equal(new.drop(columns=UNJUDGED), old.drop(columns=UNJUDGED), check_exact=True)
        walked = [chain.walk({"8": f}, list(f.index), given["steps"], given["tags"]) for f in (old, new)]
        for i in (0, 1):
            pd.testing.assert_frame_equal(walked[0][i], walked[1][i], check_exact=True)


def test_odd_monkeys_give_the_old_facts() -> None:
    """A one-trade monkey (its planted `add` is NaN), one whose variants drop trades, one without a build."""
    given, bars = inputs(), base.walk()
    lone = base.donor(bars, base.N_OOS, 6, 31)
    lone = lone[(lone["sample"] == "IS") | (lone.index == lone[lone["sample"] == "OOS"].index[0])]
    unbuilt = base.donor(bars, base.N_OOS, 6, 33)
    trades = pd.concat([base.donor(bars, base.N_OOS, 6, 30), lone, base.donor(bars, base.N_OOS, 3, 32),
                        unbuilt[unbuilt["sample"] == "OOS"]], ignore_index=True)
    harvest = chain.as_harvest(trades, given["real"])
    got = chain.facts_edges(harvest, given["gate_cfg"], (0.0, 0.1))
    for edge in (0.0, 0.1):
        old = old_facts8(harvest, given["gate_cfg"], edge)
        pd.testing.assert_frame_equal(got[edge].drop(columns=UNJUDGED), old.drop(columns=UNJUDGED), check_exact=True)


def test_many_run_does_not_depend_on_the_workers(monkeypatch: pytest.MonkeyPatch) -> None:
    """The whole study with 1, 2 and 4 workers: same facts, funnel and rules, bit for bit."""
    cfg = fp_inputs.config(["population.per_level=40", "monkeys.per_donor=10"])
    seen = []
    for n in (1, 2, 4):
        monkeypatch.setattr(fanout, "CORES", n)
        got = many.run(inputs(), cfg)
        seen.append({k: got[k] for k in ("facts", "funnel", "rules")})
    for other in seen[1:]:
        for key in seen[0]:
            pd.testing.assert_frame_equal(seen[0][key], other[key], check_exact=True)


def test_the_moved_excess_of_a_planted_table_is_the_bare_one() -> None:
    """2D2: delay.measure takes the moved excess of another copy of the same trades, and gives the same table."""
    given = inputs()
    data = {**given["real"], "out": Path(tempfile.mkdtemp())}
    cfg = given["gate_cfg"]
    level1a.run(data, cascade.population(data).index, cfg)
    bare, plain = data["oos"], {}
    planted = bare.assign(pnl=bare["pnl"] + 1.7, excess=bare["excess"] + 1.7)
    args = (data["bars"], data["market"]["windows"]["OOS"], data["costs"], cfg["drift"], cfg["delay"]["variants"])
    delay.measure(bare, *args, moved=plain)
    assert sorted(plain) == sorted(cfg["delay"]["variants"])
    pd.testing.assert_frame_equal(delay.measure(planted, *args, moved=plain), delay.measure(planted, *args),
                                  check_exact=True)


def test_level3ab_does_not_depend_on_the_workers_and_keeps_its_q(monkeypatch: pytest.MonkeyPatch) -> None:
    """2B and 3.4c: one root drawn in the parent, so 1 and 4 workers agree; a given q_p is taken as is."""
    given = inputs()
    harvest = chain.as_harvest(many.population(given, fp_inputs.config(
        ["population.per_level=20", "monkeys.per_donor=5"]))[0], given["real"])
    cfg, everyone, out = given["gate_cfg"], cascade.population(harvest).index, Path(tempfile.mkdtemp())
    data = {**harvest, "out": out}
    level1a.run(data, everyone, cfg)
    data["build"] = gate_inputs.build_pnl(data, everyone)
    cfg["homogeneity"]["seed"] = cfg["drawdown"]["seed"] = None            # a fresh root each call, drawn in the parent
    runs = []
    for n in (1, 4):
        monkeypatch.setattr(fanout, "CORES", n)
        runs.append(level3ab.run({**data, "keep_draws": n == 1}, everyone, cfg))
    assert runs[0]["q_seed"].iloc[0] != runs[1]["q_seed"].iloc[0]            # roots differ, as asked
    assert all(r[c].nunique() == 1 for r in runs for c in ("q_seed", "dd_seed"))   # one root across a run's workers
    cfg["homogeneity"]["seed"] = cfg["drawdown"]["seed"] = 7
    one = level3ab.run(data, everyone, cfg)
    monkeypatch.setattr(fanout, "CORES", 4)
    pd.testing.assert_frame_equal(one, level3ab.run(data, everyone, cfg), check_exact=True)
    pd.testing.assert_frame_equal(one, level3ab.run({**data, "q_p": one["q_p"], "keep_draws": False}, everyone, cfg),
                                  check_exact=True)
    assert set(draws.read(out)["test"]) == {"gate.3a", "gate.3b"}        # the one with keep_draws left them


def test_the_real_gate_keeps_the_histogram_and_not_the_raw_draws(monkeypatch: pytest.MonkeyPatch) -> None:
    """3.1: level 3c's rows have counts, tails, n_ge, n_le; `draws` is empty; z and p are readable from them."""
    monkeypatch.setattr(fanout, "CORES", 2)
    given = inputs()
    out, cfg, everyone = Path(tempfile.mkdtemp()), given["gate_cfg"], cascade.population(given["real"]).index
    data = {**given["real"], "out": out}
    level1a.run(data, everyone, cfg)
    facts = level3c.run(data, everyone, cfg)
    rows = draws.read(out)
    assert set(rows["test"]) == {"gate.3c"} and len(rows) == 4 * len(everyone)
    assert all(len(d) == 0 for d in rows["draws"]) and all(sum(c) == cfg["monkey"]["draws"] for c in rows["counts"])
    head = rows[rows["metric"] == "z_mono_timing"].set_index("identity")
    assert ((1 + head["n_ge"]) / (cfg["monkey"]["draws"] + 1)).reindex(facts.index).equals(facts["mono_p"])

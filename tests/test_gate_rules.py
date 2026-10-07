#!/usr/bin/env python3
"""The 16 rules of the new step-8 gate (encargo 44 §1.2), each against a hand truth table read
through the judge's own `pipeline.autopilot.criteria`, and the contract that every fact a rule
names is declared by a level of the gate."""

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria
from studies.screening.gate import levels

CRITERIA = Path(__file__).resolve().parent.parent / "pipeline" / "autopilot" / "criteria.yaml"
RULES = yaml.safe_load(CRITERIA.read_text(encoding="utf-8"))["steps"]["8"]["rules"]
PREFIX = "gate.scorecard."
P, L, F = "pass", "limbo", "fail"

# The facts a rule reads → its cases: one value per fact in that order (None = the fact is
# missing), then the verdict.
TABLES = {
    "presencia_passed": [(1, P), (0, F), (None, F)],                                  # R1a
    "sanidad_passed": [(1, P), (0, F), (None, F)],                                    # R1b
    "estaticas_value": [(5, P), (0, F), (-3, F), (None, L)],                          # R2
    "is_trades_per_year": [(35, P), (34.9, L), (20, L), (19.9, F), (None, L)],        # R4a
    "sanidad_value": [(100, P), (99, L), (0, L), (None, L)],                          # R5b
    "drift_excess_t": [(1.65, P), (1.64, F), (-2, F), (None, F)],                     # R3
    "z_frec": [(0, P), (1.5, P), (-1.5, P), (1.51, L), (3.5, L), (-3.5, L), (3.51, F),
               (-3.51, F), (None, L)],                                                # R5
    "edge_mean_oos t_exceso_k": [(2, 1.65, P), (2, 1.64, L), (1.99, 3, L), (1.25, 3, L),
                                 (1.24, 3, F), (1.24, 0, F), (None, 3, L), (3, None, L),
                                 (1, None, F), (None, None, L)],                      # R5c
    "t_b e_fin": [(-1.65, -5, P), (0, None, P), (-1.66, 0.1, L), (-1.66, 0, F), (-2, -1, F),
                  (None, 1, L), (None, -1, L), (-2, None, L), (None, None, L)],       # R5d
    "t_sin_mejor_trimestre t_sin_3_mejores": [
        (1.65, 1.65, P), (1.65, 1.64, L), (0.01, 3, L), (0, 3, F), (2, -1, F), (None, 2, L),
        (None, 0, F), (None, None, L)],                                               # R8
    "mae_p95_r": [(1.5, P), (1.51, L), (2.5, L), (2.51, F), (None, L)],               # R9b
    "ret_datos t_a n_afectadas": [
        (0.6, 5, 10, P), (0.1, 5, 0, P), (None, None, 0, P), (0.59, 5, 10, L),
        (0.25, 5, 10, L), (0.24, 1.65, 10, L), (0.24, 1.66, 10, F), (0.24, 1.66, None, L),
        (None, None, 10, L), (0.24, None, 10, L), (None, None, None, L)],             # data
    "retraso_ret_min retraso_t_delta": [
        (0.6, 9, P), (0.9, None, P), (0.59, 9, L), (0.25, 9, L), (0.24, 1.65, L),
        (0.24, 1.66, F), (None, 9, L), (0.24, None, L), (None, None, L)],             # delay
    "q_p": [(0.051, P), (0.05, L), (0, L), (None, L)],                                # R7
    "dd_p": [(0.11, P), (0.10, L), (0.011, L), (0.01, F), (None, L)],                 # R6
    "z_mono": [(1.65, P), (1.64, L), (-3, L), (None, L)],                             # mono
}


def verdict(key: str, values: tuple, tags: set[str]) -> str:
    """What the step-8 rules that read exactly the facts of `key` say of one strategy."""
    names = [PREFIX + name for name in key.split()]
    rules = [r for r in RULES if criteria.reads([r]) == set(names)]
    rows = [("s", n, float(v)) for n, v in zip(names, values, strict=True) if v is not None]
    facts = pd.DataFrame(rows + [("other", "x", 0.0)], columns=["who", "key", "value"])
    return criteria.outcomes(facts, ["s"], criteria.resolved(rules, tags))["s"][0]


def test_sixteen_rules_and_every_one_has_its_table() -> None:
    """Step 8 of criteria.yaml groups into the 16 rules of §1.2 (R5 is two one-sided lines), each with a
    table that holds a Pass, a missing fact, and the Limbo and the Fail the rule can give."""
    groups = {frozenset(criteria.reads([r])) for r in RULES}
    assert len(groups) == 16 and len(RULES) == 17, (len(groups), len(RULES))
    assert groups == {frozenset(PREFIX + n for n in key.split()) for key in TABLES}
    no_limbo = {"presencia_passed", "sanidad_passed", "estaticas_value", "drift_excess_t"}
    no_fail = {"sanidad_value", "q_p", "z_mono"}
    for key, cases in TABLES.items():
        seen = {case[-1] for case in cases if None not in case[:-1]}
        assert seen == {P, L, F} - ({L} if key in no_limbo else set()) - (
            {F} if key in no_fail else set()), (key, seen)
        assert any(all(v is None for v in case[:-1]) for case in cases), key


def test_truth_tables() -> None:
    """Every case of every table, on an H1 project."""
    wrong = [(key, case, got) for key, cases in TABLES.items() for case in cases
             if (got := verdict(key, case[:-1], {"H1"})) != case[-1]]
    assert not wrong, wrong


def test_timeframe_exceptions() -> None:
    """R4a's limbo starts at 15 on H4; R3 has no exception: 1.65 on H1 and on H4 alike."""
    assert verdict("is_trades_per_year", (15,), {"H4"}) == L
    assert verdict("is_trades_per_year", (14.9,), {"H4"}) == F
    assert verdict("is_trades_per_year", (19.9,), {"H4"}) == L
    assert [verdict("drift_excess_t", (1.7,), {t}) for t in ("H1", "H4")] == [P, P]
    assert not any("by" in r or "limbo" in r for r in RULES
                   if r.get("fact") == PREFIX + "drift_excess_t")


def test_levels_declare_every_fact_the_rules_name() -> None:
    """A misnamed fact does not fail, it reads as Limbo: so the names are tied here. Every
    level is a module with `FACTS` and `run(data, alive, cfg)` returning those columns."""
    declared = {PREFIX + fact for fact in levels.facts()}
    assert criteria.reads(RULES) <= declared, criteria.reads(RULES) - declared
    alive = pd.Index(["a", "b"])
    for _, module in levels.LEVELS:
        frame = module.run({}, alive, {})
        assert list(frame.columns) == list(module.FACTS) and frame.index.equals(alive)
    assert {"q_seed", "dd_seed", "mono_seed"} <= set(levels.facts())


if __name__ == "__main__":
    test_sixteen_rules_and_every_one_has_its_table()
    test_truth_tables()
    test_timeframe_exceptions()
    test_levels_declare_every_fact_the_rules_name()
    print("ok: las 16 reglas del paso 8 y los hechos de los niveles")

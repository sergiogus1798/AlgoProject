#!/usr/bin/env python3
"""The 10 rules that judge at step 8 (encargo 44 §1.2, cut down by encargo 65 §5.2), each against a hand truth table read
through the judge's own `pipeline.autopilot.criteria`, and the contract that every fact a rule
names is declared by a level of the gate."""

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria
from studies.screening.gate import levels

CRITERIA = (
    Path(__file__).resolve().parent.parent / "pipeline" / "autopilot" / "criteria.yaml"
)
RULES = yaml.safe_load(CRITERIA.read_text(encoding="utf-8"))["steps"]["8"]["rules"]
PREFIX = "gate.scorecard."
P, L, F = "pass", "limbo", "fail"

# The facts a rule reads → its cases: one value per fact in that order (None = the fact is
# missing), then the verdict.
TABLES = {
    "presencia_passed": [(1, P), (0, F), (None, F)],  # R1a
    "sanidad_passed": [(1, P), (0, F), (None, F)],  # R1b
    "estaticas_value": [(5, P), (0, F), (-3, F), (None, L)],  # R2
    "edge_mean_oos": [
        (2, P),
        (1.99, L),
        (1.25, L),
        (1.24, F),
        (None, L),
    ],  # R5c, cost part
    "t_b e_fin": [
        (-1.65, -5, P),
        (0, None, P),
        (-1.66, 0.1, L),
        (-1.66, 0, F),
        (-2, -1, F),
        (None, 1, L),
        (None, -1, L),
        (-2, None, L),
        (None, None, L),
    ],  # R5d
    "ret_datos t_a n_afectadas": [
        (0.6, 5, 10, P),
        (0.1, 5, 0, P),
        (None, None, 0, P),
        (0.59, 5, 10, L),
        (0.25, 5, 10, L),
        (0.24, 1.65, 10, L),
        (0.24, 1.66, 10, F),
        (0.24, 1.66, None, L),
        (None, None, 10, L),
        (0.24, None, 10, L),
        (None, None, None, L),
    ],  # data
    "retraso_ret_min retraso_t_delta": [
        (0.6, 9, P),
        (0.9, None, P),
        (0.59, 9, L),
        (0.25, 9, L),
        (0.24, 1.65, L),
        (0.24, 1.66, F),
        (None, 9, L),
        (0.24, None, L),
        (None, None, L),
    ],  # delay
    "q_p": [(0.051, P), (0.05, L), (0, L), (None, L)],  # R7
    "dd_p": [(0.11, P), (0.10, L), (0.011, L), (0.01, F), (None, L)],  # R6
    "z_mono": [(1.645, P), (1.644, F), (-3, F), (None, F)],  # the z, B = 1
}


def verdict(key: str, values: tuple, tags: set[str], batches: int = 1) -> str:
    """What the step-8 rules that read exactly the facts of `key` say of one strategy."""
    names = [PREFIX + name for name in key.split()]
    rules = [r for r in RULES if criteria.reads([r]) == set(names)]
    rows = [
        ("s", n, float(v)) for n, v in zip(names, values, strict=True) if v is not None
    ]
    facts = pd.DataFrame(rows + [("other", "x", 0.0)], columns=["who", "key", "value"])
    return criteria.outcomes(
        facts, ["s"], criteria.thresholded(criteria.resolved(rules, tags), batches)
    )["s"][0]


def test_ten_rules_and_every_one_has_its_table() -> None:
    """Step 8 of criteria.yaml groups into the 10 rules that judge (R4a, R5, R5b, R8, R9b, R3 and R5c's t are columns), each with a
    table that holds a Pass, a missing fact, and the Limbo and the Fail the rule can give."""
    groups = {frozenset(criteria.reads([r])) for r in RULES}
    assert len(groups) == 10 and len(RULES) == 10, (len(groups), len(RULES))
    assert groups == {frozenset(PREFIX + n for n in key.split()) for key in TABLES}
    no_limbo = {"presencia_passed", "sanidad_passed", "estaticas_value", "z_mono"}
    no_fail = {"q_p"}
    for key, cases in TABLES.items():
        seen = {case[-1] for case in cases if None not in case[:-1]}
        assert seen == {P, L, F} - ({L} if key in no_limbo else set()) - (
            {F} if key in no_fail else set()
        ), (key, seen)
        assert any(all(v is None for v in case[:-1]) for case in cases), key


def test_truth_tables() -> None:
    """Every case of every table, on an H1 project."""
    wrong = [
        (key, case, got)
        for key, cases in TABLES.items()
        for case in cases
        if (got := verdict(key, case[:-1], {"H1"})) != case[-1]
    ]
    assert not wrong, wrong


def test_the_z_line_is_per_cell() -> None:
    """Known answer: Φ⁻¹(1 − 0.05/B) is 1.645 / 1.960 / 2.241 for B = 1 / 2 / 4, and a strategy at
    z = 1.8 passes with B = 1 and is cut with B = 2. The yaml declares alpha, never a number."""
    rule = next(r for r in RULES if r.get("fact") == PREFIX + "z_mono")
    assert rule["alpha"] == 0.05 and "pass" not in rule and "limbo" not in rule
    assert [round(criteria.threshold(0.05, b), 3) for b in (1, 2, 4)] == [
        1.645,
        1.960,
        2.241,
    ]
    assert (
        verdict("z_mono", (1.8,), {"H1"}, 1) == P
        and verdict("z_mono", (1.8,), {"H1"}, 2) == F
    )
    assert (
        verdict("z_mono", (2.25,), {"H1"}, 4) == P
        and verdict("z_mono", (2.24,), {"H1"}, 4) == F
    )


def test_dropped_rules_stay_out_of_the_judge() -> None:
    """R3, R4a, R5, R5b, R8, R9b and R5c's t are columns now: no rule reads them."""
    columns = {
        "drift_excess_t",
        "is_trades_per_year",
        "z_frec",
        "sanidad_value",
        "t_sin_mejor_trimestre",
        "t_sin_3_mejores",
        "mae_p95_r",
        "t_exceso_k",
    }
    assert not {f.removeprefix(PREFIX) for f in criteria.reads(RULES)} & columns


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
    test_ten_rules_and_every_one_has_its_table()
    test_truth_tables()
    test_the_z_line_is_per_cell()
    test_dropped_rules_stay_out_of_the_judge()
    test_levels_declare_every_fact_the_rules_name()
    print("ok: las 10 reglas que juzgan en el paso 8 y los hechos de los niveles")

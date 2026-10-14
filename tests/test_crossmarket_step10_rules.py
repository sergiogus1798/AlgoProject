#!/usr/bin/env python3
"""Step 10's rules in criteria.yaml (P1-P9, encargo 46), run through the judge's own path
(`criteria.resolved` -> `criteria.outcomes`): each rule's pass / limbo / fail, the P9 compound's
four corners, and a missing fact giving limbo."""

import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria

FILE = (
    Path(__file__).resolve().parent.parent / "pipeline" / "autopilot" / "criteria.yaml"
)
RULES = criteria.resolved(
    yaml.safe_load(FILE.read_text(encoding="utf-8"))["steps"]["10"]["rules"], set()
)
P = "crossmarket.verdict_csv."
# a strategy that passes every rule; each case below changes the facts it names
GOOD = {
    "invalid_fraction": 0.0,
    "fixed_distance": 0.0,
    "freq_off": 0.0,
    "freq_off_fraction": 0.0,
    "z_conj_v0v2": 3.0,
    "z_minus_market": 2.0,
    "p_breadth": 0.01,
    "tau_half": 0.8,
    "worse": 0.0,
    "worse_fraction": 0.0,
    "z_beta": 0.0,
    "e_end": 0.1,
}


def state(**change: float | None) -> str:
    """The outcome of GOOD with some facts changed; None removes the fact."""
    got = {**GOOD, **change}
    frame = pd.DataFrame(
        [("s", P + k, v) for k, v in got.items() if v is not None],
        columns=["who", "key", "value"],
    )
    return criteria.outcomes(frame, ["s"], [r for r in RULES])["s"][0]


def test_the_good_strategy_passes_and_every_rule_has_a_name() -> None:
    """A strategy that meets every line passes, and every line carries its Spanish name."""
    assert state() == "pass"
    assert len(RULES) == 9 and all(r.get("name") for r in RULES)


def test_each_rule_has_its_pass_limbo_and_fail() -> None:
    """(changes, outcome) per line of the encargo's table; a rule that never fails says so."""
    cases = [
        ({"invalid_fraction": 0.25}, "pass"),
        ({"invalid_fraction": 0.3}, "limbo"),
        ({"fixed_distance": 1}, "limbo"),
        ({"fixed_distance": 5}, "limbo"),
        ({"freq_off": 1, "freq_off_fraction": 0.1}, "limbo"),
        ({"freq_off": 2}, "limbo"),
        ({"freq_off": 3, "freq_off_fraction": 0.2}, "fail"),
        ({"freq_off": 1, "freq_off_fraction": 0.3}, "fail"),
        ({"z_conj_v0v2": 1.65}, "pass"),
        ({"z_conj_v0v2": 1.0}, "limbo"),
        ({"z_conj_v0v2": 0.0}, "limbo"),
        ({"z_conj_v0v2": -0.1}, "fail"),
        ({"z_conj_v2": -5.0, "z_conj": -5.0}, "pass"),  # columns, no longer judge
        ({"z_minus_market": 1.65}, "pass"),
        ({"z_minus_market": -3.0}, "limbo"),
        ({"p_breadth": 0.10}, "pass"),
        ({"p_breadth": 0.5}, "limbo"),
        ({"tau_half": 0.5}, "pass"),
        ({"tau_half": 0.2}, "limbo"),
        ({"tau_half": 0.0}, "fail"),
        ({"tau_half": float("-inf")}, "fail"),
        ({"worse": 1}, "pass"),
        ({"worse": 2, "worse_fraction": 0.2}, "limbo"),
        ({"worse": 3, "worse_fraction": 0.3}, "fail"),
        ({"worse": 1, "worse_fraction": 0.3}, "fail"),
    ]
    bad = [(c, got, want) for c, want in cases if (got := state(**c)) != want]
    assert not bad, bad


def test_p9_four_corners_and_the_bands_between() -> None:
    """z_beta > -1.65 passes whatever e_end says; between -2.33 and -1.65 e_end > 0 passes and
    otherwise limbo; at or under -2.33 e_end > 0 is limbo and e_end <= 0 fails."""
    for z, e, want in [
        (0.0, 0.1, "pass"),
        (0.0, -0.1, "pass"),
        (-1.64, -0.1, "pass"),
        (-1.65, 0.1, "pass"),
        (-1.65, -0.1, "limbo"),
        (-2.0, 0.1, "pass"),
        (-2.0, -0.1, "limbo"),
        (-2.33, 0.1, "limbo"),
        (-2.33, 0.0, "fail"),
        (-3.0, 0.1, "limbo"),
        (-3.0, -0.1, "fail"),
    ]:
        assert state(z_beta=z, e_end=e) == want, (z, e)


def test_a_missing_fact_is_limbo_and_p7_without_e_principal_never_passes() -> None:
    """Every fact absent alone gives limbo (P9's e_end excepted: z_beta alone can pass it);
    the whole of step 10 with tau_half empty is limbo, which is what the encargo accepts."""
    for fact in set(GOOD) - {"e_end"}:
        assert state(**{fact: None}) == "limbo", fact
    assert state(z_beta=None, e_end=None) == "limbo"
    assert state(e_end=None) == "pass"  # z_beta > -1.65 passes P9 whatever e_end says
    assert state(z_beta=-2.0, e_end=None) == "limbo"
    assert state(z_conj_v0v2=-5, tau_half=None) == "fail"  # a fail still beats a limbo


if __name__ == "__main__":
    for test in (
        test_the_good_strategy_passes_and_every_rule_has_a_name,
        test_each_rule_has_its_pass_limbo_and_fail,
        test_p9_four_corners_and_the_bands_between,
        test_a_missing_fact_is_limbo_and_p7_without_e_principal_never_passes,
    ):
        test()
    print("ok: paso 10, P1-P9 por el camino del juez")

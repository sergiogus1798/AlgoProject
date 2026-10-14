#!/usr/bin/env python3
"""The rules `criteria.yaml` gives steps 18.5 (off, entry kept) and 19; 18 has none, on hand-made fact rows: every branch
of each rule, the missing ones included, as the real file is read — and the two shapes those
facts come in, a batch file and a WFM page."""

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, facts, judge

STEPS = judge.settings()["steps"]


def state(n: str, row: dict[str, float]) -> str:
    """Step `n`'s outcome for one strategy carrying the facts of `row`."""
    frame = pd.DataFrame(
        [("m", k, v) for k, v in row.items()] + [("other", "x", 1.0)],
        columns=["who", "key", "value"],
    )
    return criteria.outcomes(frame, ["m"], criteria.resolved(STEPS[n]["rules"], set()))[
        "m"
    ][0]


def test_step_18() -> None:
    """18 is a column since encargo 65 §3c: no rules, so it judges and cuts nobody."""
    assert STEPS["18"]["rules"] == []


def test_step_18_5() -> None:
    """Order positive or neutral passes, perverse fails, absent (sin_dato) is limbo; the premium
    under its null's p5 and a perverse oos2 only add limbo; oos2 absent — before the blind
    block — does not count."""
    ok = {"marketSurfaces.orden.estado": 0.0, "marketSurfaces.prima.bajo_p5": 0.0}
    assert state("18.5", ok) == "pass"
    assert state("18.5", ok | {"marketSurfaces.orden.estado": 1.0}) == "pass"
    assert state("18.5", ok | {"marketSurfaces.oos2.perverso": 0.0}) == "pass"
    assert state("18.5", ok | {"marketSurfaces.orden.estado": -1.0}) == "fail"
    assert state("18.5", {"marketSurfaces.prima.bajo_p5": 0.0}) == "limbo"
    assert state("18.5", {"marketSurfaces.orden.estado": 1.0}) == "limbo"
    assert state("18.5", ok | {"marketSurfaces.prima.bajo_p5": 1.0}) == "limbo"
    assert state("18.5", ok | {"marketSurfaces.oos2.perverso": 1.0}) == "limbo"
    assert state("18.5", ok | {"marketSurfaces.oos2.sin_dato": 1.0}) == "limbo"
    assert (
        state(
            "18.5",
            ok
            | {
                "marketSurfaces.oos2.sin_dato": 0.0,
                "marketSurfaces.oos2.perverso": 0.0,
            },
        )
        == "pass"
    )
    assert (
        state(
            "18.5",
            ok
            | {
                "marketSurfaces.orden.estado": -1.0,
                "marketSurfaces.oos2.perverso": 1.0,
            },
        )
        == "fail"
    )


def test_step_19() -> None:
    """L1: p- at 0.05 or under fails, a median excess at zero or under is limbo. Modo fijo —
    no `wfm.reopt.*` — is not hurt by their absence; present, they only add limbo."""
    ok = {"wfm.l1.p_menos": 0.40, "wfm.l1.mediana_exceso": 12.0}
    assert state("19", ok) == "pass"  # modo fijo
    assert state("19", ok | {"wfm.l1.p_menos": 0.05}) == "fail"
    assert state("19", ok | {"wfm.l1.p_menos": 0.051}) == "pass"
    assert state("19", ok | {"wfm.l1.mediana_exceso": 0.0}) == "limbo"
    assert (
        state("19", ok | {"wfm.l1.p_menos": 0.01, "wfm.l1.mediana_exceso": -3.0})
        == "fail"
    )
    assert state("19", {"wfm.l1.mediana_exceso": 12.0}) == "limbo"
    assert state("19", {"wfm.l1.p_menos": 0.40}) == "limbo"
    reopt = ok | {"wfm.reopt.centro_exceso": 5.0, "wfm.reopt.l2_p_menos": 0.30}
    assert state("19", reopt) == "pass"
    assert state("19", reopt | {"wfm.reopt.centro_exceso": 0.0}) == "limbo"
    assert state("19", reopt | {"wfm.reopt.l2_p_menos": 0.05}) == "limbo"
    assert (
        state("19", reopt | {"wfm.reopt.l2_p_menos": 0.05, "wfm.l1.p_menos": 0.02})
        == "fail"
    )


def test_the_three_annotate() -> None:
    """`cut: null` on each: they judge and delete nothing."""
    assert all(STEPS[n]["cut"] is None for n in ("17", "18", "18.5", "19"))


def test_the_facts_come_from_a_batch_file_and_from_a_page() -> None:
    """18.5's file: `orden.estado` in words becomes a number, an absent state is no fact.
    19's page (`estrategias/<name>.json` of a result folder): its `facts` are read too."""
    with tempfile.TemporaryDirectory() as tmp:
        file = Path(tmp) / "Strategy_1.2.3" / "estudios" / "marketSurfaces.json"
        file.parent.mkdir(parents=True)
        file.write_text(
            json.dumps(
                {
                    "facts": {
                        "orden": {"estado": "perverso", "rho": -0.2},
                        "prima": {"bajo_p5": 1},
                    }
                }
            )
        )
        got = {r["key"]: r["value"] for r in facts.file_rows("marketSurfaces", file)}
        assert got == {"orden.estado": -1.0, "orden.rho": -0.2, "prima.bajo_p5": 1.0}
        assert {r["strategy"] for r in facts.file_rows("marketSurfaces", file)} == {
            "Strategy 1.2.3"
        }

        page = Path(tmp) / "wfm" / "estrategias" / "Strategy 1.2.3.json"
        page.parent.mkdir(parents=True)
        page.write_text(
            json.dumps(
                {
                    "strategy": "Strategy 1.2.3",
                    "identity": "abc",
                    "facts": {"l1": {"p_menos": 0.4, "mediana_exceso": 3}},
                }
            )
        )
        rows = facts.from_folder("wfm", page.parent.parent)
        assert {(r["strategy"], r["identity"], r["key"], r["value"]) for r in rows} == {
            ("Strategy 1.2.3", "abc", "l1.p_menos", 0.4),
            ("Strategy 1.2.3", "abc", "l1.mediana_exceso", 3.0),
        }


if __name__ == "__main__":
    test_step_18()
    test_step_18_5()
    test_step_19()
    test_the_three_annotate()
    test_the_facts_come_from_a_batch_file_and_from_a_page()
    print("ok")

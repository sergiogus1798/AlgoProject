#!/usr/bin/env python3
"""The judge finds the facts of a strategy whose identity changed between the build and the
retest: `selection.resolve` is the one lookup, and it moves nothing for an identity that held.
On frames built here: no SQX, no install."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, selection

PRESENCE = {"fact": "gate.presencia", "pass": ">= 1", "missing": "fail"}
# The cut databank: A kept its identity, B's changed in the retest, C is known by name only.
POP = pd.DataFrame({"strategy": ["A", "B", "C"], "identity": ["ia", "ib_retest", "ic"]})


def facts(rows: list[tuple[str, str, str, float]]) -> pd.DataFrame:
    """A long fact frame from (strategy, identity, key, value) rows."""
    return pd.DataFrame(rows, columns=["strategy", "identity", "key", "value"])


def outcomes(pop: pd.DataFrame, found: pd.DataFrame) -> dict[str, str]:
    """Strategy name → its state under PRESENCE, resolved as `judge.judge` does."""
    who, found_who = selection.resolve(pop, found)
    got = criteria.outcomes(found.assign(who=found_who), sorted(set(who)), [PRESENCE])
    return {s: got[w][0] for s, w in zip(pop["strategy"], who)}


def test_a_changed_identity_finds_its_gate_facts() -> None:
    """The gate files B under the build identity, the monkey under the retest's: both are B's."""
    found = facts(
        [
            ("A", "ia", "gate.presencia", 1.0),
            ("B", "ib_build", "gate.presencia", 1.0),
            ("B", "ib_retest", "monkey.p", 0.2),
            ("C", "ic", "gate.presencia", 1.0),
        ]
    )
    who, found_who = selection.resolve(POP, found)
    assert list(who) == ["ia", "ib_retest", "ic"]
    assert list(found_who) == ["ia", "ib_retest", "ib_retest", "ic"]
    assert outcomes(POP, found) == {"A": "pass", "B": "pass", "C": "pass"}


def test_a_changed_identity_no_fact_carries_is_found_by_name() -> None:
    """No study read the retest file of B: it is judged under its name, and the gate's fact too."""
    found = facts(
        [("A", "ia", "gate.presencia", 1.0), ("B", "ib_build", "gate.presencia", 1.0)]
    )
    who, found_who = selection.resolve(POP, found)
    assert list(who) == ["ia", "B", "C"] and list(found_who) == ["ia", "B"]
    assert outcomes(POP, found) == {"A": "pass", "B": "pass", "C": "fail"}


def test_a_fact_without_identity_keeps_its_key() -> None:
    """crossTF files a mother by name: the fact stays under the name, as before the fix."""
    found = facts(
        [
            ("A", "", "gate.presencia", 1.0),
            ("C", "", "gate.presencia", 1.0),
            ("A", "ia", "monkey.p", 0.2),
        ]
    )
    who, found_who = selection.resolve(POP, found)
    assert list(who) == ["ia", "B", "C"] and list(found_who) == ["A", "C", "ia"]
    assert outcomes(POP, found) == {"A": "fail", "B": "fail", "C": "pass"}


def test_equal_identities_resolve_as_before() -> None:
    """Every identity held: each side is keyed by it, and a foreign fact joins nobody."""
    found = facts(
        [
            ("A", "ia", "gate.presencia", 1.0),
            ("B", "ib_retest", "gate.presencia", 0.0),
            ("C", "ic", "gate.presencia", 1.0),
            ("Z", "iz", "gate.presencia", 1.0),
        ]
    )
    who, found_who = selection.resolve(POP, found)
    assert list(who) == list(POP["identity"]) and list(found_who) == list(
        found["identity"]
    )
    assert outcomes(POP, found) == {"A": "pass", "B": "fail", "C": "pass"}


if __name__ == "__main__":
    test_a_changed_identity_finds_its_gate_facts()
    test_a_changed_identity_no_fact_carries_is_found_by_name()
    test_a_fact_without_identity_keeps_its_key()
    test_equal_identities_resolve_as_before()
    print("ok")

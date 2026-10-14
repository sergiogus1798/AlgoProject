#!/usr/bin/env python3
"""Known-answer test of crossmarket/travel's recorded distributions (encargo: draws behind every z):
on the rules test's toy tensor, each raw row reproduces the study's own z (or p) from its observed
value and its draws, and the per-market rows keep only the histogram."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.transfer.crossmarket.travel import records, rules
from test_crossmarket_travel_rules import CAL, CFG, toy


def test_rows_reproduce_the_verdict() -> None:
    """z of every raw row equals the verdict column of the same name; p_breadth from n_ge."""
    one = toy()
    got = rules.evaluate(one, CAL, CFG)
    out = records.rows(one, rules.windows(CAL), got, "S", "id1", 7)
    verdict = got["verdict"]
    raw = {r["metric"]: r for r in out if len(r["draws"])}
    assert set(raw) == {
        "z_conj",
        "z_conj_v0",
        "z_conj_v1",
        "z_conj_v2",
        "z_conj_v0v2",
        "z_minus_market",
        "p_breadth",
        "z_beta",
    }
    for metric, r in raw.items():
        assert (
            json.loads(r["where"])["seed"] == 7
            and r["strategy"] == "S"
            and r["identity"] == "id1"
        )
        if metric == "p_breadth":
            assert (1 + r["n_ge"]) / (r["n"] + 1) == pytest.approx(
                verdict[metric], abs=1e-9
            )
            continue
        assert (r["observed"] - r["mean"]) / r["sd"] == pytest.approx(
            verdict[metric], abs=1e-9
        )
    per_market = [r for r in out if r["metric"] == "z"]
    assert [json.loads(r["where"])["market"] for r in per_market] == ["A", "B", "C"]
    assert all(len(r["draws"]) == 0 and len(r["counts"]) for r in per_market)
    for r, z in zip(per_market, got["markets"]["z"]):
        assert (r["observed"] - r["mean"]) / r["sd"] == pytest.approx(z, abs=1e-9)

#!/usr/bin/env python3
"""Step 10's negative controls (owner, 2026-10-12): P8 per role, the roles from the expected-sign table, the table's reader."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.transfer.crossmarket.travel import rules
from test_crossmarket_travel_rules import CAL, CFG, toy


def test_negative_controls_pass_below_zero_and_count_above_the_line() -> None:
    """A structural market of a control family passes with z <= 0 and counts against P8 from +1.65."""
    z, n = np.array([-5.0, 0.0, 1.64, 1.65, 3.0]), np.array([100] * 5)
    assert rules.worse(z, n, 30, -1.65, ["control"] * 5) == 2              # only +1.65 and +3.0
    assert rules.worse(z, n, 30, -1.65, ["free"] * 5) == 1                 # today's sense: -5.0 only
    assert rules.worse(z, n, 30, -1.65, ["skip"] * 5) == 0                 # no sign: never counts
    got = rules.evaluate(toy(), CAL, CFG, role=["free", "control", "skip"])["verdict"]
    assert got["worse"] == 1 and got["worse_fraction"] == 1 / 2            # B z = +1.73 against; C left out
    got = rules.evaluate(toy(), CAL, CFG, role=["free", "free", "control"])["verdict"]
    assert got["worse"] == 0                                                # C: z = -0.87 <= 0 passes


def test_roles_come_from_the_expected_sign_table() -> None:
    """roles(): structural markets follow the family's row; family markets and unknown families stay free."""
    table = {"volatility": {"family": "positive", "structural": "control"},
             "momentum": {"family": "positive", "structural": "none"}}
    cat = {"F": "family", "S": "structural"}
    assert rules.roles(["F", "S", "X"], cat, "volatility", table) == ["free", "control", "free"]
    assert rules.roles(["F", "S", "X"], cat, "momentum", table) == ["free", "skip", "free"]
    assert rules.roles(["F", "S"], cat, "", table) == ["free", "free"]       # Simple Strategy: as before


def test_expected_sign_is_read_and_is_not_an_asset() -> None:
    """The seven rows of _markets.yaml; `markets()` never hands the table back as a main's block."""
    from core import assetdata
    table = assetdata.expected_sign()
    assert sorted(table) == ["breakout", "meanReversion", "momentum", "pattern", "session", "trendFollowing", "volatility"]
    assert {f for f, r in table.items() if r["structural"] == "control"} == {"breakout", "volatility", "meanReversion", "session"}
    assert all(r["family"] == "positive" for r in table.values())
    assert assetdata.markets("_expected_sign") == {} and assetdata.markets("XAUUSD")["categories"]


def test_p3_z_pools_only_the_free_markets() -> None:
    """z_conj_v0v2 leaves controls and skips out; z_conj keeps every market."""
    # V0+V2 totals A 6, B 5, C -3: all three real 8 (z 8/6); without the control C real 11, sd sqrt(24)
    every = rules.evaluate(toy(), CAL, CFG)["verdict"]
    cut = rules.evaluate(toy(), CAL, CFG, role=["free", "free", "control"])["verdict"]
    assert every["z_conj_v0v2"] == pytest.approx(8 / 6) and cut["z_conj_v0v2"] == pytest.approx(11 / 24 ** 0.5)
    assert cut["z_conj"] == every["z_conj"] and cut["z_conj_v0"] == every["z_conj_v0"]

#!/usr/bin/env python3
"""The «Entradas del dueño» writer: a typed value reaches the local layer and the loaders, a blank one goes back, comments survive."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import config as study_config
from portfolio.common.construct.inputs import config as construct_config
from portfolio.funded.sim import inputs
from ui.daemon.portfolios import owner


def test_answered_values_load() -> None:
    """The owner's answers of 2026-10-14 are what the loaders give, in the scale the verdict reads."""
    cfg = construct_config.load([])
    assert cfg["funded"]["open_risk_cap"] == 0.5
    assert cfg["verdict"]["pass_percentile"] == 0.95, (
        "0-1 scale: decide.py compares 1 - level"
    )
    gaps = inputs.load([])["gaps"]
    assert (
        gaps["hantec_fee_refund"] is False
        and gaps["hantec_endurance_payout_days"] == 14
    )


def test_owner_inputs() -> None:
    """One pass over the writer."""
    keep = study_config.LAYER
    try:
        with tempfile.TemporaryDirectory() as tmp:
            study_config.LAYER = (
                Path(tmp) / "owner.yaml"
            )  # never the real config/owner.yaml
            base = inputs.load([])
            was = base["owner"]["tax_rate"]
            owner.set_field("sim.owner.tax_rate", "0,21")
            owner.set_field("sim.gaps.ftmo_1step_floor_after_payout", "initial")
            owner.set_field("construct.funded.open_risk_cap", "0.4")
            got = inputs.load([])
            assert was is None and got["owner"]["tax_rate"] == 0.21, (
                "the layer reaches the sim loader"
            )
            assert got["gaps"]["ftmo_1step_floor_after_payout"] == "initial"
            assert construct_config.load([])["funded"]["open_risk_cap"] == 0.4, (
                "and the construct loader"
            )
            assert inputs.load(["owner.tax_rate=0.3"])["owner"]["tax_rate"] == 0.3, (
                "--set still wins"
            )
            assert got["owner"]["p_payout_denied"] == 0.05, (
                "an input never typed keeps the file's value"
            )
            owner.set_field("sim.owner.tax_rate", "")
            assert inputs.load([])["owner"]["tax_rate"] is None, (
                "a blank box gives the file's value back (tax off)"
            )
            for field, bad in (
                ("sim.owner.tax_rate", "1.5"),
                ("sim.owner.eurusd", "0"),
                ("sim.gaps.hantec_endurance_payout_days", "3.5"),
                ("sim.gaps.ftmo_1step_floor_after_payout", "never"),
                ("sim.owner.rebuy", "1"),
            ):
                try:
                    owner.set_field(field, bad)
                except ValueError:
                    continue
                raise AssertionError(f"{field}={bad} should be refused")
            text = study_config.LAYER.read_text()
            assert (
                text.startswith("# Written by the window")
                and "open_risk_cap: 0.4" in text
            )
    finally:
        study_config.LAYER = keep

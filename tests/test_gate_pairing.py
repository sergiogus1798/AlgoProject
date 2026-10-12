#!/usr/bin/env python3
"""Known answers for the gate's pairing: by identity, never by file name."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import paths
from studies.screening.gate import collect, pairing


def test_same_name_other_identity_is_not_paired() -> None:
    """A reused name must not join two strategies; the same identity under another name does."""
    build = {"idA": Path("1.1.1.sqx"), "idB": Path("1.1.2.sqx")}
    after = {"idX": Path("1.1.1.sqx"), "idB": Path("renamed.sqx")}
    pairs, alias, missing = pairing.pair(build, after)
    assert set(pairs) == {"idB"} and pairs["idB"][1].name == "renamed.sqx"
    assert alias == {"idX": "idA"} and missing == ["idA"]


def test_golden_real_harvest() -> None:
    """On a stored harvest the identity pairs are exactly the pairs the name pairing made."""
    project, day = "Test_NIKKEI225_M30_simpleL_fin", "2026-10-05"
    done = paths.harvest_dir(project, "Results", day) / "metrics.parquet"
    install = paths.worker_dir("custodian")
    banks = [paths.databank_dir(project, d, install) for d in ("Results", "OOS")]
    if not done.exists() or not all(b.is_dir() and any(b.glob("*.sqx")) for b in banks):
        pytest.skip("harvest or its databanks absent")
    build, after = (collect.index(b) for b in banks)
    pairs, alias, missing = pairing.pair(build, after)
    held = pd.read_parquet(done, columns=["strategy_build", "strategy"])
    assert set(pairs) == set(held.index) and not alias
    assert {i: pairs[i][0].stem for i in pairs} == held["strategy_build"].to_dict()

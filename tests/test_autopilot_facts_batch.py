#!/usr/bin/env python3
"""A batch study's result that is a FILE (the WFC) reaches facts, and the seal of oos2 holds."""

import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import gate
from pipeline.autopilot import criteria, facts, judge


def test_file_result_flattens_facts_and_names_the_mother_like_the_databank() -> None:
    """`<batch>/estudios/wfc.json`: the state words become numbers, rho and p stay numbers."""
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "Strategy_10.11.484" / "estudios" / "wfc.json"
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({"facts": {"c1": {"estado": "limbo", "orden": "perverso",
                                                  "rho": -0.2, "p_menos": 0.01, "nota": "x"}}}))
        got = {r["key"]: r["value"] for r in facts.file_rows("wfc", f)}
        assert {r["strategy"] for r in facts.file_rows("wfc", f)} == {"Strategy 10.11.484"}
    assert got["c1.estado"] == 0.0 and got["c1.orden"] == -1.0
    assert got["c1.rho"] == -0.2 and got["c1.p_menos"] == 0.01 and got["c1.nota"] is None


def test_the_criterion_of_step_17_judges_the_three_states() -> None:
    """criteria.yaml's rule on `wfc.c1.estado`: pasa passes, limbo is limbo, no_pasa fails, absent is limbo."""
    rule = judge.settings()["steps"]["17"]["rules"][0]
    out = [criteria.one(v, rule, 0.0) for v in (1.0, 0.0, -1.0)]
    assert out == ["pass", "limbo", "fail"] and rule["missing"] == "limbo"


def test_seal_shuts_oos2_without_a_written_calibrated_criterion() -> None:
    """Step 17 on oos2: sealed with no calibration, with another criteria.yaml's hash, or `abre: false`;
    open with a matching one. build is never sealed; a step not in `reserved_for` is refused."""
    real = gate.CALIBRATION
    with tempfile.TemporaryDirectory() as tmp:
        gate.CALIBRATION = Path(tmp) / "wfc_calibration.json"
        try:
            gate.seal(17, "build+oos1", "XAUUSD")
            with pytest.raises(PermissionError):
                gate.seal(17, "oos2", "XAUUSD")
            sha = gate.criteria_hash(yaml.safe_load(gate.CRITERIA.read_text(encoding="utf-8"))["steps"]["17"])
            for rec, shut in (({"criteria_sha256": "0", "abre": True}, True),
                              ({"criteria_sha256": sha, "abre": False}, True),
                              ({"criteria_sha256": sha, "abre": True}, False)):
                gate.CALIBRATION.write_text(json.dumps(rec))
                if shut:
                    with pytest.raises(PermissionError):
                        gate.seal(17, "oos1+oos2", "XAUUSD")
                else:
                    gate.seal(17, "oos1+oos2", "XAUUSD")
            gate.seal(18, "oos2", "XAUUSD")           # CSCV: reserved for it, no criterion needed
            with pytest.raises(PermissionError):
                gate.seal(21, "oos2", "XAUUSD")
        finally:
            gate.CALIBRATION = real


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))

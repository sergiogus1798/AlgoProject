"""The old pipeline's verdict stage reads the CSCV facts of estudios/cscv.json with the autopilot's fail cuts."""

import json
import tempfile
from pathlib import Path

from pipeline.stages import recipe, verdict


def test_cscv_facts_gate() -> None:
    """P of loss at 0.5 or over, or a PBO over its null's p95, breaks the gate; below both it holds."""
    rules = [r for r in recipe.settings()["verdict"]["rules"] if r["number"].startswith("cscv.")]
    assert {r["number"] for r in rules} == {"cscv.p_perdida", "cscv.pbo_sobre_p95"}
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "estudios").mkdir()
        (work / "brief.json").write_text("{}")

        def broken(**facts: float) -> list[str]:
            """The numbers of the rules this batch's facts break."""
            (work / "estudios" / "cscv.json").write_text(json.dumps({"facts": facts}))
            return [b["number"] for b in verdict.judge(verdict.numbers(work, work / "brief.json"), rules)]

        assert broken(p_perdida=0.49, pbo_sobre_p95=0) == []
        assert broken(p_perdida=0.5, pbo_sobre_p95=0) == ["cscv.p_perdida"]
        assert broken(p_perdida=0.1, pbo_sobre_p95=1) == ["cscv.pbo_sobre_p95"]

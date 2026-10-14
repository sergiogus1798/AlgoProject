"""18.5 per mother, at execution time: it runs only where step 17's `descuadre_sqx` is under `wfc.sqx_gap_relative`."""

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import blind, call, plan, survivors
from test_autopilot_tail import BLOCK, GIVEN, WHO, kinds, patched, rail
from ledger import gate


def read(gap: float | None) -> str:
    """`blind.look` of 18.5 over one mother whose wfc.json holds `gap` (None: no file); its words."""
    ran = []
    mothers = pd.DataFrame({"strategy": ["M"], "identity": ["i"], "file": [None]})
    with (
        tempfile.TemporaryDirectory() as tmp,
        patched(survivors, about=lambda p: WHO),
        patched(gate, allow=lambda *a: None),
        patched(call, run=ran.append, window=lambda *a: [["-m", a[0]]]),
        patched(blind, variants_dir=lambda p, m: Path(tmp) / m),
    ):
        if gap is not None:
            wfc = Path(tmp) / "M" / "estudios" / "wfc.json"
            wfc.parent.mkdir(parents=True)
            wfc.write_text(
                json.dumps(
                    {"facts": {c: {"descuadre_sqx": gap} for c in ("c1", "c2", "c3")}}
                )
            )
        said = blind.look("P", "18.5", "marketSurfaces", mothers, redo=False)
    return said + ("|ran" if ran else "|none")


def test_a_matching_repricer_runs_18_5() -> None:
    """A descuadre of 0.0 under the threshold: the study is run."""
    assert read(0.0).endswith("|ran") and "saltado" not in read(0.0)


def test_a_gap_skips_18_5_with_a_line_and_the_tail_goes_on() -> None:
    """0.46 is not under 0.01: no run, one Spanish line; the plan still has 18.5 and 19.5."""
    said = read(0.46)
    assert (
        said.endswith("|none")
        and "18.5 saltado en M: descuadre con SQX 0,46 ≥ 0,01" in said
    )
    got = plan.plan(
        rail(), GIVEN
    )  # the plan is made before the figure exists: 19.5 still follows
    assert kinds(got)[2:5] == BLOCK and ("19.5", "oos2read") in kinds(got)


def test_a_missing_wfc_file_skips_18_5() -> None:
    """No wfc.json, no figure: skipped, never a crash."""
    said = read(None)
    assert said.endswith("|none") and "18.5 saltado en M: sin descuadre con SQX" in said


if __name__ == "__main__":
    test_a_matching_repricer_runs_18_5()
    test_a_gap_skips_18_5_with_a_line_and_the_tail_goes_on()
    test_a_missing_wfc_file_skips_18_5()

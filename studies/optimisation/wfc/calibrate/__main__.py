#!/usr/bin/env python3
"""The command: calibrate step 17's criterion and write the register that opens the blind block."""

from typing import Any
import argparse
from pathlib import Path

from core import datapaths
from core.study import config as study_config
from core.study import result
from ledger import gate, thresholds
from studies.optimisation.wfc.calibrate import families, page, rates, record, rehearsal
from studies.optimisation.wfc.inputs import config as wfc_config

HERE = Path(__file__).resolve().parent


def load(overrides: list[str]) -> dict[str, Any]:
    """The calibration's config.yaml, `ledger:` keys filled, then the overrides."""
    return study_config.apply(
        thresholds.fill(study_config.load(HERE / "config.yaml", [])), overrides
    )


def main() -> None:
    """Measure the synthetic grid, rehearse the real batches, print the report, write the register."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--set",
        dest="overrides",
        action="extend",
        nargs="+",
        default=[],
        help="clave=valor de calibrate/config.yaml; con esto el registro no se escribe",
    )
    ap.add_argument(
        "--workers", type=int, default=16, help="procesos para los escenarios"
    )
    a = ap.parse_args()
    cfg, wfc = load(a.overrides), wfc_config.load()
    table = rates.table(families.specs(cfg), cfg, wfc, a.workers)
    result.progress(92, "ensayo build → oos1 en los lotes reales")
    rehearsed = rehearsal.run(datapaths.variants_dir("P", "S").parents[1], wfc)
    decision = record.decide(table, cfg)
    report = page.text(table, decision, rehearsed, cfg, wfc, written=not a.overrides)
    print(report)
    if a.overrides:
        return
    # A register made under --set would sign for a calibration the ledger does not declare.
    record.write(gate.CALIBRATION, record.build(decision, table, rehearsed, cfg, wfc))
    gate.CALIBRATION.with_suffix(".md").write_text(report + "\n", encoding="utf-8")
    result.progress(100, f"registro escrito, abre: {str(decision['abre']).lower()}")
    print(f"-> {gate.CALIBRATION}")


if __name__ == "__main__":
    main()

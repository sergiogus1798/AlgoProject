#!/usr/bin/env python3
"""The WFC's composition of the split: only the owner's four pass, and each look is recorded per segment."""

import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.variants import look, panel
from ledger import blind, gate, record

REFUSED = ((["oos1"], ["oos2"]), (["build"], ["build"]), (["build", "oos1"], ["oos1", "oos2"]),
           (["build"], []), (["build"], ["oos3"]), (["build", "oos2"], ["oos1"]))
UNIONS = ("build", "build+oos1", "oos1", "oos2", "oos1+oos2")   # what sqx.variants.collect writes


def batch(folder: Path) -> Path:
    """A batch holding only the one row `look.market` reads, on USDJPY M30."""
    pd.DataFrame([{"variant_id": "P00000", "segment": "build", "market": look.MAIN,
                   "result_key": "Main: USDJPY_M1/M30"}]).to_parquet(
        folder / "segments.parquet")
    return folder


def main() -> None:
    """Check the admitted compositions, their columns, the door, the rows and blind's skip."""
    failures = []
    for inside, outside in REFUSED:
        try:
            panel.composition(inside, outside)
            failures.append(f"composición admitida: {inside} contra {outside}")
        except ValueError:
            pass
    labels = [panel.label(c) for c in panel.COMPOSITIONS]
    if len(set(labels)) != 4 or any(c[0][0] != "build" for c in panel.COMPOSITIONS):
        failures.append(f"las cuatro composiciones no son distintas o build no va dentro: {labels}")
    for comp in panel.COMPOSITIONS:
        cols = panel.columns(comp)
        if cols["is_label"] not in UNIONS or cols["oos_label"] not in UNIONS:
            failures.append(f"{panel.label(comp)} pide una unión que collect no escribe")
    if {v for v in panel.SHORTCUTS.values()} - set(panel.COMPOSITIONS):
        failures.append("un atajo con nombre no es una composición admitida")

    if look.offered("USDJPY") != labels:
        failures.append(f"con el WFC en reserved_for se ofrecen {look.offered('USDJPY')}")
    look.admit(8, ("build", "oos2"), "USDJPY")      # a human is never refused (2026-09-28)
    os.environ[gate.AUTONOMOUS] = "1"                 # the door holds for an autonomous agent
    for step in (17, 18):
        gate.allow(step, "oos2", "USDJPY")    # raises if the policy stopped granting it
    try:
        look.admit(8, ("build", "oos2"), "USDJPY")
        failures.append("la puerta dejó al paso 8 leer oos2")
    except PermissionError:
        pass
    os.environ.pop(gate.AUTONOMOUS)

    written = []
    record.append = lambda study, row: written.append((study, row)) or row
    with tempfile.TemporaryDirectory() as tmp:
        work = batch(Path(tmp))
        look.log(work, "fam", {"step": 17, "launched_by": "wfc", "n_in": 5, "n_out": 5,
                               "criterion": "wfc/build+oos1__oos2"}, ("build", "oos1", "oos2"))
        frame = pd.DataFrame([row for _, row in written])
        if [s for s, _ in written] != ["USDJPY_M30_fam"] * 3 or \
                list(frame["segment"]) != ["build", "oos1", "oos2"]:
            failures.append(f"filas escritas: {[(s, r['segment']) for s, r in written]}")
        if blind.recorded(frame, 17, work) is not True or blind.recorded(frame, 18, work):
            failures.append("blind no reconoce la fila viva del paso 17, o inventa una del 18")

    print("\n".join(failures) or
          f"ok: {len(REFUSED)} composiciones fuera de la regla rechazadas; las cuatro admitidas "
          f"({', '.join(labels)}) leen uniones que collect ya escribe; la puerta deja al 17 y "
          f"al 18 leer oos2 y rechaza al 8; una mirada deja un renglón por tramo en su estudio "
          f"y blind no la reconstruye")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

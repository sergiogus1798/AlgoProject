#!/usr/bin/env python3
"""Known-answer test for OPEN.md #79: theta-zero's own level, sampled by no other tuple, must not
read as the marginal profile's argmax."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.spp.inputs.export import ORIGINAL, without_original
from studies.breakage.spp.model.profile import marginal, plateau

PARAMETER, METRIC = "BBerDeviation1", "metric"
ORIGIN_LEVEL, PLATEAU_LEVEL = 2.9, 1.5


def grid() -> pd.DataFrame:
    """Four sampled levels with a two-wide plateau at 1.5/2.0, plus theta-zero alone at 2.9,
    scored far above everything sampled — the shape measured 2026-09-27 on the three USDJPY M30
    SPPs (`knowhow/research/spp-origin-level-sampled-once.md`): the step grid never lands back on
    the original value, so permutation -1 is the sole tuple at its own level, and its own
    in-sample score wins there by construction.
    """
    sampled = pd.DataFrame({
        PARAMETER: [1.0, 1.0, 1.5, 1.5, 2.0, 2.0, 2.5, 2.5],
        METRIC: [1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 1.0, 1.0]},
        index=pd.Index(range(8), name="permutation"))
    origin = pd.DataFrame({PARAMETER: [ORIGIN_LEVEL], METRIC: [99.0]},
                          index=pd.Index([ORIGINAL], name="permutation"))
    return pd.concat([sampled, origin])


def main() -> None:
    """Fail loudly if theta-zero's lone level ever re-enters the marginal profile."""
    failures = []
    frame = grid()

    without = without_original(frame)
    if ORIGINAL in without.index:
        failures.append("without_original dejo pasar la fila -1")
    if ORIGIN_LEVEL in without[PARAMETER].to_numpy():
        failures.append("without_original dejo el nivel de theta-zero sin ningun otro tuple")

    curve = marginal(without, PARAMETER, METRIC)
    shape = plateau(curve, share=0.5)
    if shape["argmax"] != PLATEAU_LEVEL:
        failures.append(f"argmax dio {shape['argmax']}, se esperaba el nivel muestreado "
                        f"{PLATEAU_LEVEL}, no el de theta-zero")
    if shape["width"] == 1:
        failures.append("plateau de anchura 1 (spike) sobre un nivel con solo theta-zero")

    # The bug this guards against: aggregating WITH theta-zero spikes on its own lone level.
    buggy_curve = marginal(frame, PARAMETER, METRIC)
    buggy_shape = plateau(buggy_curve, share=0.5)
    if buggy_shape["argmax"] != ORIGIN_LEVEL or buggy_shape["width"] != 1:
        failures.append("el fixture no reproduce el bug original — revisar los valores de la rejilla")

    print("\n".join(failures) or
          "ok: sin theta-zero el argmax cae en el nivel muestreado y no hay spike de anchura 1; "
          "con theta-zero (el bug) el fixture sigue reproduciendo el artefacto original")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

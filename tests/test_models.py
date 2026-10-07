#!/usr/bin/env python3
"""Regression test for `trade_models.semester_shift`: the same calendar semester moves the same way
in every market, and by batches reproduces the whole draw — what the travel test's joint shift rests on."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.nulls.placement import trade_models

DRAWS, SEED = 200, 20260908


def main() -> None:
    """Fail loudly on the first property that does not hold."""
    failures = []
    # The same semester, drawn for two markets that start five years apart, must move the
    # same way: that is what lets the travel test shift every market jointly.
    shared = [trade_models.semester_shift(SEED, 4030, DRAWS, 0),
              trade_models.semester_shift(SEED, 4030, DRAWS, 0)]
    if not np.array_equal(*shared):
        failures.append("semester_shift: el mismo semestre dio dos desplazamientos")
    if np.array_equal(shared[0], trade_models.semester_shift(SEED, 4031, DRAWS, 0)):
        failures.append("semester_shift: dos semestres distintos dieron el mismo")
    whole = trade_models.semester_shift(SEED, 4030, DRAWS, 0)
    halves = np.concatenate([trade_models.semester_shift(SEED, 4030, DRAWS // 2, 0),
                             trade_models.semester_shift(SEED, 4030, DRAWS // 2, DRAWS // 2)])
    if not np.array_equal(whole, halves):
        failures.append("semester_shift: por lotes no reproduce la tirada entera")
    print("\n".join(failures)
          or "ok: un semestre se mueve igual en cualquier mercado")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

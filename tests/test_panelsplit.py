#!/usr/bin/env python3
"""Known-answer test: `panel.split` cuts at a segment's own start, not a retested leg's warm-up."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from engines.variants import panel

SYMBOL = "USDJPY"
# assets/_policy.yaml: oos2 starts 2023. A leg retested over oos2 carries curve points from
# ~2 months earlier at zero P&L (knowhow/sqx-format/leg-curve-warmup.md); `equity.json`'s
# `windows` used to record that warm-up date, and cutting there put oos1's real tail on the
# OOS side (issue 44).
WARMUP = "2022-11-03"


def main() -> None:
    """The boundary is oos2's real start, and no P&L dated before it lands on the OOS side."""
    failures = []
    comp = panel.SHORTCUTS["oos2_only"]
    boundary = panel.split(SYMBOL, comp)
    true_start = assetdata.segment_start(assetdata.load(SYMBOL), "oos2")

    if boundary != true_start:
        failures.append(f"split() = {boundary}, no coincide con el tramo real {true_start}")
    if boundary <= WARMUP:
        failures.append(f"split() = {boundary} no es posterior al calentamiento {WARMUP}: "
                        "el arreglo no habría movido nada")

    # A leg's curve carries real P&L through the tail of oos1 (…2022-12-31), including the
    # days its own warm-up (2022-11-03…12-31) overlaps — every one of them before oos2's
    # real start.
    dates = pd.date_range("2022-10-01", "2023-02-01", freq="D")
    wide = pd.DataFrame({"P00000": 1.0}, index=dates)
    inside, outside = panel.windows(wide, boundary)

    if not (inside.index < boundary).all() or not (outside.index >= boundary).all():
        failures.append("windows() no respeta su propio boundary")
    tail = wide.loc[WARMUP:"2022-12-31"]
    if not tail.index.isin(inside.index).all():
        failures.append(f"P&L de {WARMUP} a 2022-12-31 (tramo oos1) cayó del lado OOS: "
                        "ha vuelto el bug del calentamiento")

    print("\n".join(failures) or
          f"ok: split('{SYMBOL}', oos2_only) = {boundary}, el propio inicio de oos2 en "
          f"_policy.yaml y no el calentamiento {WARMUP}; ningún P&L de antes de {boundary} "
          "cae del lado OOS")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

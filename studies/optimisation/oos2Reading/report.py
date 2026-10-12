#!/usr/bin/env python3
"""The single reading of oos2: every mother of a project, one look in her cell, cut by sign only."""

import argparse
import json
import sys
import zlib

import numpy as np

from core import assetdata
from core.barstore import source as read_bars
from engines.market import reprice
from engines.nulls import footprint
from engines.variants import look
from ledger import cells
from studies.optimisation.oos2Reading import inputs, measure

REFUSED = 3     # exit code of a look the ledger refuses


def main() -> None:
    """Ask the door and the seal, spend the cell's look, read each mother, write `estudios/oos2Reading.json`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()
    cfg = inputs.config(a.overrides)
    mothers = inputs.batches(a.project)
    symbol, _ = look.market(next(iter(mothers.values())))
    look.admit(inputs.STEP, (inputs.SEGMENT,), symbol)
    try:
        looks = cells.look_oos2(a.project, cfg["max_looks"])
    except PermissionError as refusal:
        print(refusal, file=sys.stderr)
        sys.exit(REFUSED)
    feed = assetdata.load(symbol)["sqx_symbol"]
    span = inputs.window(symbol)
    bars = read_bars(feed, ["Open", "High", "Low", "Close"])
    bars = bars[(bars.index >= span[0]) & (bars.index < span[1])]
    costs = reprice.costs(feed, inputs.SEGMENT)
    for i, (name, batch) in enumerate(mothers.items()):
        print(f"PROGRESS {100 * i // len(mothers)} {name}", flush=True)
        trades = inputs.mother_trades(batch, span)
        excess = measure.weekly(inputs.daily(trades, bars),
                                footprint.footprint(trades, bars, costs, cfg["benchmark"])[0])
        seed = np.random.SeedSequence([cfg["null"]["seed"], zlib.crc32(name.encode())])
        facts = measure.read(excess, cfg["null"], seed)
        (batch / "estudios").mkdir(exist_ok=True)
        (batch / "estudios" / "oos2Reading.json").write_text(json.dumps(
            {"strategy": name, "facts": facts | {"miradas_celda": looks}}, indent=2), encoding="utf-8")
        print(f"{name}: suma {facts['suma']:.2f}  z {facts['z']:+.2f}  p {facts['p']:.4f} "
              f"± {facts['p_error_mc']:.4f}  {'CORTA' if facts['corta'] else 'sigue'}")
    print(f"PROGRESS 100 {len(mothers)} madres, mirada {looks} de {cfg['max_looks']} de su celda")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate the orderstocsv export on ONE strategy before scaling to the pool.

Checks, in order:
  1. what values Close type / Sample type actually take,
  2. that MAE/MFE ($) convert to price via  price = |$| / (Size * pointValue),
  3. what the realised cost per trade is, by comparing reported P/L against
     gross (close-open) * size * pointValue.  This is how we learn whether the
     SizeBased commission of 8 is charged per side or per round turn.
"""
import csv, sys
from collections import Counter
from datetime import datetime

POINT_VALUE = 100.0          # $ per 1.0 price unit per 1.0 lot (XAUUSD_Infinox)

def load(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        # SQX writes ';'-separated, '"'-quoted
        return [r for r in csv.DictReader(fh, delimiter=";") if (r.get("Open price") or "").strip()]

rows = load(sys.argv[1])
print(f"{len(rows)} trades\n")

for col in ("Type", "Close type", "Sample type"):
    print(f"{col}: {dict(Counter(r[col] for r in rows))}")
print(f"Time in trade: {dict(Counter(r['Time in trade'] for r in rows).most_common(12))}\n")

f = lambda s: float(str(s).replace(",", "."))

print(f"{'open':>9} {'close':>9} {'size':>6} {'gross$':>10} {'rep P/L':>10} "
      f"{'cost$':>8} {'$/lot/side':>11} {'MAEpx':>7} {'MFEpx':>7}")
costs_per_lot_side = []
for r in rows[:12]:
    op, cl, sz = f(r["Open price"]), f(r["Close price"]), f(r["Size"])
    pl = f(r["Profit/Loss"])
    gross = (cl - op) * sz * POINT_VALUE          # long-only, so no sign flip
    cost = gross - pl                              # what the engine took out
    per_lot_side = cost / (sz * 2)                 # if charged both sides
    costs_per_lot_side.append(per_lot_side)
    mae_px = abs(f(r["MAE ($)"])) / (sz * POINT_VALUE)
    mfe_px = abs(f(r["MFE ($)"])) / (sz * POINT_VALUE)
    print(f"{op:9.2f} {cl:9.2f} {sz:6.2f} {gross:10.2f} {pl:10.2f} "
          f"{cost:8.2f} {per_lot_side:11.3f} {mae_px:7.3f} {mfe_px:7.3f}")

# Full-sample view of the implied cost
allc = []
for r in rows:
    op, cl, sz = f(r["Open price"]), f(r["Close price"]), f(r["Size"])
    allc.append(((cl - op) * sz * POINT_VALUE - f(r["Profit/Loss"])) / (sz * 2))
allc.sort()
n = len(allc)
print(f"\nimplied $/lot/side over all {n} trades: "
      f"min {allc[0]:.3f}  p25 {allc[n//4]:.3f}  median {allc[n//2]:.3f}  "
      f"p75 {allc[3*n//4]:.3f}  max {allc[-1]:.3f}")

# Sanity: MAE must bracket the trade's own excursion
bad = 0
for r in rows:
    op, cl, sz = f(r["Open price"]), f(r["Close price"]), f(r["Size"])
    mae_px = abs(f(r["MAE ($)"])) / (sz * POINT_VALUE)
    if cl < op and mae_px < (op - cl) - 1e-6:      # loser: MAE must be >= loss
        bad += 1
print(f"trades where MAE < realised adverse move (should be 0): {bad}")

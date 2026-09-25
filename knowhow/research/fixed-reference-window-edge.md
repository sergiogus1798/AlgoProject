---
q: fixed semester partition reference window, centered window ±3m ±6m ±12m, test 1b paired.py, arbitrary modelling choice sweep, log return presentation basis points dollars
tag: 🔬  date: 2026-09-16  see: research/zero-drift-division
---
# Use a centered reference window; sweep arbitrary choices and print every answer
A fixed-boundary window measures trades near its edge against the past, and gives neighbours across a boundary
disjoint references. Use a centered window (every blind trade of the same length starting within ±N months of
entry). When a modelling choice is arbitrary, sweep it and show all answers. Present log-return stats also in
bps, %, ATR, $/trade and $ accumulated; keep the maths in log space.

## Evidence
- `studies/transfer/crossmarket/simulate/paired.py`, test 1b, previously used the null's fixed semester partition.
- Centered window = running mean over per-bar returns: one pass per distinct hold whatever the width, no per-trade loop, no sampling.
  It reads bars after entry — legitimate, and must be said: "what the market paid around then", not tradable.
- Sweep ±3m / ±6m / ±12m / block partition, `Strategy 1.10.80` / Brent: p = 0.749 / 0.677 / 0.667 / 0.753; alpha −5.27 / −4.68 / −4.72 / −5.22 bps.
- "The timing put −$6,507 into this market" is read; "−0.00053" is not.

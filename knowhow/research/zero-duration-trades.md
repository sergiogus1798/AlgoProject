---
q: fewer trades than SQX databank, zero-duration trades Open time == Close time, Time in trade 0s, envelope.occupancy exit > entry, trade count mismatch, bar grid study
tag: 🔬  date: 2026-09-16  see: research/bar-file-wider-than-backtest, columns/zero-pl-trades
---
# Separate "what the run did" from "what the test could compare", and print both counts
Net profit, drawdown, PF and trade count come from every exported trade row. The subset a bar-grid test can
hold (`exit > entry`) feeds only the null/occupancy. Any grid study (cross-market, stop sim, MAE/MFE) inherits this split.

## Evidence
- `Strategy 24.7.38` gold: 2,142 in databank, 2,089 in study; the 53 missing have `Open time == Close time`,
  `Time in trade` `0s`, `Close type` `Exit Signal` (exit fired on the entry bar).
- `Retest Markets - Family` export: 1,695 of 92,329 trades (1.84 %) zero-duration, in 57 (strategy, market) pairs,
  up to 9.8 % on `Strategy 8.16.41(1)` / silver. Plus 3 `Exit After X Bars` collapsing to one bar, 5 before the first bar of their file.
- `envelope.occupancy()` keeping only `exit > entry` is correct for displacement, blind-window matching and occupied-bar counts — wrong for defining the run.

---
q: which SPP parameters are inert? eta-squared vs duplicate test, freeze parameter, parameter importance, SPP unbalanced, pairing IS/OOS SPP runs
tag: 🔬  date: 2026-09-21  see: export/spp-parameter-importance, export/spp-pairing-for-wfc
---
# Freeze on the duplicate test, never on eta-squared
Inert parameter = every group of tuples differing only in it gives an identical backtest (duplicate test).
Use that to freeze; use eta-squared only to allocate levels. An SPP samples unbalanced, so an inert
parameter's eta-squared is biased upward, not zero. Report eta-squared as a table over several metrics
and name the decision metric. Test inertness per strategy, never per block.

## Evidence
`XAUUSD/SPP IS` (2026-09-10 export), metric `ReturnDDRatio`:
- `CBlock_SqzMmnInt21` on `Strategy 17.9.39`: 217 groups, all 217 identical (inert) — eta² **0.0173**.
- `IsBars1`: eta² **0.0016**, live (1 of 188 groups identical). Eta² would keep the dead one, drop the live one.
- Same block on `Strategy 41.5.25`: 108 groups, only 106 identical — inertness is per strategy.
- ⚠️ Metric dependence: `DICrossShift1` explains 7.6 % of NetProfit, 23.6 % of Ret/DD, 78.5 % of trade count.

Pairing failure (`Strategy 17.9.39`, 2026-09-19 paired export): IS run 11,598 rows, OOS run 11,662,
shared `param_key` values: **6**. Two SPP runs cannot be paired → the 5,000 designed variants are the main route.
Same export: `DICrossShift1` explains 34.2 % of IS Ret/DD variance, 68.2 % of OOS (protocol headline 67.6 %).
Most important OOS parameter, and a shift — one a default-configured SPP freezes.

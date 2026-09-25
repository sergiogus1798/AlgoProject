---
q: pair SPP IS and SPP OOS permutations for walk forward correlation WFC; SPP grid size coverage; Steps MaxTests shifts saturate grid; birthday collisions
tag: 🔬  date: 2026-09-19  see: export/spp-parameter-importance, export/sequential-opt-not-wfc, export/spp-export
---
# Two SPP runs pair only when the grid is saturated; at default settings they share ~0 tuples
- SPP samples (all parameters move at once), it does not walk a grid and is not seeded to repeat.
- Saturate: freeze every `ParamTypeShift` first (÷7^k), then set `Steps ~ n^(1/k) − 1` for a budget of n permutations over k parameters.
- Give the OOS task the SAME SPP settings as the IS task before re-running, or the grids differ.
- Saturated SPP = a WFC instrument with all 152 stats per point, no variant machinery.

## Evidence
- `XAUUSD/SPP IS` (task 13, 2008–2017) vs `SPP OOS` (task 14, 2018–2022): same 5 strategies, byte-identical `strategy_Portfolio.xml`,
  `MaxTests` 15000, ±30 %, 20 steps, *Recommended*. Grids 2.7e7–3.2e11, ~12,000 drawn each. 62,997 IS vs 63,114 OOS tuples share 5 =
  birthday count (5.05 expected on `Strategy 17.9.39`; 0.03/0.20/0.00/0.00 vs 0 on the others). Value domains identical (7–20 values); no run repeats a tuple.
- Each permutation moves ≥2–6 parameters → SPP cannot describe the optimum's neighbourhood. 📓 The 5 collisions join correctly (IS NetProfit 23,608 / OOS 10,789).

| run | params moved | grid | permutations | coverage |
|---|---|---|---|---|
| `Strategy 1.19.29` (20 steps, Recommended) | 10 | 6.0e9 | 12,857 | 0.0002 % |
| `Strategy 1.19.29(1)` (12 steps; Periods+Constants+ExitParamsUsed) | 6 | 6.27e4 | 41,720 | 66.5 % |
| `Strategy 4.33.46(1)` | 5 | 4.03e4 | 34,390 | 85.3 % |

- Expected shared tuples `n_IS × n_OOS / grid` ≈ 27,750 and 29,300 (66 %, 85 % of each run).
- Freezing shifts (3–6 per strategy, 7 levels): `41.5.25` 1.39e11→1.18e6, `17.9.39` 2.06e6→6.0e3, `1.19.29` 6.02e9→3.58e5.
  k=4 → ~10 steps, k=6 → ~4, k=7 → ~3. Integer ranges cap further (`IsBars1` = 3 → 5 values).
- 🤔 Saturation stops at 66 % (21,000 of 62,720 tuples never appear); unknown if SQX excludes them systematically (then real overlap ~100 %).
  As of 2026-09-19 task 14 still had `Steps` 20 / `MaxTests` 15000 / Recommended.

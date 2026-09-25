---
q: sequential optimization results sqx, SequentialOptimization_Results.xml, BestValue stable area, chained scan fitness, sequential opt parse
tag: 🔬  date: 2026-09-10  see: sqx-format/optimization-profile-bin, export/sequential-opt-not-wfc
---
# Sequential optimisation writes plain XML with fitness only; the scan is chained
`.sqx` gains `Results/Main: <SYMBOL>_<feed>/SequentialOptimization_Results.xml` and **no**
`optimizationProfile.bin`. One scalar fitness per point (never an `SQStats`) — any study of it studies
the configured fitness function. `BestValue` = centre of the stable area, not the argmax. Parameter k is
scanned with 1..k-1 fixed at this run's choices; only the first parameter sees the untouched strategy.

## Evidence
- File ~11 KB, root `<ChainOptimizationResults>`. Per optimised variable one `<Parameter originalValue="…">`:
  variable definition, `;`-separated `<Values>` (30 steps over ±30 %, rounded → 30–31 distinct),
  `;`-separated `<Fitness>` in [0,1] same length, `<Results>` with `BestValue`,
  `BestAreaStartValue/EndValue`, `StableAreaFound`. Parse with `ElementTree`, no SQX.
- `BestValue` is the scan's best point on only 5–9 of each strategy's parameters.
- Chain proof: fitness at param k+1's *original* value = fitness at param k's `BestValue` on nearly
  every link (7/7, 7/7, 6/6, 8/9 on four of five XAUUSD strategies; misses where `BestValue` ≠ argmax).
  Tell: fitness at original value differs across parameters in one run (8 distinct over 10 params on
  `Strategy 1.19.29`).

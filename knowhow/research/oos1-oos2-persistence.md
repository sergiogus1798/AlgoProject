---
q: How much of a strategy's per-trade Sharpe on oos1 persists on oos2, and what is a step-8 line worth there?
kw: persistence oos1 to oos2 Spearman 0.06, true spread of edge 0.02, step 8 criteria value on oos2, net-positive per 1000, pool per cell not per passer, near-duplicates weighting, oos2 has no null, t 1.65 passers lose money
tag: 🔬  date: 2026-10-04  see: post-selection-bias, is-optimisation-vs-oos, is-filters-inside-the-build
---
# Per-trade Sharpe barely persists oos1 → oos2 (ρ ≈ 0.06): a step-8 line moves the odds, not the sign
Within-population Spearman of per-trade Sharpe, mean over cells: **0.059** (CI 0.035-0.084; H1 0.026, M30 0.084, indices
0.12, yen 0.03); true spread of edge ≈ 0.02; with hold and frequency partialled out 0.038, **H1 zero**. Worth of a line on
oos2, net-positive per 1,000, passers vs rest of the cell: t ≥ 1.65 & net > 0 **+60** (CI +26…+96), t ≥ 2.33 +122
(fragile), oos1 net > 0 +57, monkey p ≤ 0.05 +26 (≈ 0); about +35 appears with NO edge. ~65 % of line passers still lose
on oos2. Sign: «step 8 moves the odds of an oos2-positive strategy from 29 % to 35 %, half by picking few-trade ones».
**Pool per CELL, never per passer:** one control (428 near-duplicate passers) turned a pooled +60 into −29.
oos2 has no null: index longs 2024-26 are half net-positive anyway (515 vs 503 per 1,000).

## Evidence
- Details: short holds pay more cost per unit risk (hold ↔ Sharpe ρ +0.12); IS → oos1 0.060; 974,188 strategies = 506,614 structures; FX 0.03; passers' oos2 per-trade Sharpe −0.057 vs −0.066.
- 🔬 `AlgoData/scratch/calib2/redteam/review.md` §C1-C2 (independent recomputation from `harvest/<P>/Results/…`;
  scripts `c1.py`, `c2347.py` there). The synthesis's «329 vs 331» was a weighting artefact; the red team's number is recorded.
- 📓 Toolkit wording `synth_final/synthesis.md`: ρ 0.054, ≈ 0.02 spread (agrees); «noise alone ±0.05» is the wrong yardstick (one population's ρ has sd 0.12 across cells).
- 📓 31 base cells (all H1, built before queue v8) have no oos2; oos2 is validation only, never used to choose a line.
- 🤔 Yen «enriched but not persistent» is NOT supported: its persistence equals FX majors'.

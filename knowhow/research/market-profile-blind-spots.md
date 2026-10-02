---
q: market profile finds no trend following or mean reversion, why nothing passes, horizons, D1 context, exit sweep, cost bar, BH correction and draws floor, power per asset, clock measures, prior vs measured
tag: 🔬  date: 2026-10-02  see: research/market-profile-block-length
---
# The profile's blind spots were real, and widening it changed the verdict little: cost and power are the wall
Widened from 31 measures (lookback <= 55 bars, fixed exits, no D1 context) to 99 plus a 53,352-variant exit/parameter sweep: 2 cell-families pass naked (was 1), 3 sweep variants, none on a plateau.
Reversion is everywhere and pays 0.2x cost; conditioning, target exits and longer holds do not lift it to 2x.
Trend is at or below chance at every horizon on one asset: 3-12 trades a year need a per-trade mean/sd of ~0.5 to show in 8-10 years (documented: 0.2-0.35). Index dip-buying pays 6-18x gross at 5-8 trades a year, p 0.07-0.17.
⚠️ Tests x draws: with 14,364 tests and 1,000 draws only a p at the floor can be significant — use 3,000 draws, or the normal tail of z (0.88-1.12 of the counted p).
One Benjamini-Hochberg over all tests is the LENIENT choice for sparse families: they borrow the dense ones' threshold.

## Evidence
`AlgoData/research/profiles/measures.csv` (3,000 draws), `sweep/variants.parquet`, `variance_ratio.csv`.
Raw p<=0.05 rate of trade measures (chance 5 %): tendencia 1.3 % of 2,929; long-horizon trend 0.8 % of
1,703; `run3_fade` 87.5 %; `rsi2_sma5` 68/63/39/5 % on M15/M30/H1/H4, median multiple 0.19-0.30.
Significant trade measures failing only on cost: M15 155/158, M30 112/116, H1 57/64, H4 17/21.
Corrections: headline 528 significant / 2 pass; per family 599 / 4; per asset 553 / 6; raw 1,297 / 66.
`connors_d1` long: USA500 13.0x, USATEC 17.2x, DJ30 11.9x, NIKKEI225 6.2x, DAX40 -4.7x; 5-8 trades/yr.
Sweep: best of nine exits lifts the median multiple 0.08 -> 0.57 and entries with a >=2x variant
7 % -> 26 %; 623 significant (574 reversion M15-M30), median 0.3-0.5x. VR(8) < 1 in 69 of 76 cells.
Stouffer by class (assets correlated, so an upper bound): index breakouts long z 2.9-3.1, forex
pullback H1 long 3.1, index `weak_d20_mean` long 2.6 — class-level hints no single cell shows.

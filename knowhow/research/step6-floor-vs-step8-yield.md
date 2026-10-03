---
q: How does the step-6 trades-per-year floor affect step-8 yield and Pass counts?
kw: step 6 trades per year floor 20 25 30 40 50 cost, build acceptance PF floor luck formula, step 8 pass bucket empty, oos_trades_per_year rule 30/20, floating risk grows with frequency, calibration populations validation, criteria.yaml step 8 numbers
tag: 🔬  date: 2026-10-04  see: is-filters-inside-the-build, oos1-oos2-persistence, gate-t-scales, random-entry-nulls, gates-are-owner-decisions, post-selection-bias
---
# A trades/yr floor above 20 costs yield at step 8, and an OOS-frequency rule above the floor empties Pass
Post hoc on 23 calibration populations (87,357 strategies, USDJPY/XAUUSD, trades ≥ 100 & net > 0): keep step 8's
`oos_trades_per_year` rule BELOW the step-6 floor — at 30 / 20 Pass holds 6 strategies, at 15 / 10 it holds 49. Per 1,000
kept (USDJPY H1 long GA, ceiling 75, PF ≥ 1.10): 31.7 at floor 20 · 17.6 at 30 · 8.6 at 50. PF floor 1.10 flat.
🔬 Recalibrated 2026-10-04 (116 base cells): a **35/yr floor loses 81 % of the oos1-robust** on H1 (77 %) and M30 (86 %)
alike, cut afterwards; inside the Build 2.2 vs 7.6 per 1,000, 5.4 vs 32.4 per minute. Quality is flat across bands
(median OOS PF 0.88-0.91); the robust lost are robust again on oos2 at their band's rate (17.1 vs 16.8): cost in
strategies, not proven in edge. Ceiling near 75/yr supported (0.41× the null above it; 🤔 not recomputed by the red team).

## Evidence

- 2026-10-04: `AlgoData/scratch/calib2/redteam/review.md` §C3, `adaptive/RECIPE.md` §1; proposal in `assets/_study.yaml`.
`AlgoData/scratch/calib_final/validation.md` (tables, bootstrap CIs by structure), `s6_grid.csv` (every F × C × PF
× label × group), `s8_sensitivity.csv`, `s8_buckets_by_pop.csv`; scripts `build.py` → `s8.py` (real path:
`facts.per_strategy` → `criteria.resolved` → `criteria.outcomes`; the vectorised twin `emu.py` agrees on all
87,357) → `s6.py`, `s8fun.py`, `s8sens.py`. Mean drift-excess t is flat from 15 to 40 trades/yr (0.31–0.38);
R8 fails 13–17 % of the significant below 25/yr and 35–38 % at 25–40; `exp(3.4/√N)` per strategy is worse than a
flat PF floor at the same kept share; strategies at the t pass line trade a median 23/yr. Floors on the t label alone (drift-excess t ≥ 1.65 & net > 0), lift
on USDJPY H1 long GA: F 20 0.92 [0.83, 1.00] · 25 0.73 [0.58, 0.88] · 30 0.62 · 40 0.39 [0.29, 0.53] · 50 0.24.

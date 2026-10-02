---
q: step 6 trades per year floor 20 25 30 40 50 cost, build acceptance PF floor luck formula, step 8 pass bucket empty, oos_trades_per_year rule 30/20, floating risk grows with frequency, calibration populations validation, criteria.yaml step 8 numbers
tag: 🔬  date: 2026-10-02  see: gate-t-scales, random-entry-nulls, gates-are-owner-decisions, post-selection-bias
---
# A trades/yr floor above 20 costs yield at step 8, and an OOS-frequency rule above the floor empties Pass
Post hoc on 23 calibration populations (87,357 strategies, USDJPY/XAUUSD, built with trades ≥ 100 & net > 0):
keep step 8's `oos_trades_per_year` rule BELOW the step-6 floor (0.75 × / 0.5 ×) — at 30 / 20 Pass holds 6
strategies, at 15 / 10 it holds 49. Continuing per 1,000 kept (USDJPY H1 long GA, ceiling 75, PF ≥ 1.10): 31.7
at floor 20 · 20.8 at 25 · 17.6 at 30 · 11.8 at 40 · 8.6 at 50; same on H4; edge ÷ no-edge stays 5–7×. Floating
risk in R grows with frequency. PF floor: 1.10 flat; ≥ 1.15 on top of a floor ≥ 30 halves the yield again.
What a Build forced above a floor breeds is not measured: A/B it.

## Evidence
`AlgoData/scratch/calib_final/validation.md` (tables, bootstrap CIs by structure), `s6_grid.csv` (every F × C × PF
× label × group), `s8_sensitivity.csv`, `s8_buckets_by_pop.csv`; scripts `build.py` → `s8.py` (real path:
`facts.per_strategy` → `criteria.resolved` → `criteria.outcomes`; the vectorised twin `emu.py` agrees on all
87,357) → `s6.py`, `s8fun.py`, `s8sens.py`. Mean drift-excess t is flat from 15 to 40 trades/yr (0.31–0.38);
R8 fails 13–17 % of the significant below 25/yr and 35–38 % at 25–40; `exp(3.4/√N)` per strategy is worse than a
flat PF floor at the same kept share; strategies at the t pass line trade a median 23/yr. Floors on the t label alone (drift-excess t ≥ 1.65 & net > 0), lift
on USDJPY H1 long GA: F 20 0.92 [0.83, 1.00] · 25 0.73 [0.58, 0.88] · 30 0.62 · 40 0.39 [0.29, 0.53] · 50 0.24.

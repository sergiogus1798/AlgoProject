---
q: gate degradacion_t scale, mark-to-market vs closed-trade mismatch, Lo (2002) t of the Sharpe units bug annualised Sharpe in variance term, t ceiling sqrt(2 years) 3.16, null FPR not comparable, trade_t drift_excess_t which t to judge on, decay.py t
tag: 🔬  date: 2026-10-02  see: sqx-format/daily-equity-bin, research/random-entry-nulls, research/post-selection-bias, research/gates-are-owner-decisions
---
# The gate's three t's are three scales; before 2026-10-02 `degradacion_t` was compressed and capped
Judge on `gate.scorecard.drift_excess_t` (or `trade_t`); never compare a t across these, nor against a null
computed on another one. `degradacion_t` (Lo 2002 on SQX's daily equity: each day's LOW, floating in, `OPEN.md`
#88) ≈ 0.78–0.88 × `trade_t`. A null that books **closed trades** has a daily t ≈ 1.00 × its trade t, so its
FPRs read at the gate's line are 2–4× too high. Scorecards and decay reports from **before 2026-10-02** carry
the bugged t: old 1.3 / 1.65 / 2.0 = new 1.42 / 1.92 / 2.55 on a 5-year oos1 (1.46 / 2.03 / 2.82 on 4 years),
and the old one could not exceed √(2·years).

## Evidence
Bug: `studies/screening/analysis/decay.py` had `sqrt((1 + 0.5 * SR_a**2) / years)` with `SR_a` annualised.
Lo (2002), iid: SE(SR_day) = sqrt((1 + SR_day²/2) / T) → annualised `sqrt((1 + 0.5 * SR_a**2 / 252) / years)`;
the squared term was 252× too large. Known answer: `tests/test_gate_measures.py` (iid days, Sharpe ≈ 8 → t > 15
where the old cap was 3.16).

Re-run of the gate on the same harvests, old scorecard against new (`reports/<P>/Results/<day>/gate`):

| population (reached `degradacion`) | new/old median · p95 | old ≈ 1.3 / 1.65 / 2.0 → new | max old → new | ≥ 1.65 old → new | `trade_t` ≥ 1.65 | `drift_excess_t` ≥ 1.65 |
|---|---|---|---|---|---|---|
| `Test_Calib_USDJPY_H1` (Donchian long, 4,515) | 1.05 · 1.17 | 1.42 / 1.90 / 2.61 | 2.24 → 3.11 | 232 → 565 | 957 | 449 |
| `Test_Calib_USDJPY_H1_freeL` (2,720) | 1.03 · 1.12 | 1.42 / 1.92 / 2.54 | 2.24 → 3.13 | 43 → 130 | 431 | 183 |

The ratio grows with the Sharpe (1.00 at t ≈ 0, 1.2 above old 1.65), so rankings are unchanged and counts
above a line are not. New `degradacion_t` / `trade_t`, median over `trade_t` > 1: 0.88 and 0.78.
Mark-to-market vs closed (red team, `AlgoData/scratch/calib_redteam/review.md` §2, 200 strategies from raw
trades): daily sd 1.21×, lag-1 autocorrelation −0.09 vs 0.00, plain daily t 0.82× the trade t, closed-trade
daily t 1.00×, Newey-West daily t 0.95×.
`drift_excess_t` = the toolkit's `t_ex_ar1_oos` to 4e-16 on 5,048 strategies (its t's were checked against
statsmodels); definition in `studies/screening/analysis/tradelevel.py`.

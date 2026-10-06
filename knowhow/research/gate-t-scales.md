---
q: Why can the gate's three t statistics not be compared with each other?
kw: gate degradacion_t scale, mark-to-market vs closed-trade mismatch, Lo (2002) t of the Sharpe units bug annualised Sharpe in variance term, t ceiling sqrt(2 years) 3.16, null FPR not comparable, trade_t drift_excess_t which t to judge on, decay.py t
tag: 🔬  date: 2026-10-04  see: sqx-format/equity-reconstruction-usdjpy-gap, drift-term-biased-by-side, sqx-format/daily-equity-bin, research/random-entry-nulls, research/post-selection-bias, research/gates-are-owner-decisions
---
# The gate's three t's are three scales; before 2026-10-02 `degradacion_t` was compressed and capped
Judge on `gate.scorecard.drift_excess_t` (or `trade_t`); never compare a t across these, nor against a null
computed on another one. `degradacion_t` (Lo 2002 on SQX's daily equity: each day's LOW, floating in, `OPEN.md`
#88) ≈ 0.78–0.88 × `trade_t`. A null that books **closed trades** has a daily t ≈ 1.00 × its trade t, so its
FPRs read at the gate's line are 2–4× too high. Scorecards and decay reports from **before 2026-10-02** carry
the bugged t: old 1.3 / 1.65 / 2.0 = new 1.42 / 1.92 / 2.55 on a 5-year oos1 (1.46 / 2.03 / 2.82 on 4 years),
and the old one could not exceed √(2·years).

`drift_excess_t` itself is side-biased (long vs short, ±0.02-0.27 t): `drift-term-biased-by-side.md`.

## Evidence
**Which line is live (🔬 2026-10-04, OPEN.md #91):** the old 1.65 = 1.92 on the corrected scale (oos1 of 5.16 years).
No live rule reads that t (`min_t` = 0.0); the live rule is R3 of `pipeline/autopilot/criteria.yaml`,
`drift_excess_t` ≥ 2.33, which was never on the old scale. FPR under the null, H1, 40-100 trades/year,
median cell [worst cell]: R3 ≥ 2.33 with costs 0.00 % [0.23], **without costs 0.58 % [1.08]**; R3 at 1.65 with
costs 0.07 % [1.8], without 3.6 % [5.8]. Corrected 1.42 / 1.92 / 2.55: FPR 0.15 % [7.8] / 0.02 % [2.4] / 0.00 % [0.24];
left on the old lines 0.24 % [10.3] / 0.07 % [5.2] / 0.02 % [2.5]. Which null defines «has edge» (with or
without costs) is the owner's call. **The null of 2026-10-01 no longer exists** (closed trades, bugged formula);
`scratch/null2` (deleted 2026-10-06) replaced it, costs identical to today's asset cards: its cost drag is 0.84-1.04× that of six real
random-generation populations, and re-costing moves the FPR ≤ 1.3×. Still-live reports from before 2026-10-02:
only XAUUSD/OOS (MANTENER 4 → 25 of 231).

Bug: `studies/screening/analysis/decay.py` had `sqrt((1 + 0.5 * SR_a**2) / years)` with `SR_a` annualised.
Lo (2002), iid: SE(SR_day) = sqrt((1 + SR_day²/2) / T) → annualised `sqrt((1 + 0.5 * SR_a**2 / 252) / years)`;
the squared term was 252× too large. Known answer: `tests/test_gate_measures.py` (iid days, Sharpe ≈ 8 → t > 15
where the old cap was 3.16).

`drift_excess_t` = the toolkit's `t_ex_ar1_oos` to 4e-16 on 5,048 strategies (its t's were checked against
statsmodels); definition in `studies/screening/analysis/tradelevel.py`.

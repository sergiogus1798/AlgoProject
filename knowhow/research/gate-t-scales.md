---
q: Why can the gate's three t statistics not be compared with each other?
kw: gate degradacion_t scale, mark-to-market vs closed-trade mismatch, Lo (2002) t of the Sharpe units bug annualised Sharpe in variance term, t ceiling sqrt(2 years) 3.16, null FPR not comparable, trade_t drift_excess_t which t to judge on, decay.py t
tag: 🔬  date: 2026-10-06  see: sqx-format/equity-reconstruction-usdjpy-gap, drift-term-biased-by-side, sqx-format/daily-equity-bin, research/random-entry-nulls, research/post-selection-bias, research/gates-are-owner-decisions
---
# The gate's three t's are three scales; before 2026-10-02 `degradacion_t` was compressed and capped
Since encargo 65 (2026-10-12) step 8 judges on `gate.scorecard.z_mono` alone; the t's below are columns. Never compare a t across these, nor against a null
computed on another one. `degradacion_t` (Lo 2002 on SQX's daily equity: each day's LOW, floating in, `OPEN.md`
#88) ≈ 0.78–0.88 × `trade_t`. A null that books **closed trades** has a daily t ≈ 1.00 × its trade t, so its
FPRs read at the gate's line are 2–4× too high. Scorecards and decay reports from **before 2026-10-02** carry
the bugged t: old 1.3 / 1.65 / 2.0 = new 1.42 / 1.92 / 2.55 on a 5-year oos1 (1.46 / 2.03 / 2.82 on 4 years),
and the old one could not exceed √(2·years).
Variants a, b of the drift term are side-biased (`drift-term-biased-by-side.md`); a no-edge strategy crosses 1.65 4 % gross, ~0.9 % net, not 5 % (Evidence).

## Evidence
`drift_excess_t` with the mean-bar term (variants a, b) is side-biased, ±0.05-0.33 t; the blind-trade term (c, d)
leaves ≤ 0.06: `drift-term-biased-by-side.md`. A no-edge strategy does NOT cross 1.65 5 % of the time: 🔬 2026-10-06,
240,000 random-entry strategies, gross of costs, 4.0-4.5 % by formula (plain iid 4.0, plain AR(1) 3.7, skew-kurt iid
4.4, skew-kurt AR(1) 4.05), net of oos1 costs 0.7-1.0 % — R3's line lets through ~90 per 10,000, not 390.

**Which line is live (🔬 2026-10-04, OPEN.md #91):** the old 1.65 = 1.92 on the corrected scale (oos1 of 5.16 years).
No live rule reads any of these t's (`min_t` = 0.0; R3 is a column since encargo 65): the live rule is
`z_mono` ≥ Φ⁻¹(1 − 0.01/B), B = the cell's `batches_screened`, in `pipeline/autopilot/criteria.yaml` step "8". The FPRs below are R3's, kept as the t-scale record. FPR under the null, H1, 40-100 trades/year,
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

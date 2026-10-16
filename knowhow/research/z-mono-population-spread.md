---
q: Is a real population's z_mono distributed N(0, 1), so that its pass rate above the step-8 line means anything?
kw: z_mono spread 0.47, population mean 0.82, empirical null, common batch shift, pass rate 6 of 7356, below N(0,1) tail, IS recipe outcome
tag: 🔬  date: 2026-10-16  see: research/gate-monkey-z-tracks-drift-t, research/monkey-restricted-to-the-strategys-hours, research/gate-t-scales
---
# No: in a real batch z_mono is narrow and shifted (V, USATEC H1 long breakout: mean +0.82, sd 0.47), so read it within the population
7,356 strategies of `Test_USATEC_H1_breakoutL_v8b_leaseWeb` (step 8, 2026-10-15): quantiles 1/5/50/95/99 % = −0.12 / 0.10 / 0.80 / 1.62 / 1.93; 342 above 1.645 (N(0, 1): 5 %), **6 above 2.326 (0.08 %, N(0, 1): 1 %)**, 2 above 2.576. The batch sits *above* the monkey on average — not worse than random — but its spread is half a standard normal's, so the theoretical tail is never reached. Same shape as encargo 65 §5.3's empirical null (δ₀ ≈ σ₀ ≈ 0.55, D11).
Consequence: a pass count above the N(0, 1) line has ~6 events per batch and cannot rank IS filters; compare strategies by rank or by z referred to the batch's empirical null (encargo 50 §5.2 R1). Not: «real strategies pass less often than random entries» — the planted null's 0.78 % (encargo 50 header) is monkeys judged as strategies, a different population.

## Evidence
`AlgoData/autopilot/Test_USATEC_H1_breakoutL_v8b_leaseWeb/20261015-202229/paso-8/hechos.parquet`, key `gate.scorecard.z_mono` (7,356 non-null), with `gate.scorecard.mono_p` (corr with Φ⁻¹(1 − p) = 1.0). Measured 2026-10-16 with pandas quantiles and counts against `scipy.stats.norm.sf`.

---
q: Does correcting the DSR's n for autocorrelation of daily P&L change which SQX strategies pass?
kw: deflated sharpe effective n; n_eff Newey-West Bartlett; autocorrelated daily returns; DSR 0.95; plateau.effective_n; trials.deflated_autocorrelated; encargo 75 E2
tag: 🔬  date: 2026-10-16  see: research/trade-t-vs-frequency-and-skew
---
# SQX builds' daily P&L has no positive autocorrelation: the effective-n DSR moves 14 of 64,261
`n_eff = n/(1+2·Σ w_k ρ_k)` (Bartlett weights, Newey–West lag `floor(4(n/100)^(2/9))`, capped at n)
leaves n untouched for 98 % of strategies: their autocorrelation sum is ≤ 0. It is a guard for
strategies that hold positions over days, not a correction today's populations need.
Production DSR still uses n; the alongside version (`core.surface.plateau.effective_n`,
`ledger.trials.deflated_autocorrelated`) waits for the owner's decision (encargo 75 E3).

## Evidence
Step-8 harvests, 66 of them, build IS daily P&L, σ = population spread of per-day Sharpes,
N = population size, pass = DSR > 0.95: 1,472 pass with n, 1,458 with n_eff. The 14 that drop
were all marginal (0.950–0.955 → 0.944–0.949), all in Test_USDJPY_M30_doubleROCLong_10k_B2/B3/B5.
n_eff/n = 1.000 at p10, p50 and p90; the largest DSR change was 0.0244. Store: 681 of 890 matched
to a harvest (via store/identity-map-2026-10.csv); 38 pass under both, 0 change, max change 0.0126.

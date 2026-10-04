---
q: Can the SPP's IS-vs-OOS1 decay metrics (median ratio, Vargha–Delaney A, W1/IQR) tell a zero-edge family from a real one?
kw: spp criteria decaimiento mediana vargha delaney wasserstein IQR distancia original zero-edge null path noise 1/sqrt(years) kill rule diagnostic not criterion verdict_csv a_sharpe
tag: 🔬  date: 2026-10-04  see: post-selection-bias
---
# With a 4-year OOS1 the SPP decay metrics cannot tell zero edge from the real thing: diagnostics, not criteria

`studies/breakage/spp/model/decay.py` computes them, `spp.verdict_csv.*` publishes them, no rule
reads them. Every permutation shares ONE price path, so a zero-edge family's OOS1 grid sits at
Sharpe 0 ± 1/√years (±0.5 at 4 years), which covers «no decay» for any IS median below ~0.8.
Set a threshold only after an SPP on a zero-edge population or on a longer OOS; the quantiles a
threshold is read from are below.

## Evidence
`studies/breakage/spp/model/decay.py` computes them, `spp.verdict_csv.*` publishes them, no rule reads
them. All three (ratio of medians, A, W1/IQR(IS)) only say where the OOS1 grid sits against the IS
grid, and every permutation shares ONE price path: a zero-edge family's grid median is 0 ± 1/√years
of annualised Sharpe (±0.5 at 4 years), which covers "no decay" for any IS median below ~0.8.
Separation is d′ = median(IS)·√years_OOS; N permutations is not a sample size, so no p-value.
The original-vs-median distance has no zero-edge null at all (no SPP of null strategies exists):
its only null is "a random member of its own grid". Set a threshold on any of them only after an
SPP on a zero-edge population, or on a longer OOS.

`Trade_NIKKEI225_M30_volatilidadL`, 10 strategies, ~13,900 permutations a side, IS 8 y, OOS1 4 y.
Null: OOS1 grid keeps its shape, centre drawn — Sharpe N(0, 1/years); Sortino the same × IQR(Sortino)/
IQR(Sharpe); Profit Factor of a per-trade mean N(0, 1/median trades), normal trades; R/Edge: no model.
Quantiles 5/25/50/75/95 — real (across the 10) | null (median across the 10 of each quantile):

| metric | real | zero-edge null | real beyond null p95 (good side) |
|---|---|---|---|
| ratio Sharpe | 0.29 0.84 0.94 1.36 1.62 | −1.60 −0.67 0.00 0.67 1.60 | 0 / 9 |
| A Sharpe | 0.25 0.46 0.51 0.62 0.76 | 0.00 0.04 0.14 0.36 0.75 | 0 / 10 |
| W1/IQR Sharpe | 0.17 0.25 0.32 0.59 1.52 | 0.29 0.71 1.43 2.27 3.54 | 3 / 10 (below p5) |
| ratio Sortino | 0.28 0.75 0.91 1.36 1.57 | −1.79 −0.75 0.00 0.75 1.79 | 0 / 9 |
| A Sortino | 0.23 0.42 0.49 0.60 0.74 | 0.01 0.06 0.17 0.41 0.78 | 0 / 10 |
| W1/IQR Sortino | 0.19 0.27 0.44 0.66 1.69 | 0.27 0.69 1.29 2.06 3.24 | 2 / 10 |
| ratio PF | 0.78 0.84 0.94 0.96 0.98 | 0.52 0.63 0.71 0.81 0.96 | 2 / 9 |
| A PF | 0.21 0.33 0.42 0.45 0.66 | 0.04 0.09 0.15 0.26 0.48 | 3 / 10 |
| W1/IQR PF | 0.21 0.28 0.34 1.16 2.37 | 0.30 0.67 1.02 1.29 1.69 | 3 / 10 |
| distance of the original, in IQR (12 metric × side) | medians −0.27 … +0.39 | own grid p5/p95 ≈ −1.2 / +1.3 (Sharpe, Net Profit), −0.8 / +1.9 (PF, Ret/DD, DD) | 0 / 120 outside |

In % of the median the same distance spans −53 … +147 % (Net Profit, Ret/DD): «± 30 %» fails half of
originals that sit well inside their own grid. Reproduce: scratch `criteria/spp_null.py` logic =
`decay.measure` per strategy; test `tests/test_spp_decay.py`.

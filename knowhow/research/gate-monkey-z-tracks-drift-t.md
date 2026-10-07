---
q: Does the gate's monkey z add information beyond R3's drift-excess t on a cost-bound asset?
kw: z_mono drift_excess_t correlation 0.97, monkey vs drift term, level 3c, windowed monkey, USA500 indicesIBS, drift equals cost, gate monkey timing cost per strategy
tag: 🔬  date: 2026-10-06  see: monkey-reprice-audit, drift-term-biased-by-side, gate-t-scales
---
# On USA500 H1 the monkey's z is the drift-excess t again: drift is about cost, so the monkey adds no second opinion
`z_mono` (level 3c, `engines.nulls.windowed`) correlates 0.971 / 0.985 / 0.974 / 0.992 with `drift_excess_t` (variants a / b / c / d); none of 300 strategies reaches 1.65 on either. Mean `z_mono` 0.50 against t -0.07 (b) or 0.23 (d), almost the t of raw P/L (0.52): the monkey pays costs, R3's drift term does not, and drift is about cost on this asset. Do not expect level 3c to rescue or reject what R3 decided here. The Monte Carlo matches the exhaustive null. Cost: 0.23 core-s per strategy at 5,000 draws x 4 rungs (113 trades median), ~10 MB, linear in draws x trades (~60 ns per valuation): 20,000 strategies ≈ 19 min on 4 cores.

## Evidence
USA500 H1 indicesIBS, first 300 identities, seed 7, 5,000 draws (2026-10-06).
- Exhaustive null, one 90-trade strategy: monkeys' mean -6.16 ± 2.37 against an expectation of -2.55 over every eligible bar; flat-size rung 6.35 ± 1.75 against 5.82.
- Known answers: `tests/test_gate_mono.py`.

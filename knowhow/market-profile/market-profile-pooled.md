---
q: Does pooling the market profile by asset class find edges that pay?
kw: pooled market profile, group test asset class, Stouffer joint resampling cross-correlation, shrunk effect empirical Bayes random effects, how many board cells pooling adds, reversion forex pays below cost, day_down_volhigh
tag: 🔬  date: 2026-10-02  see: market-profile-power, market-profile-block-length
---
# Pooling by asset class names 142 group tests, and almost none pays: the edges it finds are 0.2-0.6 costs
`studies/research/pooledProfile`: 142 of 2,543 group tests pass BH 5 % (99 with trades; in 25 no asset passed
alone). They are reversion and pattern in forex and metal; median excess 0.37 round-trip costs. Only 4 reach
2 costs: `day_down_volhigh_1d` long in forex on M15, M30, H1 (2.0-2.1 costs, tau 0, no pair alone) and
`bar2atr_up200` long in metal H4 (5.5 costs, 5-8 trades a year). No trend or breakout group passes.
Board: 218 cell-families by the loose route (148 new), 3 by the strict one (shrunk effect pays, stable,
frequent) — all three already there. So: pooling shows the naked reversion is real and below cost; it is
not a route onto the board. Placebo worlds name nothing (0 of 200). ⚠️ Joint resampling = one seed per group + shared bar times.

## Evidence
`python3 -m studies.research.pooledProfile.report --judge-only` → `AlgoData/research/pooled/tests.csv`,
`assets.csv`, `board.csv`, `run.json` (seed 20261002, 3,000 joint draws, 76 cells, ~5 h at 2 workers).
`tests/test_pooledprofile.py`: four identical assets → the null sum spreads 2.00×, not 1.
BH over 2,543 tests with a p floor of 1/3001 needs ≥ 17 tests at the floor to name any: the draws bound it.

---
q: cross-market parameter surface, same parameter region on two markets, Spearman between markets confounded, exposure times drift, long-only net profit ranks, rho_neutral, market surfaces encargo 15
tag: 🔬  date: 2026-09-26  see: research/cloud-ranking-stability
---
# Between two markets, a long-only net-profit ranking is partly time-in-market × each market's drift
Two markets that drifted apart rank the variants **against** each other by exposure alone, so a raw
cross-market Spearman of net profit mixes "the same region" with "stays in longer". Read it beside
the rho with each market's own exposure removed (`marketSurfaces` `rho_neutral`); a call on raw rho
alone over-reads the negative pairs. Within one market the WFC does not suffer this (one drift).

## Evidence
- 🔬 2026-09-26, 3 USDJPY mothers × 5,000 variants × 9 pairs, build/oos1, provisional costs:
  23-1-46 oos1 USDJPY net profit vs its own exposure −0.73; USDJPY vs AUDUSD −0.70 raw (−0.87 on
  distinct results), −0.39 once each side's exposure rank is regressed out. 6-1-69 build EURUSD −0.36 → −0.10.
- Synthetic (tests/test_marketsurfaces.py): two markets rewarding only exposure with opposite
  drifts read rho −0.92 raw and −0.02 neutral.
- The call of all three mothers (region does not travel) holds under both readings.

---
q: How much edge can the market profile detect, and below how many trades a year is it blind?
kw: market profile power, minimum detectable effect, 2 of 1064 finding or blindness, positive controls, planted edge, how small an edge the profile sees, cut p 0.00167, trades per year needed, H4 blind
tag: 🔬  date: 2026-10-02  see: market-profile-block-length, market-profile-pooled
---
# The market profile sees a 2-cost edge in 31 % of its tests: under ~100 trades a year it is blind
At the raw p the map's correction demands (0.00167, z 2.93) a measure names an excess with 80 % power only
from 3.78 standard errors. Median over the 10,926 trade tests: 4.6 round-trip costs (0.63 ATR). By trades a
year: <12 → 48 costs · 12-40 → 8.8 · 40-100 → 4.1 · 100-300 → 1.8 · >300 → 0.7. H4 sees 2 costs in 3-5 % of
its tests (forex, index, metal). «Does not pass» below ~100 trades a year is not evidence of no edge.
Not: read a cell's failure as absence; and not: plant huge edges — a plant on many bars becomes drift,
which the null keeps (20 costs detected always, 60 never, `channel20` on noise).
⚠️ A replication forks ~1 GB RSS and the pooled study ~2 GB: 52 workers held 65 GB. Keep ≤ 8.

## Evidence
`python3 -m studies.research.profilePower.report --judge-only` → `AlgoData/research/power/reach.csv`,
`reach_class.csv`, `widened.csv` (normal approximation on `measures.csv`: mde = 3.78 × null_sd × |multiple/stat|;
hit-rate measures `inside`, `engulfing`, `run3_*` left out). Of 1,865 tests paying ≥ 2 costs none has z ≥ 3.78.
617 of 912 cell-families have some ≥ 40-trades measure that would see 2 costs (H4: ruptura 11 %, reversion 34 %).
Size: `tests/test_profilepower.py`, 5.0 % at a nominal 5 % on noise. Simulated on H4 (XAUUSD, EURUSD, USA500;
1,680 replications, 10.6 core-hours, `mde.csv`): channel55 18 costs, rsi2 19, extreme2 19, bar2atr 16,
narrow_break 7.6, run3_follow 1.2; 5-7 trades a year: never, even at 25. Alone at 5 %: 9, 7, 15, 8, 4.4, 0.65.
The simulation detects 9 points less than the approximation (`calibration.csv`): the map's figures are a ceiling.

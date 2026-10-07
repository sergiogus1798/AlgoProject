---
q: Why did a no-edge population read z_conj +0.44 in V1, and what do the index feeds' holes do to a shift null?
kw: holes in index feeds 2011-2015; HK50 UK100 AUS200 USA500 USATEC gap months; displaced share; shift null piles up after a hole; z_conj V1 +0.44; max_displaced_share; travel validity per cell
tag: 🔬  date: 2026-10-07  see: research/crossmarket-returns-miss-entry-offset
---
# Index feeds have months-long holes in 2011-2015; a shift null that lands in one piles every run on a bar
HK50, UK100, AUS200, USA500, USATEC lack whole months (76-180 days). A shifted stamp with no bar takes the
NEXT bar, so random runs pile there; the real run does not: no-edge uniform entries read z_conj +0.44 in V1.
Fix (encargo 46 D3): `tensor.exclude` probes 20,000 blind entries per market; a (market, cell) whose
displaced share exceeds `travel.validity.max_displaced_share` (0.20) is NaN in every run, listed in
`crossmarket.json` `excluded` (bars and cells only). Real bars: 10 pairs fall, all V1; uniform population
V0 +0.01, V1 +0.08, V2 +0.00, full +0.06 +- 0.07. A synthetic clean-block hole did NOT reproduce +0.44.

## Evidence
- `scratch/d2/` scripts and `AlgoData/scratch/paso10_travel/diagnostico-2026-10-07/` (step3_displaced_share.csv).
- Gate rerun through the study code: `AlgoData/scratch/paso10_travel/2026-10-07-huecos-gate/`.

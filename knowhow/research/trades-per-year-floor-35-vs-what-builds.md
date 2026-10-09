---
q: Why do most built strategies fall under step 8's 35 trades/year floor?
kw: trades per year 35 floor R4a, limbo 20-35 fail <20, build acceptance 10-16 trades/year, assets/_study.yaml, cal6 aroon 15 trades per year
tag: 🔬  date: 2026-10-09  see: research/is-filters-inside-the-build, research/step8-gate-measured-on-six-populations
---
# The build accepted 10-16 trades/year while step 8's R4a wanted 35; since 2026-10-09 both ask the same
Until then the acceptance filter in `assets/_study.yaml` took 10-16 trades/year as floor (30 with a ceiling
of 75-100 by default) and the 35 was applied only at step 8, so a slow-trading template built populations
R4a emptied. Owner, 2026-10-09: the build asks 35/year on M15, M30 and H1 and 20 on H4, with no ceiling
and no per-symbol exception; R4a passes at 35 (limbo 20-35), on H4 at 20 (limbo 15-20).

## Evidence
- 🔬 IS trades/year ≥ 35 among the 10,000 built (2026-10-08/09): cal1 6,869; cal2 6,758; cal3 105 (median 23.5); cal4 2,167 (median 20.4); cal5 3,239 (median 27.5); cal6 15 (95th percentile 25.8).
- 🔬 cal6: R4a killed 3,635 and put all 1,352 survivors in limbo.
- 🔬 Of those passing R3 at 1.65, under 35/year: cal1 1/16, cal2 34/87, cal3 0/2, cal4 23/35, cal5 27/39, cal6 1352/1352.

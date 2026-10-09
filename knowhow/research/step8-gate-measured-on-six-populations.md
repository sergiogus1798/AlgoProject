---
q: How many monkeys and how many real strategies cross step 8, and which rules discriminate?
kw: step 8 gate null rate, monkeys surviving step 8, planted edge 0.10 0.15, R2 R3 R4a R5c R9b mae_p95_r, limbo causes, R3 threshold 1.65 2.00 2.33, falsePositives, cal1 cal6
tag: 🔬  date: 2026-10-09  see: research/trades-per-year-floor-35-vs-what-builds, pipeline/monkey-after-cut-has-no-cap
---
# Step 8 passes ~0.3-1.5 % of no-edge monkeys; five real populations sit at or below that, and R9b does not discriminate
Thresholds are the owner's; these are measures, not a change. Raising R3 from 1.65 to 2.33 cuts the null
~6x and the power at 0.10 ~2.3x. No monkey exists for steps 10 and 12 (`falsePositives` applies «0 de 10
reglas» there). A clean «Pasa» at step 8: 1 strategy in all six runs; the rest of the survivors are Limbo.

## Evidence
Six runs, 10,000 strategies each, 30 min build, long only, R3 = 1.65 (2026-10-08/09): cal1 DJ30 H1, cal2 USDCAD M30, cal3 EURJPY H1 template, cal4 GBPUSD H1, cal5 DAX40 M30, cal6 NIKKEI225 H1 template. Reports `AlgoData/reports/Test_<...>_calN/`.

| share surviving step 8 (pass+limbo) | cal1 | cal2 | cal3 | cal4 | cal5 | cal6 |
|---|---|---|---|---|---|---|
| 5,000 no-edge monkeys % | 1.5 | 0.56 | 1.26 | 0.34 | 0.68 | 0.90 |
| planted edge 0.10 % | 34.9 | 22.2 | 23.4 | 17.5 | 22.1 | 14.7 |
| planted edge 0.15 % | 58.6 | 33.7 | 40.1 | 29.4 | 37.2 | 25.5 |
| real, of 10,000 (count) | 9 | 74 | 2 | 32 | 33 | 1,352 |
| reals passing R3 at 1.65 / 2.00 / 2.33 | 16/7/0 | 87/29/12 | 2/0/0 | 35/9/3 | 39/14/8 | 1352/712/271 |

- Only cal6 is above the null: 10,000 near-clones of one fixed Aroon cross on an index that rose in oos1, all with <35 trades/year.
- R2 (net oos1 > 0): reals pass 28, 40, 6.5, 24, 40 % (cal1-5) vs 48, 54, 43, 32, 50 % of no-edge monkeys: worse than random entry on oos1 net; cal6 86 %.
- R9b `mae_p95_r`: same pass rate at every planted level (33, 2.7, 24.8, 61.8, 18 %), so it does not discriminate edge, yet it is a main limbo cause (56 of 74 in cal2, 21 of 33 in cal5).
- R5c (`t_sin_3_mejores`/`t_sin_mejor_trimestre`) puts 33 of 34 (cal4) and 27 of 33 (cal5) in limbo.
- Joint R2+R3 pass of monkeys null / 0.05 / 0.10 / 0.15, range over six runs: R3 1.65 → 1.1-1.7 / 12-18 / 25-40 / 44-65 %; 2.00 → 0.4-0.8 / 6-11 / 15-28 / 30-52 %; 2.33 → 0.2-0.3 / 3-6 / 9-19 / 18-40 %.

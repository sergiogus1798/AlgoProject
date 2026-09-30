---
q: portfolio worst intraday floating loss per day; sum of members' daily worst vs exact; M5 vs M1 resolution for prop-firm daily loss; cost of a minute-level portfolio path; Monte Carlo at M5; how to rank combinations by intraday drawdown cheaply
tag: 🔬  date: 2026-09-30  see: export/mae-mfe-from-m1, perf/ram-budget
---
# A portfolio's worst intraday floating: M5 blocks give the M1 answer at 1/11 of the cost; summing members' daily worsts overstates it ×1.6
Per member, keep the worst floating of each 5-minute block (float32, ~7 MB over 14 years); a combination's day-worst is the
min over blocks of the members' sum — equal to exact M1 on the test, 20 ms for 10 members vs 224 ms at M1. Summing each
member's own daily worst (the free bound) reads the loss ×1.57 median, ×2.89 p95 too deep and punishes diversification.
No Monte Carlo needs intraday resolution: resample whole days, each carrying its exact intraday worst.

## Evidence
- Scratch benchmark 2026-09-30, `USDJPY_DukasM1_the5ers` (8,734,300 bars), 10 members = the archived USDJPY strategy
  (`4d679e…`, 2,094 long trades) shifted by 0, 37, 113, 241, 419, 601, 787, 1013, 1301, 1567 bars — synthetic, same
  strategy: cost and resolution are representative, the size of the bound's error on real independent members is not.
- 3,146 days with a position: bound / M1 median ×1.572, p95 ×2.890, worst day −64,882 $ vs −58,231 $;
  M5 / M1 median ×1.000, p95 ×1.000, worst day −58,231 $ both.
- Per member: M1 path 0.022 s, to M5 0.040 s, daily worst 0.004 s. Per 10-member combination: bound 0.27 ms, M5 20.2 ms,
  M1 224 ms. M1 array 69.9 MB (float64), M5 array 7.0 MB (float32).
- 🤔 Members on different feeds, or strategies entering off the half-hour grid, may put extremes inside one 5-minute block at
  different minutes; M5 is then conservative by at most one block — to re-measure on a real multi-asset pool.

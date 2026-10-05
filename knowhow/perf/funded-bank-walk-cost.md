---
q: How long does the funded bank walk take per configuration, on one core and on 8 threads?
kw: bank simulation cost per configuration, stage C ms per plan add-on risk, portfolio.funded.sim kernel speed, 10000 draws 1250 days numba prange, how long the bank table takes, PLAN 14.3 estimate 30-60 ms
tag: 🔬  date: 2026-10-02  see: perf/ram-budget
---
# The bank walk costs ~115-130 ms per configuration on one core, 30-70 ms on 8 threads (10,000 draws × 1,250 days)
PLAN §14.3's 30-60 ms is met only with threads, not on one core — measured with the machine at load
87 of 96, so the idle figure is lower. A whole table (11 plans, singles of add-ons, 3 × 3 risk levels =
1,305 configurations + monkey + 5 haircuts) on 2,000 × 1,250 paths: 4.4 s wall, 38 s CPU, 8 threads.
Memory is the path set: 4 float64 arrays + 1 int32 = 450 MB at 10,000 × 1,250, plus one `closed` and
one `low` copy per haircut (200 MB each) and the monkey's.

## Evidence
`bank.simulate`, median of 7, synthetic paths, 2026-10-02 13:57: Hantec Express 10k 132.7 ms (1 thread)
/ 69.2 (8); FTMO 2-step 115.7 / 31.0; Hantec Endurance 115.4 / 42.1. Full-scale command:
`python3 -m portfolio.funded.sim.run --paths <10k×1250.npz> … --set compute.threads=8`.
2026-10-05, first run on a real portfolio's path set (10,000 × 504 days, both re-buy policies, 2,610
configurations + monkey + 5 haircuts), other jobs on the machine: 86-88 s wall, 368 s CPU = 33 ms per
configuration. `frompool` (drawing the paths, T2@2, K = 4): 11.6 s. Perf target `portfolio.funded_bank`.


---
q: How long does Stage B take per 10-member combination, and what dominates its cost?
kw: cost of stage B funded search; Monte Carlo paths per second trade bootstrap; T1 T2 D cost; 10,000 paths 126 days risk grid per phase; how long does funded_b take; selected null cost; numba prange trade laying
tag: 🔬  date: 2026-10-02  see: perf/intraday-floating-resolution, perf/ram-budget
---
# Stage B: ~17 s per 10-member combination on 8 busy threads; laying whole trades is the cost, the rules and the risk grid are free
One combination at full size — 11 path sets (D and T2 at five lengths, T1) × 10,000 paths × 126 days × 100 risk settings
(two phases × 10 levels) — costs 16.7 s at K = 10 and 10.8 s at K = 5 on 8 numba threads, 0.47 GB. Per 10,000 paths: T1 4.1 s,
T2 2.2 s, D 0.15 s; the rule machine over all 100 settings 0.1 s. So 50 finalists ≈ 14 min on 8 threads. The selected null
repeats stage B once per null search: 100 searches ≈ 100× that — the verdict, not stage B, is what needs the whole machine.

## Evidence
- Scratch benchmark 2026-10-02, load average 130 (another team's job on the custodian), `NUMBA_NUM_THREADS=8`: synthetic
  members of 1,300 trades over 2,600 days, 6-480 five-minute blocks each (316,000 blocks per member), plans
  `hantec:enhanced:10000:USD` and `ftmo:2step:10000:USD` (same figures).
- Exact M1 part (`stageb_data.prepare`) on the archived USDJPY strategy (8.7 M bars, 10-year build, 1,357 trades): one
  member 6.2 s, worker peak 2.5 GB (`stageb.worker_ram_gb`), 4.5 M minutes × 2 float32 kept per member (36 MB); folding a
  combination's minutes into its days 0.45 s.
- 🔬 2026-10-05, first real pool (`Test_nikkei_ref`, test root; 10 Nikkei M30 members of ~350 trades in build, one-phase
  `hantec:express`): 11 finalists of K = 2-4 × 10 risks, the stability re-draws included, 18.5 s wall at 15 cores
  (272 s CPU), 1.84 GB peak RSS. Perf target `portfolio.stage_b` (synthetic K = 5, two phases): 4.0 s wall, 46 s CPU, 670 MB.
- 🤔 Not measured: 48 idle cores; a three-phase plan (1,000 settings: the rules' share ×10, still under the laying).

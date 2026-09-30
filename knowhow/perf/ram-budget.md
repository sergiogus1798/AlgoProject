---
q: RAM budget SQX installs vs Python, -Xmx per install master W1 W2, jstat -gc live set vs RSS, JDK tools in install j64/bin, -Xms idle worker, PC-A PC-B, how much heap does SQX need
tag: 🔬  date: 2026-09-23  see: perf/server-cores-and-ram, perf/smt-in-sqx-retest
---
# RAM budget: W2 -Xmx80g + all cores; size heaps from jstat's live set, not RSS
Current (owner, 2026-09-23, PC-A): W2 `-Xmx80g`, `coreUsage -1`; Python reserve 20 GB; OS 10–12 GB. **Exception (owner,
2026-09-30): the portfolio engine may take all cores and up to 80 GB** — so it runs when the custodian is idle. Master as viewer `-Xmx12g`
fits beside a full W2; master generating at 24g does not (swap 4 GB, overflow is OOM-killed).
Heap = 1.5 × live set (`OU + EU` from `jstat -gc`). Keep `-Xms` low (1g/2g) on workers. A Python reserve costs nothing until used;
an `-Xmx` is spent once granted. Verify a heap figure on disk: `grep Xm <install>/*.config`.

## Evidence
```
Σ(-Xmx) ≈ (RAM_total − 5_OS − Python_reserve) / 1.08      # 1.08 = JVM overhead beyond heap
```
- ⚠️ Master RSS 67.5 GB looked like need. `~/Desktop/SQX/j64/bin/jstat -gc 3385011`: EC 12,711,936 KB / EU 0; OC 47,538,176 KB / OU 16,686,751 KB;
  YGC 252 (21.3 s), FGC 39 (41.9 s) → committed 57.4 GB, live 15.9 GB (`-Xmx108g` + `UseParallelGC` never collected) → `-Xmx24g`.
- A doc once claimed the master was resized when `StrategyQuantX.config` still read `-Xmx108g` (mtime 2026-09-19); applied for real 2026-09-21, read back.
- JDK tools in the install, not on `PATH`: `~/Desktop/SQX/j64/bin/{jstat,jcmd,jinfo,jps}`. Use `jstat` on the owner's master (reads shared perf
  counters, never attaches). `FGCT` growing more than a few s/hour → heap too small.
- Python doesn't compete: worst catalogue target `montecarlo.analyse_long` peaks 2.5 GB, `montecarlo.analyse` 0.33 GB (`AlgoData/profiling/history.csv`, 2026-09-21).
- Idle worker with shipped `-Xms4g` (`sqcli.config`) holds 4 GB doing nothing.
- Revision applied to `SQX_w2/sqcli.config` and `settings.xml` with the install stopped.

| | PC-A 96c / 125 GB | PC-B 16c / 128 GB |
|---|---|---|
| binding constraint | RAM | CPU |
| M / W1 / W2 `-Xmx` | 24 / 16 / 80 GB (W2 48 until 2026-09-23) | 24 / 16 / 48, not yet applied |
| M / W1 / W2 `coreUsage` | −1 / 8 / −1 (W2 48 until 2026-09-23) | −1 / 2 / 8 |
| 5,000-variant retest | 3.5 min | ~21 min |

Not: raise heaps because RAM is free (PC-B) — buys only uncollected garbage. 🤔 On PC-B the custodian role matters more: the window where a stray command destroys work is 6× wider.

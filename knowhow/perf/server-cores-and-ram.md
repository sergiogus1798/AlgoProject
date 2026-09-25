---
q: how many cores does the server have, 48 physical 96 logical SMT siblings, os.cpu_count lies, max_workers, STREAM bandwidth oversubscription, SQX Xmx108g memory reserved, comput threads
tag: 🔬  date: 2026-09-19  see: perf/ram-budget, perf/smt-in-sqx-retest, perf/monte-carlo-bandwidth
---
# 48 physical cores, not 96; SMT and oversubscription lose bandwidth
AMD EPYC 7413, 2 sockets × 24 cores × 2 threads, one NUMA node; SMT siblings `cpu N` ↔ `cpu N+48`.
`os.cpu_count()` = 96 is the worst point of the curve for memory-bound kernels: set `max_workers` between 24 and 48 (🤔).
Nothing limits CPU (affinity `0-95`, no `cpu.max`/`cpuset`/`memory.max`). RAM is the scarce resource: SQX JVM heaps are anonymous and unrecoverable while open.

## Evidence
- Siblings: `/sys/devices/system/cpu/cpuN/topology/thread_siblings_list`. Idle SQX GUI: 0.8 % of one core.
- SMT subtracts: 96 procs on 48 physical 211,419 paths/s vs on 96 logical 203,617.
- Compute-bound control (8 KB, L1) 46.1× at 95 procs; real kernel 18.3× with 85.6/96 cores "busy" (waiting on DRAM).
- STREAM-like triad: 143.7 GB/s at 24 procs, 121.7 at 48, 101.6 at 95 (96 workers cost 29 %).
- ⚠️ SQX starts with 95 parked `comput` threads (log `Preparing thread executors: 95`); a GUI build competes for the whole machine.
- Memory at 2026-09-19 (current split: `perf/ram-budget`): `~/Desktop/SQX/StrategyQuantX.config` `option -Xmx108g` (GUI up to 108 of 125 GB),
  held 71.5 GB all anonymous (0.1 GB file-backed); `user/settings/settings.xml` `memoryCleanup=false`; `~/Desktop/SQX/sqcli.config` `option -Xmx32g`.
  37.4 GB available, 1.2 GB swap free. MC with `chunk: 2000` × 95 workers needs 32 GB on N=3,437 — fits by 5 GB, not with a worker up (71.5+32+32 = 135 > 125).

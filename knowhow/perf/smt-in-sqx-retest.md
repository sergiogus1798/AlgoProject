---
q: SQX coreUsage how many threads for a retest, 48 vs 95 threads, SMT in SQX, idle sqcli memory, jstat jcmd AttachNotSupportedException, sqcli loads strategies lazily count Records 0, databank load folder, loadconfig name=, Retest status Total tested missing, two sessions on the custodian
tag: 🔬  date: 2026-09-23  see: perf/server-cores-and-ram, perf/ram-budget, sqx-drive/worker-process-lifecycle
---
# An SQX retest scales to the 48 physical cores; 95 threads add only 2–10 %
Set `coreUsage` in `user/settings/settings.xml` with the worker stopped (log confirms `Preparing thread executors: N`).
Master at `-1` (95) and custodian at 48 fight over the same 48 physical cores: concurrent build + retest both run at half speed.
Before touching a worker: `ListAgents`, `ls -lt user/projects`, the log tail — `bin/sqx-worker.sh stop` kills anyone's run.

## Evidence
Custodian `SQX_w2` (`-Xmx48g`), throwaway project `bench_smt`: Retest without SPP/SO, XAUUSD M1 2008-01-01..2026-08-30, MT5 hedged,
2,886 strategies (`Retester/databanks/RetestOut` of 962 loaded three times — `action=load` does not dedupe).

| `coreUsage` | wall | ms/strategy | mean %CPU | clean |
|---|---|---|---|---|
| 24 | 55.5 s | 18 | 1,355 % | ⚠️ no (another session's 2 projects on top) |
| 48 | 31.1 s | 10 | 1,815 % | ✅ |
| 95 (`-1`) | 30.4 s | 9 | 3,114 % | ⚠️ no (4 projects on top) |

24→48 ≈ 1.8×. Contamination biases against 95, so "≤ 10 %" is indicative; repeat with W2 free. 🤔 If the master only views, raising W2 48→95 gains little.
- Idle `sqcli`: 1.9 GB RSS, 160 MB live heap (`jstat`: old 90 MB + survivor 71 MB, 267 threads, `-Xms1g`). 964 loaded, not retested: +350 MB heap
  after young GC (≈0.4 MB/strategy upper bound). 2,886 retested (in + out with results): old gen 5.7 GB at 48 threads, 7.4 GB at 95, no full GC, garbage included.
- `jcmd` fails (`AttachNotSupportedException: The VM does not support the attach mechanism`, jvmci build) — only `jstat`.
- `sqcli` doesn't load project strategies at start: `-databank action=count` → `Records: 0`; `action=list project=X` (or `count` on a databank) triggers
  `Syncing databank(s) from files`. Immediate `action=copy` copies 0 (copies memory). Folder into new databank: `-databank action=load project=P name=D folder=/path` (works fresh).
- `-project action=loadconfig` requires `name=` besides `file=` (`Error: Missing parameter 'name'`); relative `file=` resolves against the install folder.
- ⚠️ Retest-without-SPP `status` has no `Total tested` line (has `Strategies generated`, `Time per strategy`, `Running time so far`, `In databank`);
  `TESTED` regex in `sqx/variants/execute.py` → `None.group` crash. End signal valid for both: `-databank action=count` on the output databank.

Collision (📓 `SQX_w2/user/log/StrategyQuant/log_2026_09_23.log` 07:20–07:37): benchmark `stop`s (07:26:21, 07:27:11, 07:27:42, 07:29:19, 07:30:28,
07:31:37, 07:32:58) killed another session's cost bisection runs (`bisect_sin_costes`, `bis_*`, `chat_keltner_M30`, `ctrl_*`), which ran at a changed `coreUsage`.
A `start` at 07:31:41 opened port 5050 from `SQX_w2` and died with `Database may be already in use: Locked by another` (two processes, one H2).
No tool enforces "don't talk to the custodian while it works": `execute.awake()` respects a live instance, `stop` does not. Pending in `OPEN.md`:
owner lock in `bin/sqx-worker.sh` (`start` records who; another's `stop` refuses without `--force`).

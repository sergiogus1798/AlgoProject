---
q: build an unselected calibration population; relaxed Rankings filters; databank full replaces by fitness; In databank status counts all databanks; passed-count stop; stop project during Build; OOS "(1)" duplicate files; worker killed mid-stop loses retest; free shell template two RandomCondition; nested AND three conditions; afterrun export minutes per stop; build and OOS in one start time-limit; calibration queue cadence; random generation acceptance
tag: 🔬  date: 2026-10-01  see: perf/review-path-after-sqx, conditions/selection-window, research/post-selection-bias, sqx-drive/export-after-every-stop, authoring/one-item-group-can-drift
---
# A Build with only `trades >= 100, NetProfit > 0` accepts 1,000-2,000 strategies a minute — box it with `time-limit`, never let it fill
- The donor's `<Rankings><Conditions>` (trades > 500, Sortino > 0.6, Stagnation < 540, sampleType 127 = the build window, no OOS range in the task) reach every project verbatim; no module writes them. Relaxed by hand in the stopped `project.cfx`, the builder accepts 25-65 % of what it generates.
- Once `Results` holds `MaxStrategies`, a new strategy only enters by beating the worst on fitness: the population becomes "top N by IS Ret/DD". So: `builder --minutes M --max-strategies N` with N out of reach in M minutes (`time-limit`; `databank-full` does not stop at full), Build and OOS both active (`stage --step build,oos`), ONE `action=start`: the Build ends itself at M min and SQX goes on to the retest. Watch `In databank` and send one `action=stop` only if it nears N.
- `In databank` in the status is the sum over the project's databanks, not `Results`.
- An `action=stop` during Build ends the project (the OOS task does not run). A second stop a few seconds later landed on the OOS task that had started and left a partial `OOS`; the next full retest then wrote `Strategy X(1).sqx` beside each survivor (same identity). Empty the output databank on disk, install stopped, before a retest that is repeated.
- A worker killed while `stop` is syncing loses the whole retest databank (it was only in memory) and can leave one torn `.sqx` in the source databank (`zipfile` refuses it). Test the zips before restarting.
- A free `RandomCondition` hole may resolve into a nested `AND` of two conditions: `AND(hole, hole)` gives strategies of 3 conditions (39 % on Donchian+free), and a group-bound hole drifted off its block in 180 of 5026.

## Evidence
- `Test_Calib_USDJPY_H1` (donchianUpperCrossUp, 96 cores): 10,000 in `Results` 60 s after start, 114,489 generated in 145 s, 2.9 M generated/h. Donor filters applied afterwards to its IS metrics keep 71 of 5026.
- `Test_Calib_XAUUSD_H1`: watchdog stop at 7,056 after 35 s; 7,085 on disk. OOS retest of 7,084: 83 s.
- Free shell (`freeShellLong`, both holes free, 842 blocks on): 2 % accepted in the first minute, 34 % after five; 5,059 in 5 min (18,367 generated).
- `StopCondition type="passed-count" passedStrategies="8000"`: the build ended near 5,026 instead — 🤔 not understood, not relied on.
- 2026-10-01 19:05: custodian killed mid-stop → `OOS` 0 files, `Results/Strategy 19.18.60.sqx` 8,197 bytes "not a zip file".
- One start, 6-min `time-limit`, free shell, 96 cores (`AlgoData/scratch/calib_queue/queue.sh` v2): XAUUSD H1 genetic 6,986 accepted of 23,482 (acceptance 2 % in minute 1, 35 % in minute 6), OOS retest of them 105 s, stop 55 s, 576 s from one population leaving SQX to the next; random generation 1,059 (long) and 393 (short) of ~23,000 on USDJPY H1, 450 s. Two starts with the export at each stop were 20-40 min.
- Other projects' databanks are not rewritten by a start or a stop of the install (mtimes unchanged over two later stops of the install): project n is exported while the custodian builds n+1.
- Block keys per strategy: `signal/Item[AND]/Block/Item` of `strategy_Portfolio.xml`; dumped to `harvest/<P>/Results/<day>/blocks.parquet` by `AlgoData/scratch/calib_queue/blockdump.py`.

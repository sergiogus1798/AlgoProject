---
q: How do SQX compute, flush to disk and the pilot scale with variant batch size at step 16.5?
kw: variants batch size timing, synchronizeDatabank MB/s, flush slow, pilot RetestOnAdditionalMarkets false, no-markets pilot, live.start live.stop cost, 500 variants 215 s, 5000 variants 1394 s, extra markets cross-check cost
tag: 🔬  date: 2026-10-05  see: databanks/variants-one-big-load-loses-is-results, perf/workflow-step-durations, sqx-drive/live-chain-without-restart
---
# Step 16.5: bigger loads compute cheaper per variant, the flush costs ~9 MB/s, and the pilot's time is the 11 extra markets
Rules: flush the three leg databanks at once (17 MB/s, `sqx.projects.live.sync`); the restart route's sync wait scales
with the batch (`sqx.variants.execute.synced`); the pilot runs with `--no-markets` (it reads only main-market trade counts).
Cost per mother varies, so the compute figures are points, not one curve.

## Evidence
🔬 Custodian `SQX_w2` (80 GB, all cores), `Test_NIKKEI225_M30_simpleL_val`, three WFC legs, 11 extra markets at 1-min, 2026-10-05.
| batch (three legs, `Task finished in`) | seconds |
|---|---|
| 300 (pilot) | 152 |
| 500 (avg of 10 sessions, `..._simpleL_auto`) | 215 |
| 1,500 (3 mothers, live GUI) | 604 |
| 2,500 (5 mothers) | 987 (IS 514, OOS1 295, OOS2 178) |
| 5,000 (10 mothers) | 1,394 (IS 613, OOS1 492, OOS2 289; IS incomplete) |
Ten separate 500-batches ≈ 2,150 s against 1,394 s as one.
- Flush, one databank after another ≈ 9 MB/s: 5,000 run WFC_Build 3,952 files 1.4 GB 166 s, OOS1 1.1 GB 119 s, OOS2 645 MB 71 s;
  2,500 run 103 / 59 / 35 s. All three at once (3 threads, HTTP `/project/synchronizeDatabank`, live): 1,091 MB in 63.9 s = 17 MB/s.
  The old fixed wait (150 polls × 2 s) was too short for 5,000 IS (commits 51c13c3, 12cfb6a).
- Pilot, 300 variants, IS leg, live: with 11 markets 81.4 s run + 12.3 s sync (111 MB); with `RetestOnAdditionalMarkets use="false"`
  via `updateTaskXML` 4.3 s + 1.6 s (13 MB). Main-market trade counts identical 300/300. Autopilot wiring: commit 77ec141.
- Live GUI fixed costs: `live.start` 75.9 s (~1,300 strategies in project); `live.stop(export=False)` 196 s (syncs every databank);
  `livexec.load` 300 files 1-3 s, 1,500 files 4.7 s; `livexec.clear` 4.7 s.

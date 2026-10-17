---
q: How much time does the autopilot lose per SQX step starting and exporting?
kw: autopilot run time breakdown, dead time between SQX steps, how long does the autopilot take, worker restart cost per step, export after stop cost, step 8 python cost, profitShape entryQuality slow, build never stops databank-full minutes ignored
tag: 🔬  date: 2026-10-13  see: sqx-format/optimization-profile-byte-order, perf/workflow-step-durations, sqx-drive/live-chain-without-restart, sqx-drive/export-after-every-stop
---
# Per SQX step the autopilot spends ~27 s starting and 90-230 s exporting; on a dev run that is ~30 % of 6 → 16
First real run, XAUUSD M30, 571 built → 5 kept at step 8 (dev draw). Per SQX action: prep+JVM start
26-29 s; stop+afterrun export 89-227 s (each databank ~15 s: a conductor JVM per export, sequential;
`Results` re-exported at every stop). Python is cheap except step 8 (297 s), and 200 s of that are
`profitShape` + `entryQuality` running per strategy on all 571 BEFORE the cut to 5. The build stops at its
time limit: 📓 1,800 s exactly in 5/5 runs of 2026-10-10/11 (`fases.csv`, `AlgoData/autopilot/<P>/<stamp>/`); Not: «stops only at `databank-full` 10,000, `minutes=` ignored» (2026-10-05, one run).
Fixed after this run: XML-wide fingerprint (no `Results` re-export), no MCR trades, `buildcap`. At 10,000 strategies the fingerprint cost 13-17 min per step: fixed 2026-10-04 (per-file cache, pool).
10 survivors, 2026-10-05: 6 → 25 = 230 min, SQX 56 %; `tiempos.md` in the run folder says where.

## Evidence
- 🔬 10,000 built, cut at step 12 (six runs, 2026-10-08): 75-105 min; SQX build+OOS ~31 min, step 8 python 29-42 min of which `falsePositives` 1,719-2,520 s. `feedQuality` serial was 42 min, gone once on `core.fanout`. Final stop of a resumed session: 469-491 s against 17-41 s.
Timestamped autopilot log, custodian, 2026-10-01 10:23-11:14 (`AlgoData/autopilot/Test_XAUUSD_
timeRangeBreakout2_M30/20261001-103130/resumen.md`):

| step | prep+start | SQX | stop+export | total |
|---|---|---|---|---|
| 7 OOS (571) | 27 s | 35 s | 106 s | 168 s |
| 9 crossmarket (5 × XAGUSD) | 27 s | 30 s | 89 s | 146 s |
| 11 crossTF (+10.5 fill) | 26 s | 41 s | 135 s | 202 s |
| 13 MC Retest (7 tasks × 5) | 27 s | 1,376 s | 227 s | 1,630 s |
| 15 SPP IS+OOS (5) | 29 s | 347 s | 205 s | 581 s |

Sum: SQX 1,829 s · start 136 s · stop+export 762 s · Python 319 s (step 8 297, the rest 3-8 s each) ·
judges ~2 s. MCR 7 OHLC 386 s, MCR 6 Exits 125 s, MCR 3 Slippage 116 s, MCR 5 Params 19 s.
Step 8: gate 7 s, edgeCost 4, feedQuality 39, spread 35, decay 4, monkey 5, profitShape 96,
entryQuality 104. Build 10:09:42 → stopped by hand 10:21:33 at 571 (status «Accepted 0.24 %» at 54 s).
- 🔬 2026-10-01, live chain (`autopilot --live`, one GUI session), XAUUSD H1 donchianUpperCrossUp,
  128 built → 5: OOS 11 s · 9 crossmarket 20 s · 11 crossTF 271 s (still a restart) · 13 MCR
  1,565 s · 15 SPP 587 s; session open 28-38 s once, close+export 46-92 s once. Dead time between
  SQX steps ≈ 0 (was 27 s + 90-230 s per step). 16.5 variants (sqcli, per mother: make+pilot
  146-214 s, execute 173-281 s) 2,090 s for 5 mothers; 17+18+18.5 77 s; 19 WFM 1,072 s.
  Wall clock steps 4 → 19: 128.7 min, ~16 of them lost to the build's ignored stop and two
  relaunches.
- 🔬 2026-10-04, NIKKEI225 M30, `Results` and `OOS` at 10,000 strategies each, restart route: steps 9, 11
  and 13 took 13-17 min for seconds of SQX work, and the stop after the build 17 min. SQX resaves every
  `.sqx` on each stop and sync, so `sqx/databank/state.fingerprint` (canonical parse, ~19 ms a file)
  re-read all 10,000 each time: 3.2 min, called several times per step by `afterrun` and the rail. Now a
  per-file cache keyed by (path, mtime, size) and a fork pool for the files not seen: 4.7 s cold, 0.12 s
  warm, same digest (`tests/test_ui_loader.py`). With that and `--live`, step 15's overhead was ~1 min.
  What is left is SQX's own work on 10 survivors: variants 69 min, WFM 28 min, SPP IS+OOS 26 min.
- 🔬 2026-10-05, `Test_NIKKEI225_M30_simpleL_ref`, restart route, 10 survivors, custodian
  (`docs/AgentPDFs/WORKFLOW_TIMING_BASELINE.md`): step 16.5 = 20 sessions: `make`'s 300-variant pilot and
  `execute`'s run, per mother. Per session: boot ≈12 s, sync-from-files + clears + fixed sleeps 34-43 s,
  stop + sync-to-files 53-80 s, and a 63 s post-stop export of databanks that had not changed.
  - Fixed, 230c856: the export fingerprint called both SPP databanks stale at every stop because SQX
    re-saves `optimizationProfile.bin` in another byte order (`sqx-format/optimization-profile-byte-order`).
    🤔 In the validation run the SPP databanks were still re-exported at the stop of step 19 (WFM); cause
    open. Confirm with two consecutive stops with no SQX work between and `sqx/databank/state.py`
    `_entries` diffed.
  - Fixed, caccb79: `sqx.variants.execute` and `.pilot` stopped the worker with the post-stop export on though
    they write only the WFC databanks `afterrun.skipped()` ignores; now `worker.stop(role, export=False)`.
  - Polls shortened: variants 5 s → 2 s (`sqx/variants/config.yaml`, ready_tries 100, sync_tries 150,
    c5a2cc3); launcher `ready`/`watch` 10 s → 3 s (`ui/daemon/advance/run.py`, READY_TRIES 200, e33540b).
  - 📓 Side effect of the 3 s poll: a 1,000-strategy build with a 20-minute cap was stopped by `buildcap` at
    ≈1,204 s and the OOS retest did not chain (the autopilot ran it in a start of its own, as designed); with
    the 10 s poll the same build finished by itself at 1,218 s with the OOS chained.
  - Not done: one SQX session per mother (or for all) in 16.5 (≈100 s per mother); exports in parallel with
    the next start; live chain as default route (needs a same-project count comparison first); the fixed
    4×2 s + 8 s sleeps in `execute.load`.

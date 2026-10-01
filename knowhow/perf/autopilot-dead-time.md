---
q: autopilot run time breakdown, dead time between SQX steps, how long does the autopilot take, worker restart cost per step, export after stop cost, step 8 python cost, profitShape entryQuality slow, build never stops databank-full minutes ignored
tag: 🔬  date: 2026-10-01  see: perf/workflow-step-durations, sqx-drive/live-chain-without-restart, sqx-drive/export-after-every-stop
---
# Per SQX step the autopilot spends ~27 s starting and 90-230 s exporting; on a dev run that is ~30 % of 6 → 16
First real run, XAUUSD M30, 571 built → 5 kept at step 8 (dev draw). Per SQX action: prep+JVM start
26-29 s; stop+afterrun export 89-227 s (each databank ~15 s: a conductor JVM per export, sequential;
`Results` re-exported at every stop). Python is cheap except step 8 (297 s), and 200 s of that are
`profitShape` + `entryQuality` running per strategy on all 571 BEFORE the cut to 5. The build itself
stops only at `databank-full` 10,000: `minutes=` is ignored under that type (~48 accepted/min here).
Fixed after this run: XML-wide fingerprint (no `Results` re-export), no MCR trades, `buildcap`.

## Evidence
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

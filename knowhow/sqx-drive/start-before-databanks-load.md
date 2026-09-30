---
q: No strategies to retest; task started with empty input; Syncing databank(s) from files; first -project command loads databanks; action=start too early; WFM finished in seconds; watcher lost Starting project line; Error while running project; NullPointerException ProjectGlobalLog addAcceptedStats; run waits forever
tag: 🔬  date: 2026-09-29  see: sqx-drive/project-log-written-in-pieces, sqx-drive/export-after-every-stop
---
# A task started while SQX is still loading its databanks retests nothing
The first `-project` command after a worker starts makes SQX load every databank from its files
(«Syncing databank(s) from files» … «Synchronization finished», ~50 s for 12 banks). A status
poll from another caller (the window's pulse) can be that first command; a second status is then
answered at once, and `action=start` sent on it runs the task on an empty input: «No strategies
to retest», task done in seconds. `advance.run.ready` waits for the log's last sync to finish.
Also: a WFM writes a progress line per cell and step, so a watcher that bounds its lines must
keep the «Starting project» line (`progress.trim`) or it reads «did not start» and stops the run.

## Evidence
2026-09-29, «▶ SQX» of step 19 on Test_USDJPY_donchianUpperCrossUp_M30 (custodian):
11:52:29 sync started by the pulse's status (qtp-60), 11:52:35 `action=start`, 11:52:35 «WFM : No
strategies to retest», 11:52:47 «Loaded 21 strategies to databank SPP OOS», 11:53:21 sync done.
The 11:24 run, whose own status triggered the sync, started after it and retested. Earlier, at
11:44, the same run was stopped 20 min in: `sqxlog.grow` kept the last 20,000 lines and lost
the start. Fixed in `advance/run.ready`, `progress.trim`, `advance/sqxlog.grow`.
2026-09-29 15:40: «WFC 1 IS» (500 variants) finished, then SQX logged «Error while running
project» (NullPointerException in ProjectGlobalLog.addAcceptedStats, two statuses in flight) and
never wrote «Project finished»; `variants.execute.run` polled 53 min. Now `banks.aborted` stops
it, `run_state` counts the line as an end with `events["error"]`, and the daemon caches status 15 s.


---
q: run the workflow without restarting SQX; startOnlyTask runs the wrong task; startFromTask Task 'Build strategies' does not exist; cut a databank with the worker up; step project loadconfig; time between tasks; build to OOS gap; copy databank between projects; remove deletes folder; ServletProject.jar GUI endpoints; GUI mode headless Xvfb; browserToken; runThisTaskOnly projectXML; updateTaskXML live edit; removeReports delete by name; loadGridData metrics; CLI not ready; exitapp; databank names with spaces over HTTP
tag: 🔬  date: 2026-10-01  see: databanks/databank-verbs, databanks/curating-a-databank, perf/autopilot-dead-time, databanks/no-spaces-in-names
---
# In GUI mode (`sqx-worker.sh --gui`) one SQX session runs any task, edits any task and cuts any databank live; sqcli cannot pick a task
sqcli's `startOnlyTask task=N` runs the first task named like N's TYPE (any retest → `OOS`). GUI mode
serves `/project/*` on `WebServerPortUsed` to a POST with header `browserToken: <BrowserToken>` (both
in `settings.xml`); `start action=runThisTaskOnly taskName=<cfx name>` **plus `projectXML=<getConfig>`**
runs only that task (without `projectXML`: nothing). `/call` says «CLI not ready» all session long.

## Evidence
- 🔬 2026-10-01, custodian GUI mode, `Test_XAUUSD_GuiChain_M30` (Build, OOS, MC Trades all `active`):
  Build alone 63 s, no other task ran; OOS alone 2.3 s; MC Trades alone 1.7 s. Start 28 s, stop 30 s
  (`exitapp` → shutdown sync), all processes gone, databanks on disk = memory (Results 30, OOS 15, MC 15).
- `updateTaskXML projectName= taskXMLFile=Retest-Task1.xml xmlConfig=<xml>` (21 ms): changed the task in
  memory AND SQX rewrote `project.cfx` itself — the live way around hard rule 4. Rerun obeyed it.
- `removeReports projectName= databankName=OOS strategies=<name,name,…>` (170-190 ms): names with spaces
  work, so does `databankName=MC Trades`. It drops from memory only; the files stay until a sync.
  `synchronizeDatabank` (3 ms + ~1 s async) then leaves disk == memory exactly (30→20, 20→15).
- `listStrategies` 6 ms (names). `loadGridData … first1000=false lastChangeTime=0 refreshAction=false`
  6-8 ms: one row per strategy in the databank VIEW's column order, no headers. `databankList` 5 ms.
  `status` → «Not implemented.»: detect the end by «Project finished» in SQX's log (grep, timestamp).
- Next task read the cut: MC Trades (input OOS) tested 15 = the survivors.
- Auth (javap `SQWebGUILib.jar` `HttpJSONServlet.doGet`): a matching `browserToken` header skips the
  remote-access check; token = `new Date().toString().hashCode()` at start. No header → 401
  «Remote access disabled». Jetty binds `0.0.0.0`; port is the first free in 8080-8090 unless
  `WebServerPort` is set (custodian took 8080 with the master in CLI mode).
- ⚠️ A fresh GUI session answers `databankList` with EVERY databank at 0 records and loads them
  from disk 1-10 s later (Results 0 → 128). A sync in that gap mirrors empty memory over the files
  (hard rule 1); `live.start` returns only once memory == disk for every Test_/Trade_ project.
- `/project/stop` on a running BUILD answers «Project execution stopped.» and does NOT stop it:
  sent twice over 5 min (H1, 95 cores), Results kept growing 105 → 128, no end line in the log.
  Only closing the session (`exitapp`, ~45 s, databanks saved) ended it. So the build's minute
  cap (`buildcap`, SQX ignores `minutes=` under `databank-full`) has no live equivalent yet.
- 16.5 live (`sqx.variants.livexec`): 500 variants × 3 WFC legs — `loadFilesToDatabank folder=
  clear=true all=true` then `start` with the legs' projectXML — 151 s against 281 s by sqcli with a
  restart; emptying the four databanks 2.5 s (`removeReports` by name + sync), 500/500/500 on disk.
- Build stop types (`SQTradingLib` `StopConditionTypes`): never, databank-full, passed-count,
  time-limit. 🔬 `databank-full` with 300 / 10 min ran 49 min (606 accepted, Results held at 300);
  `time-limit` 2 min stopped itself at 123 s (`restartCount` 5 changes nothing). The type comes
  from `databank.stop_condition` in assets/_build.yaml, now `time-limit`.
- «Last generation» is held on «Auto-sync never» in memory whatever config.xml says: it never
  reaches disk, so `live.sync` skips any databank whose live `syncType` is that.
- GUI mode uses `StrategyQuantX.config`, not `sqcli.config`: the custodian's was 8g, set to 80g
  (owner, 2026-10-01) — keep the two equal.
- sqcli route, same day: cut = `synctofiles` → copy survivors → `clear` (deletes files) → `load folder=`
  (async, «Strategies loaded») → `export`; `-databank action=delete strategies=` is a no-op over HTTP;
  `syncfromfiles` adds (`X(1)`); `-project action=remove` deletes the folder; a step project by
  `loadconfig` + `-databank action=copy` into a databank declared in config.xml worked, ≈ 0.8 s.

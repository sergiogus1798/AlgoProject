---
q: run the workflow without restarting SQX; startOnlyTask runs the wrong task; startFromTask Task 'Build strategies' does not exist; cut a databank with the worker up; step project loadconfig; time between tasks; build to OOS gap; copy databank between projects; remove deletes folder; ServletProject.jar GUI endpoints; runFrom runTask by task index; onUpdateTaskXML live edit; setDatabankSynchronization syncType; GUI web server port 8082 reachable headless
tag: 🔬🤔  date: 2026-10-01  see: databanks/databank-verbs, databanks/curating-a-databank, perf/workflow-step-durations, databanks/no-spaces-in-names
---
# One SQX session can run every step and every cut: step projects by `loadconfig`, cut by `clear`+`load`; `startOnlyTask` cannot pick a task
`startOnlyTask`/`startFromTask task=N` turn N into the task TYPE's generic name ("Retest strategies",
"Build strategies") and run the first task carrying that exact `name` — in a donor-built project any
retest index runs `OOS`, and the build is unreachable (silent no-op / «Task … does not exist»). What
works live, 🔬 on `Test_USDJPY_LiveChain_H1`: `action=start` chains active tasks natively (build→OOS
0.19 s apart); the cut is files-free; a step's task runs in a step project made with `loadconfig`
(0.39 s), fed by `load folder=`, its output copied back with `-databank action=copy` into a databank
**declared in the main config.xml** (one made by `action=create` is never saved). Transition ≈ 0.8 s.

## Evidence
- 2026-10-01, custodian, 60 strategies USDJPY H1. `startOnlyTask task=3|4|5|14` → log «OOS : Starting
  strategies retesting»; `startFromTask task=1` → `Task 'Build strategies' does not exist` (cfx name is
  `Build strategies 2`). The GUI servlet (`ServletProject.jar`, `/project/start`, `action=runThisTaskOnly`,
  `taskName=` real name) would do it, but sqcli serves only `/call` on 5070 — GUI mode (port 8082) untested.
- Cut, worker up: `synctofiles` OOS 0.42 s → copy survivors to a folder → `clear` (deletes the files on
  disk at once: «removed 56») → `load folder=` (async; wait for «Strategies loaded», 0.14 s) → `export`
  = exactly the 56 survivors. Persisted on stop (disk 56 = keep list) and across a restart.
- `-databank action=delete strategies=` still a no-op over HTTP (5 encodings tried, «Reports removed.»).
- `syncfromfiles` ADDS disk files to memory (60 + 56 → 116, collisions renamed `X(1)`); `count` on an
  already-loaded project does not resync.
- `-project action=remove` deletes the project's FOLDER from disk, databanks included.
- Exports from memory: 8–18 ms per databank. Retest in the step project read «Data loaded from memory».
- `copy` into main `Markets` (made by `create`): 56 in memory, 0 on disk after stop. Into declared
  `CrossTF`: 56 and 56. Other projects on the install unchanged (snapshot compare).

## 🤔 The GUI's own JSON servlet (not sqcli) can already do everything `startOnlyTask` cannot — read from the jar, not run
`javap -c -p -constants` on `internal/plugins/ServletProject/ServletProject.jar`
(`com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet`, 2026-10-01) — this is the Electron
window's own backend endpoint, `/project/*` on the GUI's web port (`WebServerPortUsed`, 8082 on the
custodian's `user/settings/settings.xml`), separate from sqcli's `/call`. It is **not sqcli** — sqcli
never binds this port — so every finding below is from the bytecode only, nothing was called over HTTP
(GUI mode was never launched; that is pista 3 of the 2026-10-01 encargo, still a design, not a test):
- `onStart`: `action=runFrom|runTask` takes a **1-based task INDEX** (`Integer.valueOf`, bounds-checked
  against `getTasksCount()`), resolves it with `project.getTask(index-1).getName()` and calls
  `SQProject.setRunSpecification(50 or 100, thatRealName)` — the exact step sqcli's CLI parser is
  missing (bisected in `sqx-drive/cannot-start-unresolved-past-data.md`'s probe-and-remove pattern,
  not through this). `action=runThisTaskOnly|runProjectFromHere` take `taskName=` directly, same call.
- `onUpdateTaskXML`/`onUpdateProjectXML` (both `synchronized`): rewrite one task's or the whole project's
  `<Settings>` through `SQProject.updateConfig`/`ISQTask.setConfig`, then
  `SQFileManager.updateTaskConfig`/`updateWholeProjectConfig` — a live edit of which tasks are active or
  what a task runs, served from the SAME in-process `ProjectEngine.get(name)` object sqcli's `-project`
  verbs use, with no restart implied by the bytecode.
- `onSetDatabankSynchronization`: one call, `Databank.setSyncType(syncType)` — the live knob pista 5
  asked whether it exists; it does, as a plain servlet param.
- Every param here is a normal form field (`tryGetParam` off a `Map<String,String[]>`), posted
  gzipped+urlencoded by the Electron window (`BackendService.getPromise`, `internal/web/app/sq-tools/
  sqbackend/services/BackendService.js`) — not sqcli's single command string split on whitespace
  (hard rule 6's bug). A databank name with a space would very likely survive this route; untested.
- Auth: the window calls `/main/login` with a password only when "remote access" is turned on
  (`internal/web/app/login/LoginService.js`); the master answered «Remote access disabled» at
  `/main/getWebSocketPort` with its GUI up (card predates this reading). Whether a local, headless
  Electron+JVM session demands that login before serving `/project/*` is unconfirmed — the next
  concrete step, not yet taken.
- Not reachable today: sqcli is a separate process that never opens 8082. Using this means running the
  custodian in **GUI mode headless under Xvfb** instead of sqcli — a change to how `bin/sqx-worker.sh`
  launches the custodian, which hard rule 3 reserves for the owner to approve (see the chain design in
  `perf/autopilot-dead-time.md`'s sibling report, 2026-10-01).

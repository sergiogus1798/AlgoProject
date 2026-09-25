---
q: SQX GUI is Electron + Jetty web app; live progress websocket getWebSocketPort; Remote access disabled; ProgressEngine log progress; tail log for progress percent; control SQX from outside
tag: 🔬  date: 2026-09-20  see: sqx-drive/which-endpoint, eng/log-retention
---
# SQX's GUI is HTTP+WebSocket on localhost; for progress, tail the `ProgressEngine` log
No native toolkit: Electron shell over a Jetty web app, every module a folder of HTML/JS.
Live progress websocket is gated here (`Remote access disabled`). Without changing settings, tail
`user/log/StrategyQuant/log_<date>.log`: `ProgressEngine` lines give task boundaries, thread names give %.
The log is huge (55 MB by 20:44 one day) — tail it, never read it whole.

## Evidence
Modules: `internal/electron/` shell; `internal/web/BUILDER RETESTER TASKMANAGER RESULTS RESULTS2
OPTIMIZER PORTFOLIOMASTER PORTFOLIOCOMPOSER AlgoWizard SQWIZARD SQMANAGER QDM MTANALYZER NEURALNETWORK …`.
📓 Startup log: `com.strategyquant.webguilib.Electron`, `…BrowserGUI`, `…servlet.MainServlet`,
`org.eclipse.jetty.server.Server` (jetty-all-uber 11.0.20).

Websocket (`internal/web/common/Batch1/libs.js`): `GET /main/getWebSocketPort` → `{"port": N}` →
`ws://localhost:N/websocket/updates`. Fields: `progressChannel`, `progressUpdateEvent`,
`progressPercent`, `progressAction`, `progressText`.
⚠️ `GET http://localhost:8080/main/getWebSocketPort` → `{"disabled":true,"error":"Remote access disabled"}`
with master GUI up. 🤔 Untested whether enabling remote access exposes all of `/main/*` or only the port lookup.

📓 Log vocabulary (logger `c.s.t.project.ProgressEngine`):
```
<TASK> : Starting strategies retesting...
<TASK> : Loading backtest data for Main test - <SYMBOL> / <TF>
<TASK> : All backtest data prepared
<TASK> : Sequential optimization: <STRATEGY> - Optimizing parameter <NAME>...
<TASK> : Task finished in N.N s.
Project finished
Databank '<PROJ>/<BANK>' loaded - N strategies in Nms
Databank '<PROJ>/<BANK>' saved - files before sync N / after sync N / saved N / removed N in N s.
```
🔬 Finer progress is in the thread name: `[Blocking computeThread common #45 - WF: 6 runs : 20 % OOS WFO 4]`.

| want | route | master GUI up |
|---|---|---|
| start chain | `-project action=start\|startOnlyTask\|startFromTask` | worker only |
| stop/pause/resume | `-project action=stop\|pause\|resume` | worker only; MCP `stop_project` on master |
| coarse state | `-project action=status` | worker only |
| live % | `/websocket/updates` | needs remote access |
| live %, no settings change | tail `ProgressEngine` + thread names | ✅ always |
| count results landing | `-databank action=count` on a timer | worker only |

# Driving SQX from code

## Which endpoint, when

| | port | works while GUI up? | notes |
|---|---|---|---|
| master command API | 5050 | ❌ `Error: CLI not ready.` | needs the GUI closed |
| master MCP / web | 8080 | ✅ | `/call` **404s** — this is not the command API. MCP is read-only plus run/stop |
| **worker command API** | **5060** | ✅ **always** | headless, no GUI to conflict. **Use this.** |

🔬 All four verified 2026-09-02.

## The `-project` verb (from `sqcli -help`)

```
action: [list, start, startOnlyTask, startFromTask, stop, pause, resume,
         remove, status, loadconfig, saveconfig]
name:   Project name      file: Path of the config file      task: Task number, 1-indexed
```

🔬 **Projects CAN be created and modified programmatically.** Verified end to end; full cycle in
`docs/project-config-workflow.md`. The four traps:

1. **`loadconfig` never overwrites.** Into an existing name it creates `MyProject(2)` and leaves the
   original alone. The response says `Project loaded 'MyProject(2)'` — **read it**, or you will verify
   the wrong project and conclude your edit failed. To replace: `action=remove` first.
2. **`saveconfig` output cannot be fed to `loadconfig`.** The verbs are asymmetric. For a loadable
   template, copy an existing `user/projects/<name>/project.cfx` (the multi-file form).
3. **URL-encode only space→`%20`, `?`, `&`, `#`.** The server reads the query literally.
   `name=MyProject(2)` works; `%28%29` fails with `Project 'MyProject%282%29' does not exist.`
4. **A GUI-loaded project still cannot be edited on disk.** The API works because SQX itself performs
   the write.

Other verbs: `-databank action=list|export|syncfromfiles|clear|count|create|load`,
`-tools action=orderstocsv`, `-data action=export`, `-symbol action=list`.
🔬 `internal/web/SQUANT/help.txt` holds the **full `sqcli` verb reference**, readable without starting
SQX. Consult it instead of guessing at arguments.

## What the MCP server can and cannot do

🔬 The `sqx` MCP server is bound to the **master** GUI and works while the GUI is up, but it is
**read-only plus run/stop**: `list_projects`, `list_databanks`, `list_strategies`,
`get_strategy_stats`, `run_project`, `stop_project`. **There is no import/loadconfig/config-write verb.**

So to get a project into the *running* master there is exactly one route: **the GUI's own
Project → Load config**. The CLI `loadconfig` needs the GUI closed; MCP cannot do it at all.

🔬 **A project the GUI fails to load is silently omitted from the project list, with no error.** The
master returned 14 projects while `user/projects/` held 15 directories — the missing one was
`Infinox_SP500ft_H4_HighPrecision` (`OPEN.md` issue 3). **Diff the live list against the directory
listing** rather than assuming the list is complete.

🔬 **The cause of that class of failure is a `config.xml` that references task XML members the
archive does not contain** (found 2026-09-03). That project declares 8 tasks and ships only 3 task
files. `sqx/inspect/project_health.py` scans every project for it in one pass; it is the only
broken one on this install.

🔬 **Repair it by grafting, not by swapping in the backup** (2026-09-04). Diffing the two archives
member by member: `project_backup.cfx` is from 2025-10-13 and its `config.xml` still carries the old
name `Infinox - SP500ft - H4 (High Precision)` **with spaces** — which breaks the HTTP API, hard rule
6 — plus an `OOS` databank registration that was since removed and a `Retest-Task2.xml` whose input
databank is the stale `Complete Data Uncorrelated` instead of `Results`. Restoring the whole archive
undoes all three. `sqx/repair/graft_tasks.py` keeps every live member and copies in only the five
absent ones, then verifies that nothing is still missing and that every databank the grafted tasks
name is registered.

## Re-testing an arbitrary parameter set: the variant route

There is **no CLI verb that sets a strategy's parameters** (`help.txt`, full verb list). The only
way to score a chosen tuple is to write it into a `.sqx` and retest that file.

- 🔬 **Parameter values live in exactly one place**: `strategy_Portfolio.xml`,
  `<variable><id>NAME</id>...<value>N</value></variable>`. The rule slots reference the variable by
  name (`<Param key="#Period#" ...>DICrossPeriod1</Param>`), so rewriting `<value>` rewrites the
  rule. `settings.xml` does **not** carry the parameter names -- grepped, 0 hits for all of them.
- 🔬 The databank's display name is `settings.xml`: `<ResultsGroup ResultName="...">` plus
  `<StrategyName type="String">`. Rename both per variant or every variant lands under one name.
- 🔬 Writing variants is mechanical and was verified end to end on `Strategy 17.9.39`: 8
  substitutions, repack, read back -- values correct. **Strip the inherited members or the disk cost
  is absurd**: all 8 members = 5,215 KB each (57 GB for 11,597 variants), without
  `optimizationProfile.bin` = 100 KB, and keeping only `META-INF` + `settings.xml` +
  `strategy_Portfolio.xml` + `lastSettings.xml` + `version.txt` = **15 KB** (160 MB for 11,597).
  🤔 Whether SQX loads that 5-member form, and whether the databank de-duplicates on the inherited
  `<Fingerprint>`, is **untested** -- both are cheap to settle on 3 files before generating 11,597.
- 🔬 **One retest gives both samples.** A Retest task whose `Setup` spans 2008-2022 and whose
  `<OutOfSample showGraph="false"><Range dateFrom="2018.01.01" dateTo="2022.12.31"/></OutOfSample>`
  is set stores sample 10 and sample 20 in the same `.sqx` -- that is how `XAUUSD` task 1 fills the
  `OOS` databank, and a paired `.vw` then exports IS and OOS on one row (`04-export.md`). So a WFC
  needs one run, not two.

📓 **Throughput, measured off the master's log on 2026-09-19** (`totalCores: 95`):

| job | work | wall clock |
|---|---|---|
| `SPP IS` task | 5 strategies x ~12,400 permutations over 10 years = ~62,000 backtests | **369 s** |
| `SPP OOS` task | the same over 5 years | **187 s** |
| `MC Trades` task | **757 whole `.sqx` retested** over 2008-2026, loaded from a databank | **31 s** |

The last row is the honest analogue for the variant route -- ~24 strategies/s including load and
result-writing, so **11,597 variants land around 8 minutes**. Compute is not the constraint.

## Projects built on the worker are invisible on the master

🔬 The two installs are fully independent. A project created on the worker will **never** appear in the
master GUI. Moving one across means importing its `.cfx` through the master GUI, or copying the
directory with SQX closed. Say this out loud when handing over a worker-built project — "nothing on
your master was touched" also means "you will not be able to see it".

## Reading vs writing — the actual boundary

Not "which agent has permission". The boundary is **whether a running instance holds the project**:

- Read a `project.cfx` — always safe, any session, any time.
- Create/modify via the API on the **worker** — always safe.
- Edit a `project.cfx` on disk under a running instance — **silently lost**.
- Anything on the master — needs the GUI closed, i.e. the SQX-lifecycle lane.

## Authoring with the `sqx-strategy-project` skill

🔬 The skill works, but two things need handling:

- **It carries the donor's entire task chain.** Cloning XAUUSD's build task ×5 produced an **18-task**
  project: the 5 new build tasks plus all 13 donor retest/MC/SPP/WFM/Clear/GoTo tasks, including a
  **dangling `GoToTask`** pointing at a task name that no longer existed. For a builder-only project,
  strip it: `python3 -m sqx.inspect.keep_tasks in.cfx out.cfx --types Build`. That also drops
  databank registrations nothing references, while keeping the 5 system ones.
- 🔬 **`<StrategyType type="simple">` wins over an attached `templateFile`: the template is not
  applied.** Confirmed against real built strategies 2026-09-04, no longer an inference.

  Method, in `sqx/inspect/template_check.py`: take the blocks a template *fixes* — every `Item`
  under its `Rules` whose `categoryType` is `indicator`, `simpleRules`, `priceValue` or `priceRange`,
  **skipping the subtree of any `categoryType="randomBlock"`**, because those are the holes the
  builder fills and say nothing about the template. Then open strategies the project actually wrote
  and check the signature is present.

  Result over 8 projects and 33 databanks, sampling 25 per databank, seed 0:
  **0 of 642 strategies from built databanks carry their project's template block.** XAUUSD names
  `DoubleVortexLong_Template.sqx`, whose only fixed block is `Vortex`, and not one of its 10,231
  strategies contains a Vortex; each uses a different random indicator instead. Same for
  `ROCAboveLevel` (AUDJPY, EURUSD, USDJPY), `AroonCrossesAbove` (GBPJPY_H1), `CCI` (USDCHF),
  `HurstExponent` (SP500_H1) and `BBWidthRatio` (EURJPY_H1).

  Positive control: the detector *does* fire. Of 53 strategies sampled from `Existing portfolio`
  databanks, **2 carry the block** — one in SP500_H1 with `HurstExponent`, one in EURJPY_H1. Those
  databanks hold strategies built elsewhere and imported, so they are neither evidence for the
  template nor against it; they only prove the check is not blind.

  ⚠️ Two of the nine cannot be settled this way. **CADJPY_H1**'s `AcceleratorEMALong_Template.sqx` is
  made of nothing but `RandomCondition` blocks, so it fixes no block to look for — a template that
  constrains only which random groups are sampled. **XAUUSD_Breakout_H1**, the one project declaring
  `type="template"`, has no strategies on disk, so it gives no positive control from a real build.

  📓 Counted 2026-09-04 with `grep -l "'type': 'simple'"` over the per-project pipeline docs, before
  those maps were retired (`OPEN.md`); no longer reproducible from a live command. It returned **10**
  files, not 9. The tenth is `Builder`, whose `templateFile` is the stock relative
  `SQ3StrategyTemplateExample.sq4`, which does not exist on this install — so 10 hits, 9 with a real
  template file.

  Tracked as `OPEN.md` issue 9. Flipping the nine to `type="template"` would change what those
  projects generate — that is the owner's call, not a bug to fix (hard rule 3). **Owner's decision,
  2026-09-04: leave all nine as they are.** The finding stands only as a fact about what these
  populations are: generic strategies, whatever their `templateFile` implies.
- `templateFile` paths are **absolute** (build 144 has no relative form) and resolve against the
  **target** install. Copy templates into `<install>/user/settings/StrategyTemplates/<set>/` first.
- 🔬 `uSymbol` is the field SQX actually binds against, not `symbol`. The engine blanks it and SQX heals
  it on load — verified: it filled in `XAUUSD` for all 5 tasks.

## The GUI is a web app — the surface a wrapper application would use

🔬 Found 2026-09-20 while scoping whether a third-party front end could drive SQX with a live
progress bar. **StrategyQuant X has no native desktop toolkit.** Its GUI is an Electron shell over a
Jetty-served web application, and every module is a folder of HTML/JS on disk:

```
internal/electron/                     the shell
internal/web/BUILDER  RETESTER  TASKMANAGER  RESULTS  RESULTS2
             OPTIMIZER  PORTFOLIOMASTER  PORTFOLIOCOMPOSER  AlgoWizard
             SQWIZARD  SQMANAGER  QDM  MTANALYZER  NEURALNETWORK  ...
```

📓 Confirmed in the master's own log: `com.strategyquant.webguilib.Electron`,
`c.strategyquant.webguilib.BrowserGUI`, `c.s.webguilib.servlet.MainServlet` and
`org.eclipse.jetty.server.Server` (jetty-all-uber 11.0.20) all log on startup.

**Consequence.** The choice is not "drive the CLI or automate a native GUI". SQX's interface is
already HTTP + WebSocket on localhost, so anything a browser can do to it, code can do to it.

### The live event channel

🔬 The GUI does not poll for progress — it subscribes. From `internal/web/common/Batch1/libs.js`:

```js
C("/main/getWebSocketPort", {}, "GET", function (e) {
    x("ws://" + window.location.hostname + ":" + e.port + "/websocket/updates",
      "WebSocketMessageMain")
})
```

So the sequence is `GET /main/getWebSocketPort` → `{"port": N}` → connect
`ws://localhost:N/websocket/updates`. The client vocabulary around it includes `progressChannel`,
`progressUpdateEvent`, `progressPercent`, `progressAction` and `progressText` — the same fields that
draw SQX's own progress bars.

⚠️ **On this install the endpoint is gated.** `GET http://localhost:8080/main/getWebSocketPort`
returns `{"disabled":true,"error":"Remote access disabled"}` with the master GUI up. The websocket
port is therefore not discoverable from outside until remote access is enabled in SQX's own
settings. 🤔 Untested whether enabling it exposes the full `/main/*` surface or only the port lookup
— cheap to settle, and it is the single gate between the current CLI-only control and a real-time
progress feed.

### Progress without the websocket: the log

📓 Every task-level event goes through one logger, `c.s.t.project.ProgressEngine`, in a stable and
parseable vocabulary:

```
<TASK> : ================================
<TASK> : Starting strategies retesting...
<TASK> : Loading backtest data for Main test - <SYMBOL> / <TF>
<TASK> : All backtest data prepared
<TASK> : Sequential optimization: <STRATEGY> - Optimizing parameter <NAME>...
<TASK> : Task finished in N.N s.
Project finished
Databank '<PROJ>/<BANK>' loaded - N strategies in Nms
Databank '<PROJ>/<BANK>' saved - files before sync N / after sync N / saved N / removed N in N s.
```

🔬 Finer-grained progress is carried in the **thread name**, not the message:
`[Blocking computeThread common #45 - WF: 6 runs : 20 % OOS WFO 4]`. Tailing
`user/log/StrategyQuant/log_<date>.log` therefore yields both task boundaries and a percentage,
with no setting to enable and no risk to a running instance.

⚠️ That log is large and written fast — 55 MB by 20:44 on 2026-09-20. Tail it; never read it whole.

### What this means for controlling SQX from outside

| want | route | works with master GUI up |
|---|---|---|
| start a task chain | `-project action=start\|startOnlyTask\|startFromTask` | worker only |
| stop / pause / resume | `-project action=stop\|pause\|resume` | worker only; MCP `stop_project` on master |
| poll coarse state | `-project action=status` | worker only |
| live progress % | `/websocket/updates` | needs remote access enabled |
| live progress %, no settings change | tail `ProgressEngine` + thread names | ✅ always |
| count results as they land | `-databank action=count` on a timer | worker only |

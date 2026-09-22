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

⚪ **Owner's decision 2026-09-21: this one is not repaired.** The two facts above stay true forever
on this install, so treat them as permanent: **the project list is 14 against 15 directories**, and
**the hourly sync error keeps being logged**. Diff the list against the directory as always — just
do not re-diagnose that one gap. What follows is kept for a change of mind, not as pending work.

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

## The three-install topology — decided 2026-09-21, **built 2026-09-21**

One master plus **two** headless workers **per machine**, each with a fixed role. The decision and
its reasoning live in `docs/AgentPDFs/plan-ejecucion-2026-09-21.md` §3; the facts are here.

🔬 **Built and verified on PC-A, 2026-09-21.** All three installs exist and each answered on its own
port with the other two down:

| install | CLI | editor | web | `-Xmx` | `-Xms` | `coreUsage` | size |
|---|---|---|---|---|---|---|---|
| `SQX` (master) | 5050 | 5051 | 8080 | 24g | 2g | −1 | 9.7 G + History |
| `SQX_w1` (conductor) | 5060 | 5061 | 8081 | 16g | 1g | 8 | 4.4 G |
| `SQX_w2` (custodian) | 5070 | 5071 | 8082 | 48g | 1g | 48 | 4.3 G |

- 🔬 **The CLI port is not a setting in `user/settings/settings.xml` and not in the binary** — the
  `sqcli` binaries of all three installs are byte-identical (same MD5). It lives in
  `internal/AppSettings.txt`, as `<AppWebServerPortSQUANT>` plus `<AppWebServerPortSQEDITOR>`. The
  third port, the web GUI, is `<WebServerPortUsed>` in `settings.xml`. **Three files, two places.**
- 🔬 **`coreUsage` is absent from a fresh clone's `settings.xml`, and absent means every core.** W1
  ran for weeks with no `coreUsage` element at all, i.e. all 96, competing with the master's own −1.
  `clone-sqx-worker.sh` now writes it per role; an install cloned before that date needs it added by
  hand.
- 🔬 **`-Xms` is what an idle worker costs.** Dropped from the shipped `4g` to `1g`, a freshly
  started worker commits **1.7 GB** (`jstat -gc`, eden 1.0 + old 0.7) instead of 4 GB, on both
  workers, whatever its `-Xmx`.
- ⚠️ **Before 2026-09-21 the two installs promised 140 GB of heap on a 125 GB machine** (master
  `-Xmx108g` + W1 `-Xmx32g`). It never failed only because the two were never full at once. Now
  24 + 16 + 48 = **88 GB**, which is what the budget in `07-practices.md` allows.
- 🔬 **`user/data/History` is a symlink to the master's**, on both workers — the 84 GB raw archive
  exists once. The H2 bar files are per-install copies, because H2 takes an exclusive lock.
- ⚠️ **A worker is cloned without `user/projects`**, so W2 starts with only the five stock projects
  (`Builder`, `Optimizer`, `Retester`, `PortfolioMaster`, `PortfolioComposer`). That is correct for
  a custodian: it receives the databank it is given, and nothing else.

| | install | GUI | `-Xms` | `-Xmx` | `coreUsage` (96c / 16c) | ports |
|---|---|---|---|---|---|---|
| **M** master | `~/Desktop/SQX` | the owner's | `2g` | `24g` | **`-1` on both — untouched** | 5050 / 5051 / 8080 |
| **W1** conductor | `~/Desktop/SQX_w1` | never | `1g` | `16g` | 8 / 2 | 5060 / 5061 / 8081 |
| **W2** custodian | `~/Desktop/SQX_w2` | never | `2g` | `48g` | 48 / 8 | **5070 / 5071 / 8082** |

**Why two workers and not one.** Three reasons, in order of value:

1. 🔬 **A busy worker cannot answer.** With one worker, a three-hour retest queues every interactive
   query behind it — list, count, status, authoring. A small always-awake conductor is what keeps
   the system answerable. This is the main reason and it is about responsiveness, not throughput.
2. 🔬 **It removes a whole class of the rule-1 failure.** Every sync deletes on-disk `.sqx` not held
   in memory, so any command to the install holding a 5,000-variant databank is a risk. Give that
   databank its own install and the risk does not get mitigated, it **stops existing** — provided
   the custodian receives no command between "start" and "collect".
3. 🔬 **It overlaps the two expensive stages.** W1 exports mother *N*'s trades while W2 retests
   mother *N+1*'s variants.

**The core split is elastic, not static.** Leave the master at `-1` and cap only the workers. Linux
CFS then shares by runnable-thread count: with the workers idle the master keeps the whole machine
and the owner's 24/7 generation loses nothing; with W2 running (95 threads vs 48) the master still
holds ~66 %. A static three-way split would cost half the generation even on an empty machine — and
it means **the master's own `settings.xml` is never edited**, which keeps hard rule 3 clean.

⚠️ 🔬 **An install's core setting is `<coreUsage>` in `user/settings/settings.xml`, and `-1` means
"all".** The master carries it; **`SQX_w1`'s settings.xml is 38 lines and does not contain the key
at all**, so until 2026-09-21 both installs believed they owned all 96 cores.

🔬 **A third install costs ~3 GB of disk, not 98.** `SQX_w1` is 4.5 GB against the master's 98 GB
because `user/data/History` is a **symlink** to the master's (84 GB shared) and only the three H2
bar files are copied (42 MB). The rest is `internal/` at 2.8 GB. Disk is never the argument against
another install.

## 🔬 `sqcli` rewrites two `.version` stamps on start, so `check` cries STALE forever (2026-09-21)

`bin/sqx-worker.sh check` compares `user/data/*.version` precisely because the `.db` files are not
comparable — H2 rewrites a database header every time it is opened. **The `.version` files are not
safe either.** Measured on the conductor, worker stopped throughout except where stated:

| step | `data_futures.version` worker vs master |
|---|---|
| `sync` with the worker stopped | **equal** — `check` green, exit 0 |
| `start`, then `check` | `202609201214` vs master's `202609181234` → **STALE**, exit 1 |
| `stop`, `sync`, `check` | equal again, exit 0 |

The md5 of the file changes across the start (`c46fbd6c…` → `a02699c3…`) and its mtime becomes the
moment of the start. `sqcli` writes its own stamp into `data_futures.version` and
`data_stock.version` on every launch — always the same value, and one *newer* than the master's.
`brokers.version` and `group_of_stocks.version` are left alone.

🔬 **It is the same value on a different install.** `SQX_w2`, cloned from the master hours later and
never run by anyone but its cloning agent, showed `202609201214` on both files before this session
touched it — the identical stamp `SQX_w1` writes. So this is not per-install drift accumulating: it
is one fixed value `sqcli` stamps wherever it runs. 📓 Where it comes from is **not** the shared
`user/data/History` store — nothing under it has an mtime anywhere near 2026-09-20 12:14. Origin
still unknown; a future session can skip that search.

Consequences, in the order they bite:

- **`check` used to report STALE on a perfectly current worker** as soon as it had run once, with a
  message that read `worker <stamp> < master <stamp>` — and the `<` was backwards, since the
  restamped value is the newer of the two. **Fixed 2026-09-21 (evening).** `check` now knows which
  two files `sqcli` restamps, prints them as `restamp`, and does not count them toward its verdict.
  So `sqx-worker.sh check` exits 0 on a healthy worker and its exit code is usable again.
- ⚠️ **The price of the exemption:** a genuine futures or stock import on the master is no longer
  flagged by `check`. Accepted deliberately — `start` syncs unconditionally before every run, so the
  worker cannot run on stale bars whatever `check` says. `data.db`, where this project's forex bars
  live, is still compared for real.
- 🤔 The sync logic itself is right and is deliberately left alone: the copy at start is always safe
  and always current. What was wrong was only the *freshness report* after the fact.

## 🔬 `rsync` creates its destination, so a role that was never cloned must be refused

`sync_bars` does `rsync -a "$MASTER/user/data/" "$WORKER/user/data/"`. Point that at a role whose
install does not exist and it happily builds `~/Desktop/SQX_w2/user/data` — 42 MB of bars with no
`sqcli` around them. `bin/clone-sqx-worker.sh` then refuses to clone that role, because "the worker
already exists". `sync_bars` now stops unless `$WORKER/sqcli` is executable. `check` and `stop` are
read-only and still report on a missing install, which is what you want while setting one up.

## Driving a role from Python and from bash (2026-09-21)

🔬 `core/paths.py` holds the roles in `WORKERS`, a map of role → `{"path", "port"}`, plus
`worker_dir(role)` and `worker_staging(role)`. The **conductor is not an entry of `machine.yaml`'s
`sqx_workers` block**: it is `sqx_worker` + `worker_port` themselves, so its port exists in exactly
one place and `WORKER`, `WORKER_PORT` and `STAGING` keep meaning what they always meant. Every
consumer written before the roles existed still works untouched.

`core/worker.call/start/stop/wait_ready` take `role="conductor"` as their last argument.
`bin/sqx-worker.sh` and `bin/clone-sqx-worker.sh` take `--role ROLE` / `ROLE` and **ask Python** for
the install rather than parsing YAML — three lines on stdout, `MASTER`, path, port. That is what
keeps `paths.py` the only thing in the project that knows where anything lives.

🤔 A role `machine.yaml` does not define raises `KeyError` rather than falling back to the
conductor. A silent fallback would send a three-hour retest to the install that must stay
answerable, and that failure would be invisible until something was already lost.

🔬 **The port triple is derivable, so a new role sets one number.** Editor is `cli + 1` and web is
`8080 + (cli - 5050) / 10`: master 5050/5051/8080, conductor 5060/5061/8081, custodian
5070/5071/8082. `clone-sqx-worker.sh` computes both from the role's cli port instead of carrying
three constants that can disagree.

## ⚠️ The command API listens on 0.0.0.0, with no authentication

🔬 2026-09-21, `ss -ltnp`:

```
LISTEN 0.0.0.0:5050   users:(("StrategyQuantX",pid=3385011))
LISTEN 0.0.0.0:8080   users:(("StrategyQuantX",pid=3385011))
```

Not `127.0.0.1`. Anyone on the same network can send `-project action=start` or
`-databank action=clear`, because the API asks for no credentials. Two consequences:

- **Defensive**: close 5050/5051/5060/5061/5070/5071/8080/8081/8082 at the firewall on any machine
  that is not on a network you fully trust. Needs `sudo`, so it is the owner's to run.
- **Opportunity, unused for now**: a worker on another machine is drivable over the LAN without any
  daemon of its own. The owner's machines are used independently, so this is not being built — but
  it is the reason a future multi-machine design would not need one daemon per box.

## 🔬 Running a project task headlessly: `startOnlyTask` lies, `start` works (2026-09-22)

Two days of "the retest does nothing" came down to two things, and neither reports an error.

- 🔬 **`-project action=startOnlyTask name=X task=1` reports success and tests NOTHING.** It logs
  `Starting project 'X' task 1 only` and `=========== Project started ===========`, and then
  `action=status` says `Total tested 0 · Running time so far 0 ms` forever. No error, no
  `Project finished`, nothing in the log. **`-project action=start` on the same project, the same
  databank and the same instant runs the task properly** — `Total tested 11 · Time per strategy
  67 ms`. Whatever `startOnlyTask` is for, it is not this.
  ⚠️ `action=start` runs the **whole chain**, so it is only safe on a project that is a single task.
  On a project with a Build task and a `GoToTask` it starts perpetual generation. The harness this
  project drives (`Retester` on W2) holds exactly one Retest task, and it has to stay that way.

- 🔬 **A Retest task without `<Databanks retestSelected="false">` retests nothing.** A harness built
  by hand, or a stock `Retester` project, carries `<Databanks>` with no attribute; a task that has
  actually run carries `retestSelected="false"` and a `<SelectedStrategies />` element beside it.
  Absent, SQX retests "the selection", the selection is empty, and it reports 0 without complaining.
  **Build a task by copying one that has run, not by editing one that has not.** Structurally
  diffing the two is what found this: the donor also carries `Broker`, `Swap`, `Session`,
  `SequentialOptimization`, `CustomAnalysis`, `ForceRunCrossChecks` and `DeleteFailedStrategies`,
  none of which the stock harness had.

- ⚠️ 🔬 **`<DeleteFailedStrategies>true`** is in the donor and would delete any variant that fails
  the acceptance conditions. For a parameter study that is fatal — a missing variant and a variant
  that lost money become the same thing. The harness sets it `false` and sets all 30 conditions
  `use="false"`.


## 🔬 Running a task twice: `action=start` needs an `action=stop` first (2026-09-22)

A second `-project action=start` on a project that has already run **does nothing**, silently: no
error, no log line, `Total tested` stays 0 forever. `-project action=stop` first, then `start`, and
it runs — measured back to back, 0 before the stop and `tested=2` ten seconds after it.

The project does not report itself as running in the meantime; `action=status` shows zeros either
way, so the status output cannot distinguish "finished" from "never started" from "refusing to
start again". Always stop before starting, even when you believe nothing is running. It costs one
call and it is the difference between a run and an hour of confusion.

## ⚠️ The SPP cross-check runs headlessly but leaves nothing behind (2026-09-22)

**Unresolved, and it blocks running new SPPs on a worker.** Measured on the custodian with a task
copied verbatim from the owner's own `SPP IS` task (`Retest-Task13.xml` of the frozen donor),
`SequentialOptimization use="true"`, `DistributionUp/Down 35`, `Steps 40`.

What happens: the log fills with
`ProgressEngine - Sequential optimization: <strategy> - Optimizing parameter <name>...`, once per
tunable parameter, so the cross-check **is executing**.

What does not happen, in any combination tried:

| tried | `Total tested` | output databank | `optimizationProfile.bin` on the strategy |
|---|---|---|---|
| acceptance conditions all `use="false"` | 2 | empty | **absent** |
| acceptance conditions as the donor writes them (19 active) | 0 | empty | absent |
| input and output the same databank | 0 | — | absent |

- 🔬 **The plain retest in the same harness works**, which is the control: the strategy comes back
  with `orders.bin` and `Results/…/dailyEquity.bin` written, so the backtest ran and was saved. Only
  the SPP product is missing.
- ⚠️ **A trap that cost real time: a strategy staged out of `raw/…/strategies/` already carries a
  306 KB `optimizationProfile.bin` from the master's own run.** Reading it back after a worker SPP
  looks like success and is not. Test on a fabricated variant instead — the five-member shape has no
  profile member at all, so "did a profile appear" becomes a question with a yes-or-no answer.
- 🤔 The likely candidates, untested: the profile may only be persisted by the GUI's own SPP task;
  `dontStoreOP3DChartsData` is already `false` on both installs so it is not that; `ApplyToStrategy`
  is `false` in the donor and may gate the write.
- **Consequence for the protocol:** a design brief can only be built from an SPP the *master* has
  already run. `strategies/sppUltra` needs `permutations.csv` and `permutation_params.csv`, and
  those come from `export_spp.py` reading a profile that only the master currently produces.
  `export_spp.py --role custodian` now exists and works — what is missing is a profile for it to
  read.

## 🔬 `optprofile.read` reports `permutations` even when it kept no per-permutation rows

The same 306 KB profile reports `permutations: 2533` whether or not `results` holds anything. The
count is a summary field; `permutation_results` plus a non-empty `results` is what says the detail
is there. A reader that checks only the count concludes a profile is usable when it is not.

📓 And the count is not the export's row count either: `runs.csv` of the 2026-09-10 export records
3,940 permutations for `Strategy 17.9.39` while its profile's `permutations` field says 2,533.
Whatever the field counts, it is not rows. Use `len(results)`.

## 🔬 What an SPP actually costs headlessly, and why silence is not a hang (2026-09-22)

Measured on the custodian, one real XAUUSD mother (22 tunable parameters), `Steps 40`, ±35 %,
`testPrecision 1` (one-minute bars), 2008–2017, M30.

- 🔬 **It logs once per parameter, at the start, and then says nothing for the rest of the run.**
  All 22 `Sequential optimization: <strategy> - Optimizing parameter <name>...` lines appear within
  three seconds; the next log line is over **half an hour** later. `-project action=status` reports
  `Total tested 0` and `Running time so far 0 ms` throughout — the status endpoint has no
  per-permutation progress at all.
- 🔬 **The honest progress signal is the JVM's resident memory**, which climbs steadily while the
  run accumulates permutation results: 23.6 → 25.7 → 32.5 → 36.9 GB over roughly thirty minutes, on
  a 48 GB heap. A flat RSS with no log output is a hang; a climbing one is work.
- ⚠️ **So `sqx/variants/spp.py` cannot report a real percentage**, and does not pretend to: it
  reports elapsed seconds against its cap. Anything else would be invented.
- ⚠️ **Memory is the binding constraint, not time.** The profile for a strategy of this size is
  ~20 MB on disk but tens of gigabytes while it is being built. A 48 GB heap holds one at a time;
  running two SPPs concurrently on one install is not safe.

🤔 **The contrast with a fabricated variant is the diagnostic.** The same harness on a five-member
variant with 8 parameters finished in seconds, used no memory and wrote no profile. Same task, same
settings — so "the SPP does nothing headlessly" was the wrong conclusion drawn from too small a
subject. Reconnaissance is only meaningful on a strategy with real parameters and real trades.

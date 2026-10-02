# ui/daemon/launch — «Lanzar en SQX», the rail's ▶ SQX, and «Correr workflow»

Owner, 2026-09-28: «quiero un botón para lanzar la que yo quiera», then «que se pueda correr cada
paso del workflow, tanto en python como en SQX … y otro botón para correr el workflow entero». The
row under Proyecto's title launches any one task; each SQX card of the rail launches **all** its
step's tasks in one start of the worker; «Correr workflow» runs every pending step, SQX and Python,
in WORKFLOW.md's order, up to the first decision that is the owner's. The sibling of
`ui/daemon/advance/` («Continuar workflow»), whose worker preflight, readiness wait and log
watcher it reuses.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `liverun.py` | `execute` for a GUI session already up (`sqx.projects.live`): rule 5, snapshot, configurators on a COPY of the cfx, `stage.just` on it, `live.push`, fills loaded into memory, run, sync, the same compare/record, `afterrun --live` — no stop, no start. The autopilot's `--live` calls it | imported | preflight → `{title: (before, after)}` |
| `preflight.py` | `tasks(project)`: the project's tasks with the `.sqx` their input and output hold on disk; `check(project, titles, step, own_log)`: `advance.where` (the master refused first), `advance.busy` (the owner lock held by someone else, the port up, a live SQX process, the log still moving — that last one ignored with `own_log`, when the chain wrote it, or when a window job released the worker after that write; another project touched a while ago is no longer a refusal, `OPEN.md` §83), the tasks exist, a build only on the custodian, a retest with an empty input refused unless another chosen task fills it; `configure`, the configurators a chosen task still needs; `judge` is the same once those are read (the rail's ten SQX steps at once); `text`: the sentence to confirm | imported | project, task(s) or step → `{ok, reasons, chosen, off, …}` |
| `steps.py` | `of_step(n, cfx)`: the titles an SQX step switches on (`stage.titles`), every one required in the project; an MC Retest task its configurator silenced (`<MonteCarloRetest use="false"`) stays off and is named; `ELSEWHERE`: 5, 10.5 and 16.5, which are not a task start | imported | step, project.cfx → titles |
| `configure.py` | `run(pre, say)`: the configurator of every chosen task whose cross-check is still off (`steps.unconfigured`) — `sqx.projects.crossmarket`, `spp`, `wfm` — as its skill runs it, worker stopped; shared by «Lanzar en SQX» and «Continuar workflow» (📓 2026-09-30: Continuar launched Cross Market with its cross-check off, a plain retest) | imported | preflight → configured tasks |
| `run.py` | The job: preflight again; `python3 -m core.assets <SYMBOL>` (hard rule 5); the project folder copied without `log/` to `AlgoData/projects/snapshots/<P>/<stamp>/`; `configure(pre)` — the step's configurator (`sqx.projects.wfm`, `spp`, `crossmarket`) on a chosen task whose cross-check is off, never on a configured one (`steps.unconfigured`; owner, 2026-09-29: the WFM had run in 6 s as a plain retest); `stage.just` (only those titles on); `core.worker.start` once; `advance.run.ready` (status answered AND the databanks loaded from their files); `-project action=start`; `advance.run.watch` until «Project finished»; `core.worker.stop` in a `finally`; then every databank no chosen task writes compared — one that fell keeps the copy, else it is deleted — and a build's `runs.csv` row. `execute(pre, project)` is the part the chain calls | `python3 -m ui.daemon.launch.run --project P --task CONSTRUCCION` (repeatable) or `--step 13` (the window queues it) | a project → its tasks run, worker stopped |
| `chainplan.py` | The stop rule over GET /api/workflow's steps: `plan(data)` → `do` (steps in order, SQX or Python with its tests) and `stop` (the step before which it halts, and why); `RULE`, the sentence. Pure | imported | rail → plan |
| `chain.py` | «Correr workflow»: `check` (the plan, `advance.where`/`busy`, each SQX step's tasks), `text`, and the job — per SQX step `preflight.check` then `run.execute` (one start, one stop); per Python step the loader's missing pieces (`loader.state.commands`) run and waited for, then each test's commands (`workflow.run.plan`) side by side; the first failure stops it | `python3 -m ui.daemon.launch.chain --project P` (the window queues it) | a project → steps run up to the next decision |
| `api.py` | `GET /api/launch/tasks`, `GET /api/launch/preflight?task=|step=`, `GET /api/launch/steps` (every SQX step's ▶ SQX), `POST /api/launch/run {task|step}`, `GET /api/launch/chain`, `POST /api/launch/chain` — each job one on the conductor lane, labelled `launch`; this or a «Continuar» queued or running is a refusal, both ways | imported | request → JSON |

## The chain's stop rule

`chainplan.plan` walks the rail in WORKFLOW.md's order. 1-5 are walked past only when done (5,
10.5 and 16.5 are chat work: a halt when pending); **any step running is a halt**, Python too. A
Python step already done is skipped (its leftover tests run with their own ▶ PY) unless an SQX step
ran earlier in this press, which makes everything after it rerun. A Python step runs the tests
«todas las pruebas Python pendientes» runs (`auto`: never `workflow.tests.SPENDS` — wfc, cscv,
marketSurfaces, wfm, blindJoint, snoopingScreen — never 21-25, never what the window refuses). A
judging step (8, 10, 12, 14, 16 — the even steps' verdict contract) that is not done, or ran in
this press, **always** halts the chain before the next SQX step; one not done with no test the
chain can run halts at itself. The only crossing: a press that starts ON the SQX step, its judge
already done. It also halts before 19 (the WFM reads oos2) and at the first failure.

The job runs **the plan the owner confirmed**: the rail posts the plan it showed, the route
refuses when a fresh plan differs, writes it to `AlgoData/logs/ui/chain-<P>-<stamp>.json` and
passes `--plan`. Before each step the job re-reads the rail: a step now running, or — before any
SQX step of this job ran — in another state than confirmed, halts it. Before each SQX step it
re-checks safety (`preflight.check`, `own_log` once the job ran anything, `filled` = outputs of
the SQX steps it already ran) and that the step's titles are the confirmed ones.

## Traps

- **The worker table is `advance.preflight.WORKERS`**, not `core.paths.WORKERS` read directly:
  one table that `tests/test_launch.py` points at a scratch install.
- **What the task clears when it starts is its SQX configuration**, the owner's (hard rule 3):
  the launcher does not change it. It only compares afterwards and keeps the copy when a
  databank the task does not write lost files (hard rule 1).
- **The chain's second SQX step would be refused by the log its first one wrote** (`busy`'s «log
  written < 15 min»): `check(own_log=True)` passes `advance.busy(..., own_log=True)`, which skips
  that one check; the port, the process and the «started and not finished» checks stay.
- **The chain runs the loader's exports itself**, not through `jobs.py`: they belong on the
  conductor lane, which the chain holds until it ends — queued there, they would wait for it.
- **`sqx-worker.sh start` answers 0 on «already running», `stop` 0 on «STILL RUNNING after 5
  min».** `run.execute` and `advance/run.advance` call `workerguard.refuse_if_up` before any copy
  and again right before the start — up, they exit without touching or stopping it — then
  `workerguard.mark` right after the start (`AlgoData/logs/ui/workers/<role>.json`, the job's
  PID) and `workerguard.stopped` after the stop: still up, the marker stays and the run fails
  before any databank is read, so the chain halts.
- **Cancelling** from «En marcha»: a `launch`/`advance` job gets SIGTERM (`run.graceful`;
  `chain.cancelled`, which also kills the running tests and starts no queued one; advance's own
  handler), so its `finally` stops the worker; SIGKILL only after `winddown.GRACE_S` (360 s).
  The daemon stops a worker itself **only when the job's marker carries its PID**: a job that
  never started one (cancelled during a Python step, the snapshot, the curate, or refused
  because someone else's worker was up) never stops anything. The lane stays busy and `rc`
  None («cancelando…») until that stop ends; «⚠ el <rol> sigue arrancado» in the job's state
  (and in red on the rail) only behind the job's own marker.
- **Closing the window does not cancel**: uvicorn re-raises SIGTERM, atexit (`jobs._reap`) is
  skipped, and a launcher runs on, orphaned, to its natural end, stopping its own worker. The
  next window reads its marker: `/api/launch/steps` `warnings` (painted on the rail), and
  `api.queued()` refuses any launch while that job lives.
- **While a launcher job runs on a project, no test starts on it** (`workflow.tests.one`). The
  chain's own Python tests do not pass through `jobs.py`: they keep its core width (`WIDE` one
  at a time, else `SLOTS // LIGHT`) and its RAM rule (`chain.floored`).
- **A snapshot is `<stamp>.partial` until complete**, and a copy cut short is removed.

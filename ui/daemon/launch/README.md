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
| `__init__.py` | «Lanzar en SQX»: run the one task of a project the owner picks, on its worker, and stop it after. | imported | — |
| `api.py` | The routes of «Lanzar en SQX» and «Correr workflow»: tasks, steps, preflights and the jobs that run them. | imported | request → JSON |
| `chain.py` | «Correr workflow»: every pending step in WORKFLOW.md's order, SQX and Python, up to the next decision. | `python3 -m ui.daemon.launch.chain --project P` (the window queues it) | a project → steps run up to the next decision |
| `chaincheck.py` | «Correr workflow», before the press: whether the chain may start, what it would run, the sentence to confirm. | imported by `api.py` and `chain.py` | project → ok, reasons, plan |
| `chainplan.py` | What «Correr workflow» runs, in WORKFLOW.md's order, and the step it stops before — from the rail. | imported | rail → plan |
| `configure.py` | Run the configurator of every chosen task still unconfigured, as its skill does, with the worker stopped. | imported | preflight → configured tasks |
| `liverun.py` | «Lanzar en SQX» on a GUI session already up: configure a copy, push it, run, mirror to disk, export — no restart. | imported | preflight → `{title: (before, after)}` |
| `preflight.py` | Whether «Lanzar en SQX» may start one task of a project now, and every reason it may not. | imported | project, task(s) or step → `{ok, reasons, chosen, off, …}` |
| `run.py` | «Lanzar en SQX»: switch on one task or one step's tasks, start the worker once, wait for SQX, stop. | `python3 -m ui.daemon.launch.run --project P --task CONSTRUCCION` (repeatable) or `--step 13` (the window queues it) | a project → its tasks run, worker stopped |
| `steps.py` | Which SQX tasks one workflow step launches from the window, and the SQX steps it cannot launch. | imported | step, project.cfx → titles |

## The chain's stop rule

`chainplan.plan` walks the rail in WORKFLOW.md's order. 1-5 are walked past only when done (5,
10.5 and 16.5 are chat work: a halt when pending); **any step running is a halt**, Python too. A
Python step already done is skipped (its leftover tests run with their own ▶ PY) unless an SQX step
ran earlier in this press, which makes everything after it rerun. A Python step runs the tests
«todas las pruebas Python pendientes» runs (`auto`: never `workflow.tests.SPENDS` — wfc, cscv,
marketSurfaces, wfm, blindJoint — never 21-25, never what the window refuses). A
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

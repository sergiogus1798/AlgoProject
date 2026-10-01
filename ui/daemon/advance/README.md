# ui/daemon/advance — «Continuar workflow»

The one route of the window that changes what SQX holds (encargo 22 §7.2 point 3, plan 24 F7).
The owner filters in the window (F6: `AlgoData/filters/<P>/<D>/discards.jsonl`, nothing in SQX);
this button turns those discards into a curate and launches the next task, behind a preflight and
a confirmation. Sequence and evidence: `knowhow/sqx-drive/window-advances-workflow.md`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `preflight.py` | Every refusal, in order: registry install (the master first, always refused), the worker's owner lock (`OPEN.md` §32, who holds it and since when), its port and any SQX process in it, today's SQX log written in the last 15 min — unless a window job released the worker after that write (`workerguard.own_last_write`, owner 2026-09-29) — or a run unfinished, no discards, no `.sqx` on disk, no later task that reads the databank. Another project touched a while ago is not a refusal (`OPEN.md` §83). Read-only: socket, `/proc`, the lock file, file dates | imported | project, databank → `{ok, reasons, …}` |
| `confirm.py` | The literal sentence of §7.2 the owner confirms | imported | preflight → text |
| `buildcap.py` | The build's time cap (owner, 2026-10-01: N strategies or M minutes, whichever first): `minutes` reads it from the Build task's `StopCondition` (SQX itself stops only on N under `databank-full`); `enforce`, called by `run.watch` each poll, sends `-project action=stop` once the running build has used it — the project then does not go on to its next task | imported | project.cfx + running task → stop |
| `run.py` | The job: preflight again; copy the discarded `.sqx` to `AlgoData/projects/discards/<P>/<D>/<stamp>/` with `verdict.csv`; `sqx.curate.apply_verdict.apply` with the registry's role; one ledger row; a `cut` line in F6's discard log; when the next task reads a databank no task writes (`CrossTF_Input` after Cross Market, `CrossTF_Mothers` after Cross TF), `sqx.projects.crosstfload.fill` with the worker stopped; `ui.daemon.launch.configure.run` on a next-step task whose cross-check is still off; `sqx.projects.stage.apply` leaving on the next step's tasks that read the cut or an on task's output (never a silenced MC Retest); `core.worker.start`; `-project action=start`; then `progress.state` (status) each poll and `sqxlog` until «Project finished» — failing, worker stopped, if SQX never logs the start within 120 s, refuses the start, or passes 48 h; `core.worker.stop` in a `finally` that also covers a failed `worker.start` | `python3 -m ui.daemon.advance.run --project P --databank D` (the window queues it) | discards → databank cut, next task run, worker stopped |
| `sqxlog.py` | SQX's own log from the launch on, yesterday's and today's file: `mark` the offsets just before `action=start`, `grow` reads only what was written since, so an earlier finish never ends this run and a run across midnight is followed | imported | install → log lines |
| `api.py` | `GET /api/advance/preflight`, `POST /api/advance/run` (one job on the conductor lane of `jobs.py`; a second one queued or running is a refusal) | imported | request → JSON |

## Traps

- **A worker that is up is refused, never stopped** (owner, Q6): `stop` kills anyone's run
  (`OPEN.md` §32). The job stops only the worker it started itself.
- **Between `start` and «Project finished» the only verb is `-project action=status`**, sent
  by `progress.state` through `tasklog.status`. The readiness wait asks `status` too, never
  `list` (which `awake()` uses) and never `count` (which syncs from files, hard rule 1).
- **Cancelling the job from «En marcha» kills it with SIGKILL**, so its `finally` does not
  run and the worker stays up: stop it with `bin/sqx-worker.sh --role <role> stop`.
- **A cut consumes the discards**: `run.consume` appends `{clear, cut, ts, removed, task}` to
  F6's `discards.jsonl` (orchestrator, 2026-09-28). `clear` is what `discards.since_clear` cuts
  at, so the next filter starts from what the databank now holds; earlier lines stay as history.
- **The next task is the first one, in WORKFLOW.md's order after the databank's step, that
  reads that databank**, and only that task is switched on — for `Results` it is `OOS`, not
  the MC Retest or the SPP, which read it too.
- **SQX's log is per day.** `progress.log_lines` reads today's file only; a run launched at
  23:59 would never show its «Starting project» there. `sqxlog` reads both days from offsets
  marked before the launch.
- **The confirmation counts identities, the cut counts files.** SQX can hold one strategy under
  two names; both go, and the sentence says so when files outnumber identities. Identities are
  hashed once per file (path, size, mtime) — the window re-checks every 20 s.

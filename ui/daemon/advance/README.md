# ui/daemon/advance — «Continuar workflow»

The one route of the window that changes what SQX holds (encargo 22 §7.2 point 3, plan 24 F7).
The owner filters in the window (F6: `AlgoData/filters/<P>/<D>/discards.jsonl`, nothing in SQX);
this button turns those discards into a curate and launches the next task, behind a preflight and
a confirmation. Sequence and evidence: `knowhow/ui/window-advances-workflow.md`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | The routes of «Continuar workflow»: its preflight, and the one job that applies it. | imported | request → JSON |
| `run.py` | «Continuar workflow»: copy the discards aside, cut the databank, start the next task and wait. | `python3 -m ui.daemon.advance.run --project P --databank D` (the window queues it) | discards → databank cut, next task run, worker stopped |

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
  23:59 would never show its «Starting project» there. `sqx/log.py` reads both days from offsets
  marked before the launch.
- **The confirmation counts identities, the cut counts files.** SQX can hold one strategy under
  two names; both go, and the sentence says so when files outnumber identities. Identities are
  hashed once per file (path, size, mtime) — the window re-checks every 20 s.

---
name: sqx-wait
description: Look at who holds the three SQX installs before touching a worker, and wait for an SQX run in ONE background command that exits on `Project finished`, an aborted run, a dead sqcli, low RAM or a time bound (rule 18). Use before starting, stopping or querying a worker, and right after any `action=start`, instead of writing an `ss`/`OWNER`/`until grep` loop by hand.
---

# /sqx-wait

Two scripts, so no session rewrites them. Neither changes anything in SQX.

## Before touching a worker (rule 3)

```bash
.claude/skills/sqx-wait/preflight.sh
```

Per install: port up or down, its `sqcli` PID, the `OWNER` lock, the five newest projects. Then
`ListAgents`. A lock held by another session, or the master's port up when the job needs it
closed: stop and tell the owner — never `--force`, never `pkill -f`.

## Waiting for a run (rule 18)

```bash
N=$(.claude/skills/sqx-wait/wait.sh --role custodian mark)   # BEFORE action=start
# ... action=start through the step's own skill ...
.claude/skills/sqx-wait/wait.sh --role custodian --from "$N"  # run_in_background: true
```

`mark` prints `FILE:LINE` — the log it marked and where it ended. The wait reads that file from
that line and every newer log whole, so a log opened between the mark and the wait (midnight, a
worker started after the mark) loses nothing. A bare line number, the mark of the script before
2026-10-03, is still taken: it means the newest log at wait time. `--max-hours N` (whole hours,
default 72) bounds the wait.

Launch the second command with `run_in_background` and do nothing until it notifies: no `Monitor`,
no `sleep` loop, no `action=status`. It prints one line and exits:

| exit | line starts with | then |
|---|---|---|
| 0 | `finished` | collect through the step's skill, then `bin/sqx-worker.sh --role ROLE stop` |
| 1 | `failed` (`Project stopped`, `Exception in task`, `OutOfMemory`, `Error while running project` — SQX aborted the run and will never write `Project finished`) | delegate the log slice to a Sonnet subagent (rule 16), report |
| 2 | `gone` — the worker's port went down | same; the lock clears itself |
| 3 | `low-ram` — under 15 GB free | tell the owner; do not stop another session's job |
| 4 | `timeout` — no `Project finished` after `--max-hours` (72), the worker still up | tell the owner; the run may be alive — do not stop it, wait again with a fresh `--max-hours` if he says so |

`mark` must be taken before the start: a short job can finish before the wait begins, and a wait
that starts reading after `Project finished` never ends. The log rolls at midnight; the script
follows it.

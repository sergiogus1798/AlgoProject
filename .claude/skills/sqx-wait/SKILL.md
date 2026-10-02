---
name: sqx-wait
description: Look at who holds the three SQX installs before touching a worker, and wait for an SQX run in ONE background command that exits on `Project finished`, a dead sqcli or low RAM (rule 18). Use before starting, stopping or querying a worker, and right after any `action=start`, instead of writing an `ss`/`OWNER`/`until grep` loop by hand.
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

Launch the second command with `run_in_background` and do nothing until it notifies: no `Monitor`,
no `sleep` loop, no `action=status`. It prints one line and exits:

| exit | line starts with | then |
|---|---|---|
| 0 | `finished` | collect through the step's skill, then `bin/sqx-worker.sh --role ROLE stop` |
| 1 | `failed` (`Project stopped`, `Exception in task`, `OutOfMemory`) | delegate the log slice to a Sonnet subagent (rule 16), report |
| 2 | `gone` — the worker's port went down | same; the lock clears itself |
| 3 | `low-ram` — under 15 GB free | tell the owner; do not stop another session's job |

`mark` must be taken before the start: a short job can finish before the wait begins, and a wait
that starts reading after `Project finished` never ends. The log rolls at midnight; the script
follows it.

---
q: How do I retire my own Test_ project after a run and wait for another session's multi-task run?
kw: retire refuses touched in last 60 min, --own, wait.sh fires each Project finished, tail --pid, workflow.sh run --own-log, pkill -f matches own shell, pgrep -f project name
tag: 🔬  date: 2026-10-13  see: sqx-drive/owner-lock, sqx-drive/three-install-topology
---
# After a run: retire with `--own`, wait with `tail --pid`, relaunch with `--own-log`, kill by PID
- `python3 -m sqx.projects.retire <P> --role custodian --yes` refuses a project touched in the last 60 min; each SQX session rewrites every project's files, so after a run the guard never clears. The creator passes `--own`.
- `.claude/skills/sqx-wait/wait.sh` fires at each task's `Project finished`. To wait for ANOTHER session's multi-task run use `tail --pid=<SQX pid> -f /dev/null`.
- `bin/workflow.sh run <P>` after one's own failed try needs `--own-log`, else it waits 15 quiet minutes of the worker's log.
- 🔬 `wait.sh` can report a finished retest as failed: SQX logs an internal NPE (`ProjectGlobalLog.addAcceptedStats`) AFTER the task finished when a Retest is the first task of a fresh session; the bank is right (2026-10-13). It also cannot tell projects apart: another project's run ends the wait.
- `pkill -f` / `pgrep -f` with the project name matches your own shell: kill by PID.

## Evidence
- 🔬 Met repeatedly in the 2026-10-08/09 calibration campaign (cal1-cal6).

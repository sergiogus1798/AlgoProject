---
q: sqx.structural.keep refuses custodian sigue arriba PID is tail not sqcli; worker.holding false positive; Monitor tail -F on SQX log blocks safety check; nightly auditor claude -p blocks execute --clear
tag: 🔬  date: 2026-09-27  see: sqx-drive/variants-execute-needs-worker-it-started
---
# `worker.holding()` counts only a process whose executable lives in the install — fixed 2026-09-27
It used to match the install path ANYWHERE in a command line, so a `tail -F <install>/user/log/…`
(a Monitor) or a `claude -p` whose prompt names the install (the nightly auditor) read as a live SQX,
and `structural.keep` / `execute --clear` refused. Now: executable path inside the install, or a
relative executable (`./sqcli`, `./StrategyQuantX`) run from it. If a guard still names a PID, `ps -p`
it — it should now always be SQX.

## Evidence
- 2026-09-26: `structural.keep` refused naming a PID that was `tail -n0 -F "$LOG"` on the custodian's
  own SQX log; killing the Monitor let it through.
- 2026-09-27 03:07: `execute --clear` refused for the nightly auditor's two PIDs
  (`timeout 2h claude -p --agent auditor …`, cwd `AlgoProject`), for the whole 2 h of its run.
- After the fix: `bash -c "sleep 40; echo /…/SQX_w1/user/log"` → `holding(SQX_w1) == []`; conductor
  started → `[<sqcli pid>]`; stopped → `[]`.

---
q: sqx.structural.keep refuses custodian sigue arriba PID is tail not sqcli; worker.holding false positive; Monitor tail -F on SQX log blocks safety check
tag: 🔬  date: 2026-09-26  see: sqx-drive/variants-execute-needs-worker-it-started
---
# `worker.holding()` can be tripped by a `tail -F` on the SQX log, not just a live `sqcli`
`sqx.structural.keep` (and presumably anything else using `core.worker.holding()` as its "is the
install still up" guard) refused to run with `custodian sigue arriba (PID <n>): espera a que
'execute' lo pare` — but `ps -p <n>` showed that PID was a plain `tail` process, not `sqcli`, and
`ss -ltnp | grep 5070` showed nothing listening. The custodian really was stopped.

## Evidence
- 2026-09-26, right after `sqx.variants.execute` finished and manually stopped the custodian
  (confirmed no `sqcli` process, no listener on 5070), `sqx.structural.keep --work <batch>` still
  refused, naming a PID that `ps` identified as `tail` — the process behind a Monitor tool call
  running `tail -n0 -F "$LOG" | grep ...` against the custodian's own SQX log file
  (`~/Desktop/SQX_w2/user/log/StrategyQuant/log_2026_09_26.log`), used all session to watch for
  `Task finished`/`Project finished` lines.
- Stopping that Monitor task (which kills the `tail -F`) made `sqx.structural.keep` proceed cleanly
  on the very next attempt, no other change.
- Read as: the holding-check likely walks open file descriptors under the install directory (or the
  log specifically) rather than checking for the `sqcli` process by name/cwd — a `tail -F` on the
  log holds exactly such a descriptor, and the check cannot tell "watching, harmless" from
  "SQX itself, still writing".
- 🤔 Untested whether this is `core.worker.holding()`'s general behavior or specific to how it
  resolves the log path; also untested whether an ordinary `grep -f` (not `-F`) or a one-shot `cat`
  of the log would trip it too, or only a long-lived open handle does.

**Practical consequence**: kill any `tail -F`/Monitor watching a worker's own SQX log **before**
calling a command that checks `worker.holding()` on that role (`sqx.structural.keep`, and likely
anything gated the same way) — otherwise the refusal looks like a real stuck process and wastes time
chasing a `ps` that comes back empty.

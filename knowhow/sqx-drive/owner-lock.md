---
q: owner lock on a worker; OWNER file; who started this worker; stop refuses different holder; --force stop; --owner flag; SQX_OWNER; CLAUDE_CODE_SESSION_ID holder; stale lock cleared; is the 24 h guard gone; does the lock replace released.json
tag: 🔬  date: 2026-09-29  see: sqx-drive/window-advances-workflow, sqx-drive/export-after-every-stop, databanks/sync-deletes-unloaded-files
---
# `bin/sqx-worker.sh` writes a real owner lock (OPEN.md §32); `advance.busy` reads it, not a project's mtime
Fix for §32 (owner, 2026-09-29): `start` writes `<install>/user/log/OWNER` (`{holder, pid, since}`);
`stop` from a different holder refuses unless `--force`; a dead PID with a down port clears it.
Holder = `$CLAUDE_CODE_SESSION_ID`, else `--owner`/`$SQX_OWNER`, else `"owner"`. One implementation,
`bin/sqx-lock.sh`, sourced by `bin/sqx-worker.sh`; `core.worker.start/stop` already ran through it.
`advance.busy` (`core.worker.lock`, read-only) names the holder; §83's 24 h "touched" refusal is
gone. **Does not replace `released.json`**: the lock is gone once the worker stops, and that
marker covers the minutes after.

## Evidence
- 🔬 A worker with no OWNER file (started by a version of `bin/sqx-worker.sh` before this lock
  existed) stops exactly as before — `refuse_stop_if_held` returns immediately when the file is
  absent (`tests/test_worker_lock.py::test_no_lock_is_never_refused`). A run already in flight when
  this shipped is never stranded.
- 🔬 `tests/test_worker_lock.py` sources `bin/sqx-lock.sh` against a fake install dir, never a
  real one: holder precedence, a live PID (real, transient, killed to simulate staleness) kept vs.
  cleared, a port-up lock kept even with a dead PID, and `refuse_stop_if_held` naming the holder
  and honouring `--force`.
- 🔬 `tests/test_advance_edges.py::test_busy_names_the_lock_holder` — `advance.busy` folds
  `core.worker.lock(top)`'s holder and timestamp into the port/PID busy reasons.
- 🔬 OPEN.md §75, same file: `stop` sent in the ~20 s after `start` returns (port up, CLI still
  booting) was silently swallowed, so it now waits for `SQX CLI is now ready` in the worker's own
  log (bounded 30 s) before sending `-exit`.

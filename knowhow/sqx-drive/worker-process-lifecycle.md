---
q: How do I tell a worker is alive, and when do `stop` and `start` exit 1 in `bin/sqx-worker.sh`?
kw: worker did not stop but still up; sqx-worker.sh stop exit code; stop exits 1 STILL RUNNING; start in progress flock .start.lock; two starts race; start timeout kills sqcli; stale XVFB file; stop on booting worker; find worker pid; process named sqcli; worker up then Connection refused; licence check exit; worker-daemon.log; how long does a worker take to open its port
tag: 🔬  date: 2026-10-03  see: sqx-drive/driving-a-role, sqx-drive/owner-lock
---
# A worker is alive while its port answers OR its process exists; `stop` and `start` exit 1 when they failed
`bin/sqx-worker.sh`: "running" = the port **or** a `sqcli`/`StrategyQuantX` whose `/proc/<pid>/cwd`
is the install (its command line is just `./sqcli`). `stop` exits **1** if the worker is still alive
at the end (lock kept, PIDs printed, no export). `start` and `run` hold a non-blocking `flock` on
`user/log/.start.lock` from check to launch: a second one exits 1, `REFUSING: … in progress`. A port
not up in 120 s: `start` kills the sqcli it launched, by PID, and exits 1. Never kill by pattern.
"worker up" can still be followed by a licence-check exit 2 s later: on a first `Connection
refused`, read the last 3 lines of `user/log/worker-daemon.log`.

## Evidence
```bash
ss -lptn 'sport = :5060'          # pid holding the port
readlink /proc/<pid>/cwd          # confirm .../SQX_w1 before killing
kill <pid>                        # by PID — never pkill -f (hard rule 2)
curl -s -m 3 "http://localhost:5060/call?cmd=-h" && echo up || echo down
```
🔬 `ps … | grep -i StrategyQuant` and grep for `SQX_w1` both missed it. Plain `kill` was enough.
📓 Licence exit: log ends `Server started on port 5060 … Verifying license ... Failed to check license -
Error - Program cannot connect to internet … Exit app`. Twice on W1 (07:47, 07:49) while
`curl https://www.google.com` → 200 and W2 stayed up; same W1 started fine at 07:17/07:29/07:38.
"worker up" = the port answered once. 🤔 Cause: SQX's licence server, not connectivity.

2026-10-03, the lifecycle fixes (all in `bin/sqx-worker.sh`; `tests/test_worker_lifecycle.py` drives a
copy of the script against a fake root, a fake install and a Python stand-in named `sqcli`):
- 📓 Port-open time: every `Starting StrategyQuant CLI` in `user/log/launcher_*.log` against the
  next `Server started on port` in `user/log/StrategyQuant/log_*.log` — W1 1,282 launches, W2 397
  (80 GB heap, `-Xms1g`): min 1 s, median 2 s, p95 3 s, **max 7 s**, none without a port. So 120 s
  without a port is a broken start, not a slow one: the wait stays 120 s and the timeout kills
  (SIGTERM, 30 s, then SIGKILL) instead of leaving an unowned sqcli to come up later.
- 🔬 The OWNER lock is written at launch, not once the port answers, so a booting worker is held;
  a failed start removes it. The daemon is launched with `9>&-`: inheriting fd 9 would make the
  worker itself hold the start flock for as long as it lives (the test asserts it does not).
- 🔬 Check-then-launch race: `guard_launch` ran before the log prune and `sync_bars` (md5 of the
  master's data + rsync), so two sessions both passed it — the 2026-09-23 port-rewrite incident.
  Now: flock, then `guard_launch`, prune, sync, `guard_launch` again, launch.
- 🔬 `user/log/XVFB` outlives a GUI crash or a reboot. `stop` took the GUI branch on it (no `-exit`,
  5 min wait) and `kill $(cat XVFB)` hit whoever owned the PID. The file now counts only while
  `/proc/<pid>/comm` is `Xvfb` and its command line carries the install's display (`:<port/10>`);
  otherwise it is removed and the stop goes the CLI way. Any `start` clears a leftover.
- 🔬 `stop` when nothing answers on the port (curl exit 7 — still booting past the 30 s ready-wait,
  or hung): the exit was never delivered, so it waits 10 s, not 5 min, and exits 1 with the PIDs.
- ⚠️ Not exercised on a real install (the custodian was mid-run): the GUI branch (`--gui`, the
  `exitapp` servlet), SIGKILL of a JVM that ignores SIGTERM, and a real SQX shutdown where the
  port closes before the process exits.
- ⚠️ `SQX_START_WAIT` / `SQX_STOP_WAIT` (seconds) exist for the tests; do not set them in real use.

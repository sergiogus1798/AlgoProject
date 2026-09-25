---
q: worker did not stop but still up; sqx-worker.sh stop lies; find worker pid; process named sqcli; worker up then Connection refused; licence check exit; worker-daemon.log
tag: 🔬  date: 2026-09-23  see: sqx-drive/driving-a-role
---
# Poll the port, never trust `sqx-worker.sh` messages; kill a worker by PID found via its port
The worker's command line is just `./sqcli`; the install shows only in `/proc/<pid>/cwd`.
`stop` can print "worker did not stop" while the worker is still up (or vice versa); `start` can
print "worker up" and the JVM exits 2 s later on the licence check. After a start, a first
`Connection refused` → read the last 3 lines of `user/log/worker-daemon.log` first.

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

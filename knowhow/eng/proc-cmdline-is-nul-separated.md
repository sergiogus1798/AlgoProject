---
q: how to check a pid is my scratch ui daemon before killing it; /proc/<pid>/cmdline grep never matches; test daemon on --port survives kill
tag: 🔬  date: 2026-09-28  see: three-install-topology
---
# `/proc/<pid>/cmdline` separates arguments with NUL, so a grep with spaces never matches
Before killing a scratch daemon (`python3 -m ui.daemon.serve --port 8751`), turn the NULs into
spaces first: `tr '\0' ' ' < /proc/$P/cmdline | grep -q 'ui.daemon.serve --port 8751' && kill $P`.
`grep -q 'serve --port 8751' /proc/$P/cmdline` is always false, so the guard silently skips the
kill and the daemon keeps its port. Take the pid from the port (`ss -ltnp | grep ':8751 '`), not
`$!` of a `( … & )` subshell, which is the subshell's pid. Never touch 8765: it is the owner's.

## Evidence
2026-09-28, session algoproject-33: three `kill` guards with spaced patterns left the 8750 daemon
up (pid 2532905); the `tr` form stopped it on the first try, and the 8751 daemons after it.

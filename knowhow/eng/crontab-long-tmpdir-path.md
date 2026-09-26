---
q: crontab file fails No such file or directory, install crontab from a long TMPDIR scratchpad path, vixie-cron truncation bug, crontab: /tmp/.../scratch: No such file or directory
tag: 🔬  date: 2026-09-26  see: headless-claude-from-cron
---
# `crontab <file>` truncates a long path and fails with the wrong filename
`crontab <file>` on this machine's `cron 3.0pl1` (vixie-cron) copies its argument into a fixed-size
internal buffer before opening it. A path over roughly 80 characters — this session's scratchpad
lives under `/tmp/claude-1000/-home-sergioguslw-Desktop-AlgoProject/<uuid>/scratchpad/...` — gets cut
mid-name, and the error names that truncated, nonexistent path, not the real one. `crontab -l`
afterwards shows the old, unchanged crontab. Fix: copy the file to a short `/tmp` path first
(`cp long/path/crontab.new /tmp/crontab-new-$$.txt && crontab /tmp/crontab-new-$$.txt`), then remove it.

## Evidence
`crontab /tmp/claude-1000/-home-sergioguslw-Desktop-AlgoProject/9544a975-.../scratchpad/crontab.new`
→ `/tmp/claude-1000/-home-sergioguslw-Desktop-AlgoProject/9544a975-.../scratch: No such file or
directory`, exit 1 (note "scratch", not "scratchpad" — the truncation point), `crontab -l` unchanged.
Reproduced with `dangerouslyDisableSandbox: true` too, so it is not a sandbox restriction. Copying
the same file to `/tmp/crontab-new-$$.txt` and installing from there: exit 0, `crontab -l` updated.
`OPEN.md` issue 49.

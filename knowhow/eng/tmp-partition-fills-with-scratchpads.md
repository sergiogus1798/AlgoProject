---
q: No space left on device /tmp; pwd write error; /tmp full; Claude scratchpads never deleted; /tmp/claude-1000 size; clean old sessions
tag: 🔬  date: 2026-09-26  see: crontab-long-tmpdir-path, log-retention
---
# /tmp is a 3.9 GB partition, and ended Claude sessions never free their scratchpads
Every session writes `/tmp/claude-$UID/<project>/<session-uuid>/` and nothing removes it. When it fills,
every session's Bash fails with `pwd: write error: No space left on device` (the command itself may still run).
`bin/weekly-claude-cleanup.sh` (cron, Sunday 23:30) deletes session folders whose NEWEST file is > 3 days old.
⚠️ Judge age by the newest file inside, not `find -mtime` on the folder: a folder's date does not move
when a subfolder is written, so a live session looks old. `~/.claude/projects` (the conversations) is not touched.

## Evidence
- 🔬 2026-09-26: `/tmp` 3.9 G, 100 % used; `/tmp/claude-1000/-home-sergioguslw-Desktop-AlgoProject/` held 2.0 G
  in 256 session folders, one of 958 MB untouched for 23 days. Removing those older than 3 days → 28 % used.
- The Claude Code auto-mode classifier refuses a sweep of other sessions' scratchpads from inside a session
  ("Shared Scratch Sweep"); the owner's permission and the cron job are the route.

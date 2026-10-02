---
q: No space left on device /tmp; pwd write error; /tmp full; Claude scratchpads never deleted; /tmp/claude-1000 size; clean old sessions; where does project temp go; tempfile dir
tag: 🔬  date: 2026-10-02  see: crontab-long-tmpdir-path, log-retention
---
# /tmp is a 3.9 GB partition, and ended Claude sessions never free their scratchpads
Every session writes `/tmp/claude-$UID/<project>/<session-uuid>/`; nothing removes it. Full /tmp = every Bash
fails (`pwd: write error: No space left on device`). `bin/weekly-claude-cleanup.sh` (cron daily since
2026-10-02, name historical, idempotent) deletes session folders whose NEWEST file is > 3 days old (not
`find -mtime` on the folder: it does not move when a subfolder is written) and prunes `<data root>/tmp`.
**Project temp goes to `core.datapaths.tmp_dir()`** (`AlgoData/tmp`): pass it as `dir=` to `tempfile`
(`tools/manual.py` sets `TMPDIR` for Chrome). `perf.disk.report` exits non-zero above `disk.tmp_max_share`.

## Evidence
- 🔬 2026-09-26: `/tmp` 3.9 G, 100 % used; `/tmp/claude-1000/-home-sergioguslw-Desktop-AlgoProject/` held 2.0 G
  in 256 session folders, one of 958 MB untouched for 23 days. Removing those older than 3 days → 28 % used.
- 🔬 2026-10-02: back at 93 % (3.4 G; 2.8 G was `/tmp/claude-1000`). Weekly run was too slow: 125 old session
  folders = 1154 MB freed -> 62 %; 41 stray `tmp*`/`scoped_dir*`/`cfxp`/`cfxq`/`x.parquet` entries (200 MB) -> 57 %.
  The rest of the 2.1 GB is sessions < 3 days old, `bash-edit-diff` (355 MB, all recent) and ~1600 `/tmp/.com.google.Chrome.*` (320 MB).
- The Claude Code auto-mode classifier refuses a sweep of other sessions' scratchpads from inside a session
  ("Shared Scratch Sweep"); the owner's permission and the cron job are the route.

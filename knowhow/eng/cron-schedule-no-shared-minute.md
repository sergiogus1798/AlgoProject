---
q: crontab collision, two cron jobs same minute, cron order, flock wait on a lock, monthly-oos2-roll must start after weekly-data-update, docs-health after knowhow review, nightly chain times
tag: 🔬  date: 2026-10-02  see: crontab-long-tmpdir-path, headless-claude-from-cron
---
# No two cron entries share a minute; a script that waits on a lock starts after the one that takes it
`flock -w` only waits if the other script ALREADY holds the lock; started first or together it runs alongside.
Chain: Sat 02:00 `weekly-data-update` → 02:05 `monthly-oos2-roll`; Mon 02:50 janitor; 03:00 audit → 03:30 docs
→ 03:45 `archive_logs` → 04:00 fixer → 04:15 `sqx-log-prune` (archive before prune); Sun 05:00 knowhow
review → 05:10 docs-health; daily 23:30 claude-cleanup. Durations: audit 1-1.5 min, docs 40 s, fixer 1-6,
data update 15.5, janitor 1.3, knowhow 4, docs-health 11.5. Back up first (`crontab -l > AlgoData/logs/crontab-backup-<date>.txt`).

## Evidence
2026-10-02: the old crontab shared Sat/Mon 03:00, daily 04:00, Sun 05:00; docs-health waited on a lock the
review might not yet hold. Old file: `AlgoData/logs/crontab-backup-2026-10-02.txt`. Check repeats:
`crontab -l | grep -v '^#' | grep . | awk '{print $1,$2,$5}' | sort | uniq -d` (daily vs weekly: by eye).

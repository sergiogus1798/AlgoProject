---
q: How do I pick a cron minute that no other job uses, and which job must start after which?
kw: crontab collision, two cron jobs same minute, cron order, flock wait on a lock, monthly-oos2-roll must start after weekly-data-update, docs-health after knowhow review, nightly chain times
tag: 🔬  date: 2026-10-02  see: crontab-long-tmpdir-path, headless-claude-from-cron
---
# No two cron entries share a minute (except `fleet-collect`, every minute); a script that waits on a lock starts after the one that takes it
Chain: Sat 02:00 `weekly-data-update` → 02:05 `monthly-oos2-roll`; daily 02:20 `graphify update .` (1.5 min, no lock); Mon 02:50 janitor; 03:00 audit → 03:30 docs
→ 03:45 `archive_logs` → 04:00 fixer → 04:15 `sqx-log-prune` (archive before prune); Sun 05:00 knowhow
review → 05:10 docs-health → daily 05:45 `nightly-commit-proposal` (propose only; waits on the fixer, review and docs-health locks;
05:30 is kept for the off-disk backup); daily 07:00 `daily-literature-scout` (reads papers, then tops the market profile up at nice 19: 30-60 min); daily 23:30 claude-cleanup. Durations: audit 1-1.5 min, docs 40 s, fixer 1-6,
data update 15.5, janitor 1.3, knowhow 4, docs-health 2-11.5, commit proposal not yet measured. Back up first (`crontab -l > AlgoData/logs/crontab-backup-<date>.txt`). Stated exception (owner, 2026-10-03, «cron cada minuto»): `* * * * * bin/fleet-collect.sh` shares every minute; it takes no lock any other job waits on and `flock -n` skips a run while the last is going. `flock -w` only waits if the other script ALREADY holds the lock; started first or together it runs alongside.

## Evidence
2026-10-02 (b): added 05:45 `nightly-commit-proposal` (backup `crontab-backup-2026-10-02b.txt`). Headless `claude -p` with
`--allowedTools "Bash(git status*)"… --disallowedTools "Bash(git commit*)" "Bash(git add*)" "Bash(git push*)"`: `git commit --dry-run`,
`git add --dry-run`, `git push --dry-run` and `git status && git commit …` were all denied, `bash -c 'git commit …'` was not approved
(non-interactive), plain `git status` ran. First real run: 2 min.
2026-10-02: the old crontab shared Sat/Mon 03:00, daily 04:00, Sun 05:00; docs-health waited on a lock the
review might not yet hold. Old file: `AlgoData/logs/crontab-backup-2026-10-02.txt`. Check repeats:
`crontab -l | grep -v '^#' | grep . | awk '{print $1,$2,$5}' | sort | uniq -d` (daily vs weekly: by eye).

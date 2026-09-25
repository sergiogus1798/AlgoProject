---
q: snapshot user/projects before restart, snapshot size exclude log, rsync snapshot, dedupe snapshot link-dest, delete snapshot after restart, count sqx per databank
tag: 🔬  date: 2026-09-23  see: databanks/sync-deletes-unloaded-files, databanks/sync-only-touches-loaded
---
# Snapshot `user/projects` before any restart, without `log/`; delete it once the restart is verified
`rsync -a --exclude='log/'` — a complete safety net since loss is always disk-vs-memory. Take the copy,
restart, compare counts per databank (`projectsBackup/install-configs-2026-09-21/count_sqx.sh`,
`find -print0`), delete the copy (owner, 2026-09-23). `AlgoData` is for data, not an ark.

## Evidence
- 2026-09-21 snapshot 4.5 GB, 1.03 GB of it ten `global_log_*.log` (one 566 MB) — not protected by rule 1,
  not covered by `sqx/export/archive_logs.py` (it archives `user/log`, not projects' `log/`). Without:
  ~3.5 GB for the master.
- No dedupe possible: two days later 7,402 of 7,546 master `.sqx` differed in size and mtime — SQX
  rewrites every file on sync. `--link-dest` and hashing gain nothing; only lever is what is included.
- The 2026-09-21 copy (7,546 `.sqx`, 3.5 GB) held no file or databank count the live master lacked; the
  worker's 66 were rebuildable.

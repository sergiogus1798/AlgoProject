---
q: update SQX bar data download; data action=update on worker lost; master to worker rsync user/data; core.assets --dataranges refresh data ranges
tag: 🔬  date: 2026-09-22  see: costs/tick-feed-coverage, databanks/snapshot-before-restart
---
# Downloading new bars is the owner's button on the master; automate only the read side
- A download on a worker is lost: next worker start overwrites its H2 databases with the master's stale copy.
- Master download = `sqcli` on the master → forbidden while its GUI is up (hard rule 2), snapshot `user/projects` first (hard rule 1).
- Safe any time: `python3 -m core.assets --dataranges` asks the conductor and rewrites the `data:` line of all 17 assets in `assets/_policy.yaml`.

## Evidence
- 📓 `sqcli -data action=update` = GUI "Update all" (beside `import`, `export`, `exportToMT4/5`, `clone`, `timezones`). Verb reference: `internal/web/SQUANT/help.txt` (readable without starting anything).
- `bin/sqx-worker.sh` start runs `rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"` (flow master → worker). `History` is a shared symlink,
  but the three H2 databases a backtest reads are per-install copies.
- Conductor sees the master's store via the same rsync. Run mid-update, `--dataranges` caught four feeds moving `2026-01-16` → `2026-09-22`, left thirteen alone.

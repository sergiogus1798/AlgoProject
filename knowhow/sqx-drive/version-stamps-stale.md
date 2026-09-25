---
q: sqx-worker.sh check reports STALE; data_futures.version data_stock.version restamped by sqcli; worker bars freshness check; restamp 202609201214
tag: 🔬  date: 2026-09-21  see: sqx-drive/driving-a-role
---
# `sqcli` restamps `data_futures.version` and `data_stock.version` on every start; `check` ignores them
Every launch writes the fixed stamp `202609201214` (newer than the master's) into those two files,
on any install. `bin/sqx-worker.sh check` now prints them as `restamp` and excludes them from its
verdict, so exit 0 = healthy. ⚠️ Price: a real futures/stock import on the master is no longer
flagged by `check`; accepted because `start` syncs bars unconditionally. `data.db` (forex bars) still compared.

## Evidence
`.db` files aren't comparable (H2 rewrites the header on open), hence `.version` files.
| step | `data_futures.version` worker vs master |
|---|---|
| `sync`, worker stopped | equal, exit 0 |
| `start`, then `check` | `202609201214` vs `202609181234` → STALE, exit 1 |
| `stop`, `sync`, `check` | equal, exit 0 |
md5 `c46fbd6c…` → `a02699c3…` across the start; mtime = start moment.
`brokers.version`, `group_of_stocks.version` untouched. `SQX_w2`, freshly cloned, showed the same stamp.
📓 Origin not the shared `user/data/History` (no mtime near 2026-09-20 12:14); unknown — skip that search.
Old `check` message `worker <stamp> < master <stamp>` had the `<` backwards.
🤔 Sync logic itself is right (copy at start always safe and current); only the freshness report was wrong.

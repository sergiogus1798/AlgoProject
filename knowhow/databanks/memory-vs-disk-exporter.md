---
q: Why do file-based exports see an empty databank that is full in memory, even with Auto-sync every 1 hour?
kw: new databank Auto-sync every 1 hour but no directory on disk, export stages 0 strategies, exportdrv.stage empty, MCP record count misleading, databank shows records but directory empty, Auto-sync never export nothing, orderstocsv empty databank, never-synced databank strategies, find synced copy downstream
tag: 🔬  date: 2026-10-04  see: databanks/databank-verbs, export/orderstocsv-schema
---
# A databank can be full in memory and empty on disk — file-based exports see nothing; `Auto-sync every 1 hour` is a setting, not proof
`exportdrv.stage()` copies from the master's on-disk directory, so a never-synced databank silently
stages **0** strategies. `ls` the directory before exporting any databank for the first time; the MCP
record count will not warn. Route: ask the owner to sync it from the GUI, or:

`synctofiles`/`save` need the instance holding the project (the master, whose CLI is off while its GUI
is up) — no code-only route. Instead find the same strategies in a downstream auto-syncing databank
(`dump_project.py <PROJECT>`). ⚠️ That copy is the **retested** strategy: its main result covers the
retest's window, not the builder's.

## Evidence
- XAUUSD `Results`: **36 records** via MCP, `user/projects/XAUUSD/databanks/Results/` held **0 `.sqx`**.
  `orderstocsv` takes a path, so it sees nothing while the GUI shows a full databank.
- XAUUSD task 4 retests `Results` → `OOS` (hourly auto-sync): its 36 on-disk `.sqx` were the identical set
  (name-set equality vs `list_strategies` on `Results`). Window there: 2008–2022 with IS/OOS split, not the
  builder's 2008–2017.
- XAUUSD (2026-09-05): `OOS-Sharpe` **9,997 records**, `syncType: Auto-sync every 1 hour` (MCP `list_databanks`),
  yet `user/projects/XAUUSD/databanks/OOS-Sharpe/` did not exist; same for `Results-Sharpe` (10,000). Master up
  1d21h. Owner's GUI sync wrote all 9,997 `.sqx` within a minute; reference `OOS` kept its 10,000 through it.

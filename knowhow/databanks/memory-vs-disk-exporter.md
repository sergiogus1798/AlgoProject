---
q: databank shows records but directory empty, Auto-sync never export nothing, orderstocsv empty databank, never-synced databank strategies, find synced copy downstream
tag: 🔬  date: 2026-09-05  see: databanks/autosync-nothing-on-disk, databanks/databank-verbs, export/orderstocsv-schema
---
# An `Auto-sync never` databank can be full in memory and empty on disk — file-based exports see nothing
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

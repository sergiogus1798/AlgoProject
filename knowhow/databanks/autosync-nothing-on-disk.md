---
q: new databank Auto-sync every 1 hour but no directory on disk, export stages 0 strategies, exportdrv.stage empty, MCP record count misleading
tag: 🔬  date: 2026-09-05  see: databanks/memory-vs-disk-exporter, databanks/databank-verbs
---
# "Auto-sync every 1 hour" is a setting, not proof a sync ever ran — `ls` before exporting
`exportdrv.stage()` copies from the master's on-disk directory, so a databank never synced silently
stages **0** strategies. `ls` the directory before exporting any databank for the first time; the MCP
record count will not warn. Working route: ask the owner to sync it from the GUI.

## Evidence
- XAUUSD: `OOS-Sharpe` **9,997 records**, `syncType: Auto-sync every 1 hour` (MCP `list_databanks`), yet
  `user/projects/XAUUSD/databanks/OOS-Sharpe/` did not exist; same for `Results-Sharpe` (10,000). Master
  up 1d21h.
- Owner's GUI sync wrote all 9,997 `.sqx` within a minute; reference `OOS` kept its 10,000 through it.

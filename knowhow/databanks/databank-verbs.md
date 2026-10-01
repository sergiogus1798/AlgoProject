---
q: -databank action count list export which is read-only, count destroys load, verify a load, databank verbs direction memory disk, synctofiles syncfromfiles, clear deletes files, load async, syncfromfiles adds duplicates
tag: 🔬  date: 2026-10-01  see: databanks/sync-deletes-unloaded-files, databanks/curating-a-databank, sqx-drive/live-chain-without-restart
---
# `-databank` verbs move data in opposite directions; only `action=export` is a safe reader
`export` reads memory (ms). `synctofiles` forces memory → disk. `clear` empties memory AND deletes the
files at once. `load folder=` adds a folder's .sqx to memory, asynchronously (wait for «Strategies
loaded» in the log). `syncfromfiles` also ADDS — it never removes, it duplicates as `X(1)`. `count`
as a project's first command syncs from files and can destroy what `load` put there; on a loaded
project it does not resync. Never verify with `count`; verify with `export`.

## Evidence
- After `action=load` put 3 in `Retester/VerifA`, `count` printed `Syncing databank(s) from files /
  Loaded 0 strategies to databank VerifA / Records: 0`; reload + `export` returned all 3.
  (`sqx/variants/execute.py`.)
- 2026-10-01 (`sqx-drive/live-chain-without-restart`): OOS 60 in memory, 56 files after deleting 4;
  `syncfromfiles` → «Loaded 116»; `clear` → «files before sync 56 / after sync 0 / removed 56»;
  `load folder=` answered at once, export 0, «Strategies loaded» 137 ms later, export 56.
- A running worker answering `list` logs `Loaded 30 strategies`.
- Full verb list: list, count, save, load, delete, clear, create, remove, synctofiles, syncfromfiles,
  copy, move, export — none recomputes stats.
- 🤔 2026-10-01, `javap` on `ServletProject.jar` (not called live, see `sqx-drive/live-chain-without-
  restart.md`'s GUI-servlet section): `Databank.setSyncType(String)` exists and is exposed as
  `/project/setDatabankSynchronization?syncType=`, only on the GUI's own web port — sqcli has no verb
  for it. If reachable, it is the knob for hard rule 1's hourly sync: an explicit-only `syncType` would
  stop a long live session from auto-writing a cut mid-chain.

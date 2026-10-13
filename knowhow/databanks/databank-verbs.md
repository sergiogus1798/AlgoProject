---
q: Which `-databank` verbs move data from files to memory or the reverse, and which is a safe reader?
kw: -databank action count list export which is read-only, count destroys load, verify a load, databank verbs direction memory disk, synctofiles syncfromfiles, clear deletes files, load async, syncfromfiles adds duplicates
tag: 🔬  date: 2026-10-13  see: databanks/sync-deletes-unloaded-files, databanks/curating-a-databank, sqx-drive/live-chain-without-restart
---
# `-databank` verbs move data in opposite directions; only `action=export` is a safe reader
`export` reads memory (ms). `synctofiles` forces memory → disk. `clear` empties memory AND deletes the
files at once (synchronous, 8-16 ms, no wait needed). `load folder=` adds a folder's .sqx to memory, asynchronously (returns in ~8 ms; wait for the log line «Strategies
loaded», 0.26 s for 50 files; no sleeps). `syncfromfiles` also ADDS — it never removes, it duplicates as `X(1)`. `count`
as a project's first command syncs from files and can destroy what `load` put there; on a loaded
project it does not resync. Never verify with `count`; verify with `export`. A sync of a bank with nothing pending writes NO log line:
never wait for «saved» on an already-clean bank. 🔬 2026-10-13, conductor, encargo 66.

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
- 🔬 2026-10-01, GUI mode (`sqx-drive/live-chain-without-restart`): a sync mirrors memory onto disk —
  after `removeReports` dropped 5 with 20 files on disk, `synchronizeDatabank` left exactly the 15 in
  memory. So the hourly auto-sync is harmless to a cut made in memory; what it destroys is a `.sqx`
  written into a databank folder from outside and never loaded (hard rule 1). `syncType` is per
  databank in config.xml (`setDatabankSynchronization` changes it live), but "Auto-sync never" is
  not an option: the builder switches it off because such a databank never reaches disk.
- 🔬 2026-10-13, conductor (encargo 66 live session 1, XAUUSD H1, 50-file banks): `clear` is SYNCHRONOUS
  (8-16 ms, files gone at return, reply «Reports removed»): no sleep after it. `load` replies in ~8 ms and
  the log line `ProjectServlet - Strategies loaded` follows ~0.26 s later (it names no databank; start-up
  loading does not log it); `sqx.projects.loadwait.loaded` waits for it. CLI `synctofiles` is synchronous
  (0.4-0.7 s per 50, «saved» line before the reply) but the .sqx are visible half-written (sizes 0, 54, 139…)
  while it writes: read after the call returns. A sync with NOTHING pending writes no «saved» line at all;
  a sync of an «Auto-sync never» databank DOES write «saved … API request» (Retester/Results, 5.4 s).
  15 overlapping `synchronizeDatabank` of one databank (3 at once × 5): no «Cannot process», files 30 -> 30,
  ONE saved line. A retest silenced to zero trades still lands in the output databank (30 in -> 30 out, 10
  with 0 trades) while the status reads «Failed 30 / Passed 0»: the status is not presence.

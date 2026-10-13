---
q: Why does a short SQX session take 6-8 min to exit while a session older than 1 h exits in 4 s?
kw: Save all strategies before exiting, Periodical sync Auto-sync every 1 hour, slow exit, sqx-worker stop slow, exitapp 515 s, reopen costs, liverun reopen, AGED, pending save flag
tag: 📓🔬  date: 2026-10-13  see: databanks/sync-deletes-unloaded-files, sqx-drive/live-chain-without-restart
---
# SQX exit regrabs every databank loaded from file, serially, unless the hourly sync already did
Trap: a worker session younger than 1 h exits in 6-8 min (175 databanks, 33,223 files, 487-515 s); one older than 1 h exits in ~4 s. SQX marks every databank loaded from file as pending save. «Save all strategies before exiting» rewrites them in series; «Periodical sync … Auto-sync every 1 hour» saves them in parallel (161 in 76 s). So each reopen (`ui/daemon/launch/liverun.py:101-104`) makes a short session and pays ~510 s at the final stop, ~1,220 s per run in all.
Fix options (not applied): A, do not reopen (`AGED = set()`; costs the old-session penalty noted at `liverun.py:26`, WFM x1.44, SPP x2). B, after `live.start` save in parallel with `synchronizeDatabank`, only where memory == disk (rule 1).
🔬 2026-10-13, conductor: an API `synchronizeDatabank` (`sqx/projects/live.py:201`) on a file-loaded databank with memory == disk DOES clear the flag — exit save lines 1, 1 → 0, stop 10.9 s → 5.8 s (17 files, one databank). The call is asynchronous; its end is the log line `Sync triggered by 'API request project/synchronizeDatabank …'`. Do not filter out `Auto-sync never` or stock projects: `Retester/Results` is both and is re-saved at exit. **NOT tested:** the parallel gain at 175 databanks (one databank costs the same by API as at exit, 5.44 s), and not reopening before SPP/WFM.

🔬 2026-10-13, conductor, live session 3 (18 projects, 3,233 files): a fresh session stops in 52.4 s (63 exit save lines, x3); the same set aged 131.5 min stops in 12.0 s (1 save line) with no variant, because SQX's own hourly auto-sync saved 120 banks at 14:41. The presave pays only on what changed since the last auto-sync: 8-9 s stop + 6.7-7.8 s background = 15.2-15.8 s net. The env var that emptied the reopen before aged SPP/WFM never touched a stop: it was not a stop variant, deleted. Owner Q12, 2026-10-13: the presave (`sqx/projects/presaving.py`) is ALWAYS ON, no switch; SQX's hourly auto-sync already covers sessions older than an hour.

## Evidence
- 📓 Audit `AlgoData/audit/performance-2026-10-12/findings-SQXPY.md` SQXPY-1: periodic sync 03:26:49 → 04:26:49 → 04:28:05 (wf4s), 08:14:40 (leaseWeb).
- 📓 27 sessions of 2026-10-10/11 (`exits.py`): the 7 over 1 h exit in ~4 s; the 20 under 1 h take 6-8 min, three of them having done nothing.

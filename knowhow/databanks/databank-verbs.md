---
q: -databank action count list export which is read-only, count destroys load, verify a load, databank verbs direction memory disk, synctofiles syncfromfiles
tag: 🔬  date: 2026-09-23  see: databanks/sync-deletes-unloaded-files, databanks/curating-a-databank, sqx-format/five-member-sqx
---
# `-databank` verbs move data in opposite directions; only `action=export` is a safe reader
`action=count` syncs **from** files and destroys what `action=load` put in memory — never verify a load
with `count`. `action=list` fills memory from disk. `action=export` reads memory. `action=synctofiles`
forces memory → disk. Pick deliberately: it decides whether a restart preserves or discards.

## Evidence
- After `action=load` put 3 in `Retester/VerifA`, `count` printed `Syncing databank(s) from files /
  Loaded 0 strategies to databank VerifA / Records: 0`; reload + `export` returned all 3.
  (`sqx/variants/execute.py`.)
- A running worker answering `list` logs `Loaded 30 strategies`.
- Full verb list: list, count, save, load, delete, clear, create, remove, synctofiles, syncfromfiles,
  copy, move, export — none recomputes stats.
